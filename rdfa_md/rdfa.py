#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
"""
Module to handle RDFa data. The module contains two different methods:
   - Extract RDF from an input content by parsing it for RDFa (:py:func:`extract_rdf`)
   - Validate RDFa data as extracted from an input content (:py:func:`validate_rdfa`). (This function depends on other modules in the package.)
"""
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

if PY3:
	from urllib.error import HTTPError
else:
	from urllib2 import HTTPError

from rdflib import Graph
from rdflib.plugins.parsers.pyRdfa.host import MediaTypes
from .validator import Validator
from .utils import FormValues, handle_http_exception, handle_general_exception


#########################################################################################
# RDF Extraction:  use the RDFLib parser to extract the RDF graph, serialize it and
# return to the caller
# In case or problems, an HTTP response is generated incorporating the Exception data and
# some basic information on the calling parameters.
#########################################################################################
def extract_rdf(uri, form):
	"""
	Extract RDFa data from HTML or from various XML formats (SVG, XML, Atom, etc) and returns the resulting RDF data

	:param str uri: URI for the HTML data. Note that the ``text:`` and ``uploaded`` fake URI values are treated separately; the former is for textual intput (in which case a ``StringIO`` instance is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.

	:param cgi.FieldStorage form: the query parameters of the original request. See the description of the :py:class:`~.utils.FormValues` class for further details on the relevant form entries.

	:return: HTTP response, containing the RDF data encoded in the format requested by the user (default: ``turtle``), or an error message if applicable
	:rtype: str

	The function parses the HTML/SVG/XML content using the built-in ``RDFLib`` RDFa parser, and serializes the resulting RDF data using the serializaiton format requested by the user and returns the results. Serialization relies on the built-in ``RDFLib`` serializer for ``turtle``, ``nt``, or ``RDF/XML``, and on an ``RDFLib`` extension package (``rdflib_jsonld``) for ``JSON-LD``.
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
	if form_values.vocab_cache_report: output_processor_graph = True

	# Almost ready to work; creating the two RDF Graphs
	output_graph    = Graph()
	processor_graph = Graph()

	# The graph is serialized in the required format, and returned
	try:
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
		if form_values.output_format == "nt":
			header = 'Content-Type: application/n-triples; charset=utf-8\n'
			format = "nt"
		elif form_values.output_format == "turtle":
			header = 'Content-Type: text/turtle; charset=utf-8\n'
			format = "turtle"
		elif form_values.output_format == "json-ld" or form_values.output_format == "json":
			# This requires extra care, because the JSON-LD serializer is a separate
			# plugin for RDFLib (alas...)
			# If this is not successful, we are falling back on turtle
			try:
				# check if the json-ld parser can be registered in the first place
				from rdflib.plugin import register
				from rdflib.serializer import Serializer
				from rdflib_jsonld.serializer import JsonLDSerializer
				register("json-ld", Serializer, "rdflib_jsonld.serializer", "JsonLDSerializer")
				header = 'Content-Type: application/ld+json; charset=utf-8\n'
				format = "json-ld"
			except:
				# There is no JSON-LD serializer, falling back on turtle
				header = 'Content-Type: text/turtle; charset=utf-8\n'
				format = "turtle"
		else:
			header = 'Content-Type: application/rdf+xml; charset=utf-8\n'
			format = "pretty-xml"
		# Extra empty line to end the HTTP response header
		return header + "\n" + final_graph.serialize(format=format)
	except HTTPError:
		return handle_http_exception(uri, "HTTP Error in distilling RDFa content")
	except Exception as e:
		return handle_general_exception(uri, "Exception in distilling RDFa", form_values,
		                                graph_choice = graph_choice, extracts = True)



def validate_rdfa(uri, form={}):
	"""
	Validate the RDFa data from HTML or from various XML formats (SVG, XML, Atom, etc).

	:param str uri: URI for the HTML data. Note that the ``text:`` and ``uploaded`` fake URI values are treated separately; the former is for textual intput (in which case a ``StringIO`` instance is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.

	:param cgi.FieldStorage form: the query parameters of the original request. See the description of the :py:class:`~.utils.FormValues` class for further details on the relevant form entries.
	
	:return: HTTP response, containing the RDF data encoded in the format requested by the user (default: ``turtle``), or an error message if applicable
	:rtype: str

	On high level, the method:
	  - Extracts the RDFa data using the standard ``RDFLib`` RDFa parser in such a way that the "processor graph" (containing the warning and error triples detected by the parser) is also generated
	  - Interprets the processor graph triples by generating a human readable message in HTML
	  - Adds the extracted RDF graph to the output, serialized in turtle
	  - Returns the HTML content in the HTTP response.

	The real work is done in the separate :py:class:`.validator.Validator` class, this method is only a shell around that.
	"""
	form_values = FormValues(form)
	# Collect the data, depending on what mechanism is used in the form
	input, base = form_values.get_source_and_base(uri)
	try:
		validator = Validator(input, base,
								media_type      = form_values.media_type,
								vocab_expansion = form_values.vocab_expansion,
								check_lite      = form_values.check_lite,
								embedded_rdf    = form_values.embedded_rdf)

		header = 'Content-type: text/html; charset=utf-8\n'
		return header + "\n" + validator.run()
	except HTTPError:
		return handle_http_exception(uri, "HTTP Error in RDFa validation processing")
	except:
		return handle_general_exception(uri, "Error in RDFa validation processing", form_values,
		                                graph_choice = None, extracts = False)
