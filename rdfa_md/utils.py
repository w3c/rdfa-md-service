#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

if PY3:
	from io import StringIO
else:
	from StringIO import StringIO

from rdflib.plugins.parsers.pyRdfa.host import MediaTypes


#############################################################################################
# Common class to handle the (CGI) form object values
#############################################################################################
class FormValues(object):
	"""Various options to be extracted from the form (ie, a CGI FieldStorage instance)
	This class collects what is common in handling simple RDF parsing as well as for
	the validator.

	:param cgi.FieldStorage form: the query parameters of the original request.

	The meaning of the form values are. The "default" values are set in the local class attribute, when applicable and the form itself does not hold any value:

	- ``graph=[output|processor|output,processor|processor,output]``: specifying which graphs are returned. Default: ``output``.
	- ``format=[turtle|xml|json-ld|nt]``: serialization format for the output. Default: ``turtle``.
	- ``space_preserve=[true|false]``: means that plain literals are normalized in terms of white spaces. Default: ``false``. Also stored as a class attribute.
	- ``host_language=[xhtml,html,xml]``: the host language. Used when files are uploaded or text is added verbatim, otherwise the HTTP return header should be used. Default ``xml``. Also stored as a class attribute.
	- ``embedded_rdf=[true|false]``: whether embedded turtle or RDF/XML content should be added to the output graph. Default:``false``. Also stored as a class attribute.
	- ``vocab_expansion=[true|false]``: whether the vocabularies should be expanded through the `restricted RDFS entailment <https://www.w3.org/TR/rdfa-core/#s_vocab_expansion>`_. Default: ``false``. Also stored as a class attribute.
	- ``vocab_cache=[true|false]``: whether vocab caching should be performed or whether it should be ignored and vocabulary filesshould be picked up every time. Default: ``false``. Also stored as a class attribute.
	- ``vocab_cache_report=[true|false]``: whether vocab caching details should be reported. Default: ``false``. Also stored as a class attribute.
	- ``refresh_vocab_cache=[true|false]``: whether vocab caches have to be regenerated. Default: ``false``. . Also stored as a class attribute.
	- ``rdfa_lite=[true|false]``: whether warnings should be generated for non RDFa Lite attribute usage. Default: ``false``
	- ``rdfa_version=["1.1"|"1.0"]``: RDFa version. If missing, set to 1.1.
	- ``rdfagraph=["processor","output,processor","processor,output"]``: what graphs should be generated, see `the relevant section in the specification <https://www.w3.org/TR/rdfa-core/#accessing-the-processor-graph>`_ for further details.

    **Class attributes:**

	.. py:attribute:: form

	   Local storage of the form for further usage

	.. py:attribute:: keys

	   The keys of the form as a list

	.. py:attribute:: check_lite

	   boolean; whether the RDFa 1.1 Lite restrictions should be checked or not

	.. py:attribute:: media_type

	   media type; values are from the enumeration type class in :py:Class:`rdflib.plugins.parsers.pyRdfa.host.MediaType`

	.. py:attribute:: output_format

	   serialization format for the output

    **Class methods:**

	"""
	def __init__(self, form):
		self.form = form
		self.keys = list(form.keys())
		self.host_language       = self.get_value("host_language")
		self.media_type          = self._get_media_type()
		self.rdfa_version        = self.get_value("rdfa_version", "1.1")
		self.check_lite          = (self.get_value("rdfa_lite") == "true")
		self.embedded_rdf        = self.check_option("embedded_rdf", "true", False)
		self.space_preserve      = self.check_option("space_preserve", "true", True)
		self.vocab_cache         = self.check_option("vocab_cache", "true", True)
		self.vocab_cache_report  = self.check_option("vocab_cache_report", "true", False)
		self.refresh_vocab_cache = self.check_option("vocab_cache_refresh", "true", False)
		self.vocab_expansion     = self.check_option("vocab_expansion", "true", False)
		self.output_format       = self.get_value("format", "turtle")

	def _get_media_type(self):
		"""Get the media type, ie, convert the data in the form to the final MediaType values"""
		if self.host_language is None:
			media_type = ""
		elif self.host_language == "xhtml":
			media_type = MediaTypes.xhtml
		elif self.host_language == "html":
			media_type = MediaTypes.html
		elif self.host_language == "svg":
			media_type = MediaTypes.svg
		elif self.host_language == "atom":
			media_type = MediaTypes.atom
		else:
			media_type = MediaTypes.xml
		return media_type

	def get_value(self, key, default = None):
		"""Get a value if exists, set the default otherwise.

		:param str key: form key
		:param default: default value
		:type default: str or None
		:return: the corresponding form value or the default

		"""
		return self.form.getfirst(key).lower() if key in self.keys else default

	def get_value2(self, key1, key2):
		"""Get one of two options, in priority order, None if neither is present.

		:param str key1: form key
		:param str key2: form key
		:return: corresponding value or None

		"""
		retval = self.get_value(key1)
		return self.get_value(key2) if retval is None else retval

	def check_option(self, key, compare_value, default):
		"""Check how the value for `key` compares with the value. If no value
		is present, returns default.

		:param str key: form key
		:param str compare_value: value to compare with
		:param str default: value to compare with in case there is no value in the form
		:return: comparison resulting
		:rtype: bool
		"""
		# The second alternative is to ensure that the old style
		# parameters are still valid.
		# in the old days I used '-' in the parameters, the standard favours '_'
		val = self.get_value2(key, key.replace('_', '-'))
		return default if val is None else val == compare_value

	def get_source_and_base(self, uri):
		""" Return the location of the source data; usually it is a URI but,
		in some cases, it may return to the embedded data in the form.

		:param str uri: uri
		:return: uri and base pair
		:rtype: (uri,base) tuple
		"""
		# Collect the data, depending on what mechanism is used in the form
		if uri == "uploaded:":
			return (self.form["uploaded"].file, "")
		elif uri == "text:":
			return (StringIO(self.form.getfirst("text")), "")
		else:
			return (uri, uri)


