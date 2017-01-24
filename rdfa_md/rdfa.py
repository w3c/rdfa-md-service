#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
"""
Module to handle RDFa
   - extract RDF from an input content by parsing it for RDFa
   - validate RDFa data as extracted from an input content

Validation means to extract the RDFa content, using the same parser, and examining the (possible) error
(RDF) triples that the parser generates. If any, those are displayed in a readable HTML content.

Dependencies within the module:
	- RDF Extraction: None
	- RDFa Validation:
		- validator_errors.py: working through the error triples to produce proper output
		- validator_html.py: a single HTML template to be used for the generated output

"""
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

import traceback, cgi
if PY3 :
	from io import StringIO
	from urllib.error import HTTPError
else :
	from StringIO import StringIO
	from urllib2 import HTTPError

from rdflib import Graph
from rdflib.plugins.parsers.pyRdfa.host import MediaTypes
from .validator import Validator

#############################################################################################
# Common class to handle the (CGI) form object values
#############################################################################################
class FormValues(object):
	"""Various options to be extracted from the form (ie, a CGI FieldStorage instance)
	This class collects what is common in handling simple RDF parsing as well as for
	the validator.

	The meaning of the form values are:

	 - C{graph=[output|processor|output,processor|processor,output]} specifying which graphs are returned. Default: C{output}
	 - C{space_preserve=[true|false]} means that plain literals are normalized in terms of white spaces. Default: C{false}
	 - C{host_language=[xhtml,html,xml]} : the host language. Used when files are uploaded or text is added verbatim, otherwise the HTTP return header should be used. Default C{xml}
	 - C{embedded_rdf=[true|false]} : whether embedded turtle or RDF/XML content should be added to the output graph. Default: C{false}
	 - C{vocab_expansion=[true|false]} : whether the vocabularies should be expanded through the restricted RDFS entailment. Default: C{false}
	 - C{vocab_cache=[true|false]} : whether vocab caching should be performed or whether it should be ignored and vocabulary files should be picked up every time. Default: C{false}
	 - C{vocab_cache_report=[true|false]} : whether vocab caching details should be reported. Default: C{false}
	 - C{vocab_cache_bypass=[true|false]} : whether vocab caches have to be regenerated every time. Default: C{false}
	 - C{rdfa_lite=[true|false]} : whether warnings should be generated for non RDFa Lite attribute usage. Default: C{false}
	 - C{rdfa_version=["1.1"|"1.0"]} : RDFa version. If missing, set to 1.1.
	"""
	def __init__(self, form):
		self.form = form
		self.keys = list(form.keys())
		self.host_language		 = self.get_value("host_language")
		self.media_type          = self._get_media_type()
		self.rdfa_version		 = self.get_value("rdfa_version", "1.1")
		self.check_lite          = (self.get_value("rdfa_lite") == "true")
		self.embedded_rdf        = self.check_option("embedded_rdf", "true", False)
		self.space_preserve      = self.check_option("space_preserve", "true", True)
		self.vocab_cache         = self.check_option("vocab_cache", "true", True)
		self.vocab_cache_report  = self.check_option("vocab_cache_report", "true", False)
		self.refresh_vocab_cache = self.check_option("vocab_cache_refresh", "true", False)
		self.vocab_expansion     = self.check_option("vocab_expansion", "true", False)
		self.output_format       = self.get_value("format", "turtle")

	def _get_media_type(self):
		if self.host_language is None:
			media_type = ""
		elif self.host_language == "xhtml" :
			media_type = MediaTypes.xhtml
		elif self.host_language == "html" :
			media_type = MediaTypes.html
		elif self.host_language == "svg" :
			media_type = MediaTypes.svg
		elif self.host_language == "atom" :
			media_type = MediaTypes.atom
		else :
			media_type = MediaTypes.xml
		return media_type

	def get_value(self, key, default = None):
		"""Get a value if exists, None otherwise"""
		return self.form.getfirst(key).lower() if key in self.keys else default

	def get_value2(self, key1, key2):
		"""Get one of two options, in priority order, None if neither is present"""
		retval = self.get_value(key1)
		return self.get_value(key2) if retval is None else retval

	def check_option(self, key, compare_value, default):
		"""Check how the value for `key` compares with the value. If no value
		is present, returns default."""
		# The second alternative is to ensure that the old style
		# parameters are still valid.
		# in the old days I used '-' in the parameters, the standard favours '_'
		val = self.get_value2(key, key.replace('_','-'))
		return default if val is None else val == compare_value

	def get_source_and_base(self, uri):
		""" Return the location of the source data; usually it is a URI but,
		in some cases, it may return to the embedded data in the form"""
		# Collect the data, depending on what mechanism is used in the form
		if uri == "uploaded:" :
			return (self.form["uploaded"].file, "")
		elif uri == "text:" :
			return (StringIO(self.form.getfirst("text")), "")
			base	= ""
		else :
			return (uri,uri)

