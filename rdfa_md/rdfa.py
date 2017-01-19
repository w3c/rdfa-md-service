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
	def _get_option(param, compare_value, default) :
		param_old = param.replace('_','-')
		if param in list(form.keys()) :
			val = form.getfirst(param).lower()
			return val == compare_value
		elif param_old in list(form.keys()) :
			# this is to ensure the old style parameters are still valid...
			# in the old days I used '-' in the parameters, the standard favours '_'
			val = form.getfirst(param_old).lower()
			return val == compare_value
		else :
			return default

	# Retrieve the output (serialziation) format
	if "format" in list(form.keys()) :
		outputFormat = form.getfirst("format")
	else :
		outputFormat = "turtle"

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
	# Note that these options should be used for the upload and inline version only in case of a form
	# for real uris the returned content type should be used
	if "host_language" in list(form.keys()) :
		if form.getfirst("host_language").lower() == "xhtml" :
			media_type = MediaTypes.xhtml
		elif form.getfirst("host_language").lower() == "html" :
			media_type = MediaTypes.html
		elif form.getfirst("host_language").lower() == "svg" :
			media_type = MediaTypes.svg
		elif form.getfirst("host_language").lower() == "atom" :
			media_type = MediaTypes.atom
		else :
			media_type = MediaTypes.xml
	else :
		media_type = ""

	check_lite = "rdfa_lite" in list(form.keys()) and form.getfirst("rdfa_lite").lower() == "true"

	output_default_graph 	= True
	output_processor_graph 	= False
	# Note that I use the 'graph' and the 'rdfagraph' form keys here. Reason is that
	# I used 'graph' in the previous versions, including the RDFa 1.0 processor,
	# so if I removed that altogether that would create backward incompatibilities
	# On the other hand, the RDFa 1.1 doc clearly refers to 'rdfagraph' as the standard
	# key.
	a = None
	if "graph" in list(form.keys()) :
		a = form.getfirst("graph").lower()
	elif "rdfagraph" in list(form.keys()) :
		a = form.getfirst("rdfagraph").lower()
	if a != None :
		if a == "processor" :
			output_default_graph 	= False
			output_processor_graph 	= True
		elif a == "processor,output" or a == "output,processor" :
			output_processor_graph 	= True

	# Get the other options from the form, setting also the default, if needed
	embedded_rdf        = _get_option( "embedded_rdf", "true", False)
	space_preserve      = _get_option( "space_preserve", "true", True)
	vocab_cache         = _get_option( "vocab_cache", "true", True)
	vocab_cache_report  = _get_option( "vocab_cache_report", "true", False)
	refresh_vocab_cache = _get_option( "vocab_cache_refresh", "true", False)
	vocab_expansion     = _get_option( "vocab_expansion", "true", False)
	if vocab_cache_report : output_processor_graph = True

	# Almost ready to work; creating the two empty RDF Graphs
	output_graph    = Graph()
	processor_graph = Graph()

	# This is the real meat: calling out to the RDFa parser.
	output_graph.parse(input,
					   format              = "rdfa",
					   pgraph              = processor_graph,
					   embedded_rdf        = embedded_rdf,
					   space_preserve      = space_preserve,
					   vocab_expansion     = vocab_expansion,
					   vocab_cache         = vocab_cache,
					   refresh_vocab_cache = refresh_vocab_cache,
					   vocab_cache_report  = vocab_cache_report,
					   check_lite          = check_lite
					   )

	# Next step is to create the final graph to be returned to the user; this depends on
	# whether the processor graph is required or not.
	final_graph = Graph()
	if output_default_graph :
		for t in output_graph : final_graph.add(t)
	if output_processor_graph :
		for t in processor_graph : final_graph.add(t)

	# The graph is serialized in the required format, and returned
	try :
		# "retval" collects the HTTP response; first the header with the content type,
		# Then the real data
		if outputFormat == "nt" :
			retval = 'Content-Type: application/n-triples; charset=utf-8\n'
			format = "nt"
		elif outputFormat == "turtle" :
			retval = 'Content-Type: text/turtle; charset=utf-8\n'
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
				retval = 'Content-Type: application/ld+json; charset=utf-8\n'
				format = "json-ld"
			except:
				retval = 'Content-Type: text/turtle; charset=utf-8\n'
				format = "turtle"
		else :
			retval = 'Content-Type: application/rdf+xml; charset=utf-8\n'
			format = "pretty-xml"
		retval += '\n'
		retval += final_graph.serialize(format=format)
		return retval
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
		if "host_language" in list(form.keys()) :
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
