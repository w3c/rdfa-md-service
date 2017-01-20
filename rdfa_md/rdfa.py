#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

import traceback, cgi
if PY3 :
	from io import StringIO
else :
	from StringIO import StringIO
from rdflib import Graph
from rdflib.plugins.parsers.pyRdfa.host import MediaTypes

#########################################################################################
#  The core: handling the form arguments (after some prior check done elsewhere),
#  use the RDFLib parser to extract the RDF graph, serialize it and return to the caller
#########################################################################################
def extract_rdf(uri, form) :
	"""The standard processing of an RDFa uri options in a form; used as an entry point from a CGI call.

	The call accepts extra form options (i.e., HTTP GET options) as follows:

	 - C{graph=[output|processor|output,processor|processor,output]} specifying which graphs are returned. Default: C{output}
	 - C{space_preserve=[true|false]} means that plain literals are normalized in terms of white spaces. Default: C{false}
	 - C{host_language=[xhtml,html,xml]} : the host language. Used when files are uploaded or text is added verbatim, otherwise the HTTP return header should be used. Default C{xml}
	 - C{embedded_rdf=[true|false]} : whether embedded turtle or RDF/XML content should be added to the output graph. Default: C{false}
	 - C{vocab_expansion=[true|false]} : whether the vocabularies should be expanded through the restricted RDFS entailment. Default: C{false}
	 - C{vocab_cache=[true|false]} : whether vocab caching should be performed or whether it should be ignored and vocabulary files should be picked up every time. Default: C{false}
	 - C{vocab_cache_report=[true|false]} : whether vocab caching details should be reported. Default: C{false}
	 - C{vocab_cache_bypass=[true|false]} : whether vocab caches have to be regenerated every time. Default: C{false}
	 - C{rdfa_lite=[true|false]} : whether warnings should be generated for non RDFa Lite attribute usage. Default: C{false}

	@param uri: URI to access. Note that the C{text:} and C{uploaded:} fake URI values are treated separately; the former is for textual intput (in which case a StringIO is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.

	@param form: extra call options (from the CGI call) to set up the local options
	@type form: cgi FieldStorage instance

	@return: serialized graph
	@rtype: string
	"""
	# Using 'list' is necessary on Python3; this variable avoids me to call this all the time...
	form_keys  = list(form.keys())

	#####
	# Just factoring out repeated steps...
	# - get a value from the form, returning None if it is not present
	# - get a value with two alternative keys (in priority order), None if neither is present
	_get_value  = lambda key: form.getfirst(key).lower() if key in form_keys else None
	def _get_value2(key1, key2):
		retval = _get_value(key1)
		return _get_value(key2) if retval is None else retval

	####
	# See if a key is present and is of a certain value; if the key is not present,
	# return the default (boolean) value
	def _get_option(param, compare_value, default) :
		# The second alternative is to ensure that the old style
		# parameters are still valid.
		# in the old days I used '-' in the parameters, the standard favours '_'
		val = _get_value2(param, param.replace('_','-'))
		return default if val is None else val == compare_value


	# Retrieve the output (serialziation) format
	outputFormat = _get_value("format")
	if outputFormat is None: outputFormat = "turtle"

	# Collect the data, depending on what mechanism is used in the form
	if uri == "uploaded:" :
		input	= form["uploaded"].file
		base	= ""
	elif uri == "text:" :
		input	= StringIO(form.getfirst("text"))
		base	= ""
	else :
		input	= uri
		base	= uri

	# working through the possible options
	# Host language: HTML, XHTML, or XML
	# Note that these options should be used for the upload and inline version
	# only in case of a form for real uris the returned content type should be used
	host_language = _get_value("host_language")
	if host_language is None:
		media_type = ""
	elif host_language == "xhtml" :
		media_type = MediaTypes.xhtml
	elif host_language == "html" :
		media_type = MediaTypes.html
	elif host_language == "svg" :
		media_type = MediaTypes.svg
	elif host_language == "atom" :
		media_type = MediaTypes.atom
	else :
		media_type = MediaTypes.xml

	check_lite = (_get_value("rdfa_lite") == "true")

	output_default_graph 	= True
	output_processor_graph 	= False
	# Note that I use the 'graph' and the 'rdfagraph' form keys here. Reason is that
	# I used 'graph' in the previous versions, including the RDFa 1.0 processor,
	# so if I removed that altogether it would create backward incompatibilities
	# On the other hand, the RDFa 1.1 doc clearly refers to 'rdfagraph' as the standard
	# key.
	graph_choice = _get_value2("rdfagraph", "graph")
	if graph_choice == "processor":
		(output_default_graph, output_processor_graph) = (False, True)
	elif graph_choice == "processor,output" or graph_choice == "output,processor":
		(output_default_graph, output_processor_graph) = (True, True)
	else:
		(output_default_graph, output_processor_graph) = (True, False)

	# Get the other options from the form, setting also the default, if needed
	embedded_rdf        = _get_option( "embedded_rdf", "true", False)
	space_preserve      = _get_option( "space_preserve", "true", True)
	vocab_cache         = _get_option( "vocab_cache", "true", True)
	vocab_cache_report  = _get_option( "vocab_cache_report", "true", False)
	refresh_vocab_cache = _get_option( "vocab_cache_refresh", "true", False)
	vocab_expansion     = _get_option( "vocab_expansion", "true", False)
	if vocab_cache_report : output_processor_graph = True

	# Almost ready to work; creating the two RDF Graphs
	output_graph    = Graph()
	processor_graph = Graph()

	# This is the real meat: calling out to the RDFa parser.
	output_graph.parse(input,
					   format              = "rdfa",
					   pgraph              = processor_graph,
					   media_type          = media_type,
					   embedded_rdf        = embedded_rdf,
					   space_preserve      = space_preserve,
					   vocab_expansion     = vocab_expansion,
					   vocab_cache         = vocab_cache,
					   refresh_vocab_cache = refresh_vocab_cache,
					   vocab_cache_report  = vocab_cache_report,
					   check_lite          = check_lite
					   )

	# Next step is to create the final graph to be returned to the user; this depends on
	# whether the which graphs are required.
	final_graph = Graph()
	if output_default_graph :
		for t in output_graph : final_graph.add(t)
	if output_processor_graph :
		for t in processor_graph : final_graph.add(t)

	# The graph is serialized in the required format, and returned
	try :
		# "header" collects the HTTP response; first the header with the content type,
		# then the real data
		if outputFormat == "nt" :
			header = 'Content-Type: application/n-triples; charset=utf-8\n'
			format = "nt"
		elif outputFormat == "turtle" :
			header = 'Content-Type: text/turtle; charset=utf-8\n'
			format = "turtle"
		elif outputFormat == "json-ld" or outputFormat == "json" :
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
	except HTTPError :
		(type,h,traceback) = sys.exc_info()

		retval =  'Status: 400 Invalid Input'
		retval += 'Content-type: text/html; charset=utf-8\nStatus: %s \n\n' % h.http_code
		retval += "<html>\n"
		retval += "<head>\n"
		retval += "<title>HTTP Error in distilling RDFa content</title>\n"
		retval += "</head><body>\n"
		retval += "<h1>HTTP Error in distilling RDFa content</h1>\n"
		retval += "<p>HTTP Error: %s (%s)</p>\n" % (h.http_code,h.msg)
		retval += "<p>On URI: <code>'%s'</code></p>\n" % cgi.escape(uri)
		retval +="</body>\n"
		retval +="</html>\n"
		return retval
	except :
		# This branch should occur only if an exception is really raised, ie, if it is not turned
		# into a graph value.
		(type,value,traceback) = sys.exc_info()

		retval =  'Status: 400 Invalid Input'
		retval += 'Content-type: text/html; charset=utf-8\nStatus: %s\n\n' % processor.http_status
		retval += "<html>\n"
		retval += "<head>\n"
		retval += "<title>Exception in RDFa processing</title>\n"
		retval += "</head><body>\n"
		retval += "<h1>Exception in distilling RDFa</h1>\n"
		retval += "<pre>\n"
		strio  = StringIO()
		traceback.print_exc(file=strio)
		retval += strio.getvalue()
		retval +="</pre>\n"
		retval +="<pre>%s</pre>\n" % value
		retval +="<h1>Distiller request details</h1>\n"
		retval +="<dl>\n"
		if uri == "text:" and "text" in form and form["text"].value != None and len(form["text"].value.strip()) != 0 :
			retval +="<dt>Text input:</dt><dd>%s</dd>\n" % cgi.escape(form["text"].value).replace('\n','<br/>')
		elif uri == "uploaded:" :
			retval +="<dt>Uploaded file</dt>\n"
		else :
			retval +="<dt>URI received:</dt><dd><code>'%s'</code></dd>\n" % cgi.escape(uri)
		if host_language :
			retval +="<dt>Media Type:</dt><dd>%s</dd>\n" % media_type
		if "graph" in list(form.keys()) :
			retval +="<dt>Requested graphs:</dt><dd>%s</dd>\n" % form.getfirst("graph").lower()
		else :
			retval +="<dt>Requested graphs:</dt><dd>default</dd>\n"
		retval +="<dt>Output serialization format:</dt><dd> %s</dd>\n" % outputFormat
		if "space_preserve" in form : retval +="<dt>Space preserve:</dt><dd> %s</dd>\n" % form["space_preserve"].value
		retval +="</dl>\n"
		retval +="</body>\n"
		retval +="</html>\n"
		return retval