#########################################################################################
# RDF Extraction:  use the RDFLib parser to extract the RDF graph, serialize it and
# return to the caller
# In case or problems, an HTTP response is generated incorporating the Exception data and
# some basic information on the calling parameters.
#########################################################################################
def extract_rdf(uri, form) :
	"""The standard processing of an RDFa uri options in a form; used as an entry point from a CGI call.

	@param uri: URI to access. Note that the C{text:} and C{uploaded:} fake URI values are treated separately; the former is for textual intput (in which case a StringIO is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.

	@param form: extra call options (from the CGI call) to set up the local options
	@type form: cgi FieldStorage instance

	@return: serialized graph
	@rtype: string
	"""

	form_values = FormValues(form)

	# Collect the data, depending on what mechanism is used in the form
	input, base = form_values.get_source_and_base(uri)

	# Decide which graphs should be sent back
	graph_choice = form_values.get_value2("rdfagraph", "graph")
	if graph_choice == "processor":
		output_default_graph, output_processor_graph = False, True
	elif graph_choice == "processor,output" or graph_choice == "output,processor":
		output_default_graph, output_processor_graph = True, True
	else:
		output_default_graph, output_processor_graph = True, False

	# These values may be overridden in one case...
	if form_values.vocab_cache_report : output_processor_graph = True

	# Almost ready to work; creating the two RDF Graphs
	output_graph    = Graph()
	processor_graph = Graph()

	# The graph is serialized in the required format, and returned
	try :
		# This is the real meat: calling out to the RDFa parser.
		output_graph.parse(input,
						   format              = "rdfa",
						   pgraph              = processor_graph,
						   media_type          = form_values.media_type,
						   embedded_rdf        = form_values.embedded_rdf,
						   space_preserve      = form_values.space_preserve,
						   vocab_expansion     = form_values.vocab_expansion,
						   vocab_cache         = form_values.vocab_cache,
						   refresh_vocab_cache = form_values.refresh_vocab_cache,
						   vocab_cache_report  = form_values.vocab_cache_report,
						   check_lite          = form_values.check_lite,
						   rdfa_version        = form_values.rdfa_version
						   )

		# Next step is to create the final graph to be returned to the user; this depends on
		# whether the which graphs are required.
		final_graph = Graph()
		if output_default_graph :
			for t in output_graph : final_graph.add(t)
		if output_processor_graph :
			for t in processor_graph : final_graph.add(t)

		# "header" collects the HTTP response; first the header with the content type,
		# then the real data
		if form_values.output_format == "nt" :
			header = 'Content-Type: application/n-triples; charset=utf-8\n'
			format = "nt"
		elif form_values.output_format == "turtle" :
			header = 'Content-Type: text/turtle; charset=utf-8\n'
			format = "turtle"
		elif form_values.output_format == "json-ld" or form_values.output_format == "json" :
			# This requires extra care, because the JSON-LD serializer is a separate
			# plugin for RDFLib (alas...)
			# If this is not successful, we are falling back on turtle
			try:
				# check if the json-ld parser can be registered in the first place
				from rdflib.plugin import register
				from rdflib.serializer import Serializer
				from rdflib_jsonld.serializer import JsonLDSerializer
				register("json-ld", Serializer,"rdflib_jsonld.serializer", "JsonLDSerializer")
				header = 'Content-Type: application/ld+json; charset=utf-8\n'
				format = "json-ld"
			except:
				# There is no JSON-LD serializer, falling back on turtle
				header = 'Content-Type: text/turtle; charset=utf-8\n'
				format = "turtle"
		else :
			header = 'Content-Type: application/rdf+xml; charset=utf-8\n'
			format = "pretty-xml"
		# Extra empty line to end the HTTP response header
		return header + "\n" + final_graph.serialize(format=format)
	except HTTPError:
		from . import handle_http_exception
		return handle_http_exception(uri, "HTTP Error in distilling RDFa content")
	except Exception as e:
		from . import handle_general_exception
		return handle_general_exception(uri, "Exception in distilling RDFa", form_values,
		                                graph_choice = graph_choice, extracts = True )

#########################################################################################
# RDFa Validation:  use the RDFLib parser to extract the RDF graph, serialize it and
# The rough order of working:
# - generate the default and the processor graphs via the distiller
# - take the HTML code template in L{html_page}
# - expand the DOM tree of that template by (a) generate a list of errors and warnings in HTML and (b) add the generated code
# - serialize the HTML page as an output to the CGI call
#########################################################################################

def validate_rdfa(uri, form={}) :
	"""The standard processing of an RDFa uri options in a form, ie, as an entry point from a CGI call. For compatibility
	reasons with the RDFa 1.1 distiller (the same CGI entry point is used for both) the form's content may include a number
	of entries that this function ignores.

	The call accepts the following extra form option (eg, HTTP GET options):

	 - C{host_language=[xhtml,html,xml]} : the host language. Used when files are uploaded or text is added verbatim, otherwise the HTTP return header shoudl be used

	@param uri: URI to access. Note that the "text:" and "uploaded:" values are treated separately; the former is for textual intput (in which case a StringIO is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.
	@param form: extra call options (from the CGI call) to set up the local options
	@type form: cgi FieldStorage instance
	@return: serialized HTML content
	@rtype: string
	"""
	form_values = FormValues(form)
	# Collect the data, depending on what mechanism is used in the form
	input, base = form_values.get_source_and_base(uri)
	try :
		validator = Validator(input, base,
								media_type      = form_values.media_type,
								vocab_expansion = form_values.vocab_expansion,
								check_lite      = form_values.check_lite,
								embedded_rdf    = form_values.embedded_rdf)

		header = 'Content-type: text/html; charset=utf-8\n'
		return header + "\n" + validator.run()
	except HTTPError:
		from . import handle_http_exception
		return handle_http_exception(uri, "HTTP Error in RDFa validation processing")
	except :
		from . import handle_general_exception
		return handle_general_exception(uri, "Error in RDFa validation processing", form_values,
		                                graph_choice = "", extracts = False )
