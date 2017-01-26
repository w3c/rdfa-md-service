#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
"""
The only function in this module (:py:func:`extract_microdata`) is used to extract RDF data, encoded in microdata, from an HTML source.

"""
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

if PY3:
	from urllib.error import HTTPError
else:
	from urllib2 import HTTPError

# The import to cgi is necessary for the proper documentation!
import cgi
from rdflib import Graph
from rdflib.plugins.parsers.pyRdfa.host import MediaTypes
from .utils import FormValues, handle_http_exception, handle_general_exception

#########################################################################################
# RDF Extraction:  use the RDFLib parser to extract the RDF graph, serialize it and
# return to the caller
# In case or problems, an HTTP response is generated incorporating the Exception data and
# some basic information on the calling parameters.
#########################################################################################
def extract_microdata(uri, form) :
	"""
	Extract microdata data from HTML and returns the resulting RDF data.

	:param str uri: URI for the HTML data. Note that the ``text:`` and ``uploaded`` fake URI values are treated separately; the former is for textual intput (in which case a ``StringIO`` instance is used to get the data) and the latter is for uploaded file, where the form gives access to the file directly.

	:param cgi.FieldStorage form: the query parameters of the original request
	
	:return: HTTP response, containing the RDF data encoded in the format requested by the user (default: ``turtle``), or an error message if applicable
	:rtype: str

	The function parses the HTML content using the built-in ``RDFLib`` microdata parser, and serializes the resulting RDF data using the serializaiton format requested by the user and returns the results. Serialization relies on the built-in ``RDFLib`` serializer for ``turtle``, ``nt``, or ``RDF/XML``, and on an ``RDFLib`` extension package (``rdflib_jsonld``) for ``JSON-LD``.
	"""

	form_values = FormValues(form)

	# Collect the data, depending on what mechanism is used in the form
	input, base = form_values.get_source_and_base(uri)

	# Almost ready to work; creating the two RDF Graphs
	output_graph    = Graph()

	# The graph is serialized in the required format, and returned
	try :
		# This is the real meat: calling out to the RDFa parser.
		output_graph.parse(input,
						   format              = "microdata",
						   vocab_expansion     = form_values.vocab_expansion,
						   vocab_cache         = form_values.vocab_cache
						   )

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
		return header + "\n" + output_graph.serialize(format=format)
	except HTTPError:
		return handle_http_exception(uri, "HTTP Error in extracting microdata")
	except Exception as e:
		return handle_general_exception(uri, "Exception in extracting microdata", form_values,
		                                graph_choice = None, extracts = True, rdfa = False)