#########################################################################################
#  Helper functions to handle exceptions
#########################################################################################
def handle_general_exception(uri, title, form_values, graph_choice = "", extracts = True, rdfa = True) :
	"""
	As its name suggests, handle a general exception by returning the right HTTP response in HTML.

	:param str uri: URI used in the original CGI script
	:param str title: title and header of the generated HTML
	:param form_values: the current form values
	:type form_values: :py:class:`FormValues`
	:param bool graph_choice: whether the choice of the graph (processor, output, etc) has a relevance
	:param bool extracts: whether this is related to an extraction (rdfa, microdata) or a validator
	:param bool rdfa: whether this is related to RDFa, as opposed to microdata
	:return: full HTTP response encoding the information in HTML
	:rtype: str

	This function *should* be invoked from an ``except`` clause.
	"""
	# This branch should occur only if an exception is really raised, ie, if it is not turned
	# into a graph value.
	retval =  'Status: 400 Invalid Input\n'
	retval += 'Content-type: text/html; charset=utf-8\n'
	retval += 'Status: %s\n' % 400
	retval += '\n'
	retval += "<html>\n"
	retval += "<head>\n"
	retval += "<title>%s</title>\n" % title
	retval += "</head><body>\n"
	retval += "<h1>%s</h1>\n" % title
	retval += "<pre>\n"
	strio  = StringIO()
	traceback.print_exc(file=strio)
	retval += strio.getvalue()
	retval += "</pre>\n"
	retval += "<h1>Distiller request details</h1>\n"
	retval += "<dl>\n"
	if uri == "text:" and "text" in form_values.form and form_values.form["text"].value is not None and len(form_values.form["text"].value.strip()) != 0:
		retval += "<dt>Text input:</dt><dd>%s</dd>\n" % cgi.escape(form_values.form["text"].value).replace('\n', '<br/>')
	elif uri == "uploaded:":
		retval += "<dt>Uploaded file</dt>\n"
	else :
		retval += "<dt>URI received:</dt><dd><code>'%s'</code></dd>\n" % cgi.escape(uri)
	if form_values.host_language:
		retval += "<dt>Media Type:</dt><dd>%s</dd>\n" % form_values.media_type
	if extracts:
		if rdfa:
			retval += "<dt>Requested graphs:</dt><dd>%s</dd>\n" % (graph_choice if graph_choice is not None else "default")
			retval += "<dt>Space preserve:</dt><dd>%s</dd>\n" % form_values.space_preserve
		retval += "<dt>Output serialization format:</dt><dd>%s</dd>\n" % form_values.output_format
	retval += "</dl>\n"
	retval += "</body>\n"
	retval += "</html>\n"
	return retval


def handle_http_exception(uri, title):
	"""Handle an ``HTTPError`` exception, by pulling together the HTTP response.

	:param str uri: URI used in the original CGI script
	:param str title: title and header of the generated HTML
	:return: full HTTP response encoding the information in HTML
	:rtype: str

	This function *should* be invoked from an ``except`` clause for an ``HTTPError``.
	"""
	(e_type, h, e_traceback) = sys.exc_info()
	retval =  'Status: 400 Invalid Input\n'
	retval += 'Content-type: text/html; charset=utf-8\n'
	retval += 'Status: %s\n' % h.http_code
	retval += "<html>\n"
	retval += "<head>\n"
	retval += "<title></title>\n" %s
	retval += "</head><body>\n"
	retval += "<h1>%s</h1>\n" % title
	retval += "<p>HTTP Error: %s (%s)</p>\n" % (h.http_code, h.msg)
	retval += "<p>On URI: <code>'%s'</code></p>\n" % cgi.escape(uri)
	retval += "</body>\n"
	retval += "</html>\n"
	return retval
