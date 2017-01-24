#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
from __future__ import print_function

__version__ = "1.0"
__author__  = 'Ivan Herman'
__contact__ = 'Ivan Herman, ivan@w3.org'
__license__ = 'W3C® SOFTWARE NOTICE AND LICENSE, https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document'

import sys
PY3 = (sys.version_info[0] >= 3)
if PY3 :
	from io import StringIO
	from urllib.error import HTTPError
else :
	from StringIO import StringIO
	from urllib2 import HTTPError

from .rdfa import extract_rdf, validate_rdfa
import traceback, cgi


#########################################################################################
#  Helper functions to pre-process and check the incoming form data
#########################################################################################
def err_message(uri, msg) :
	"""Return an error message in HTTP/HTML and exit the script. This is called on the topmost
	CGI level, not once the extraction/validation has started.
	"""
	from .cleanhtml import clean_print
	print('Content-type: text/html; charset=utf-8')
	print('Status: 400 Invalid Input')
	print("")
	print("<html>")
	print("<head>")
	print("<title>Error in RDFa processing</title>")
	print("</head><body>")
	print("<h1>Error in distilling RDFa</h1>")
	print("<p>")
	clean_print("pyRdfa cannot process this URI: %s", uri)
	print("</p>")
	if len(msg) != 0 :
		print("<p>")
		clean_print(msg)
		print("</p>")
	print("</body>")
	print("</html>")


def brett_test(uri) :
	"""Testing, when running on W3C, the safety of the URL.
	If the the test does not pass, ie an exception is raised somewhere down the line, an error message is sent back (via HTTP) to the caller, and everything stops.

	*Note that this runs only on the W3C site (using a local Library)*
	"""
	from checkremote import check_url_safety, UnsupportedResourceError
	if PY3:
		from urllib.error import HTTPError, URLError
	else:
		from urllib2 import HTTPError, URLError
	try:
		check_url_safety(uri)
		# If we got here, there have been no issues; Brett's script simply raises exceptions
		return True
	except HTTPError as e:
		err_message(uri, 'HTTP Error with the error code: %s and the error message: "%s"' (e.code, e.reason))
	except URLError as e:
		err_message(uri, 'URL Error with the error message: "%s"' % e.reason)
	except UnsupportedResourceError as e:
		msg = e.args[0] + ": " + e.args[1]
		err_message(uri, 'Unsupported Resource Error with the error message "%s"' % msg)
	except Exception as e:
		l = len(e.args)
		msg = "" if l == 0 else (e.args[0] if l == 1 else repr(e.args))
		err_message(uri, 'Exception raised: "%s"' % msg)

	# If we got here one of the exceptions were handled, ie, the result of the check
	# is False...
	return False


#########################################################################################
#  Helper functions to handle exceptions
#########################################################################################
def handle_general_exception(uri, title, form_values, graph_choice = "", extracts = True) :
	"""
	As its name suggests, handle a general exception by returning the right HTTP response in HTML
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
	retval +="</pre>\n"
	retval +="<h1>Distiller request details</h1>\n"
	retval +="<dl>\n"
	if uri == "text:" and "text" in form_values.form and form_values.form["text"].value != None and len(form_values.form["text"].value.strip()) != 0 :
		retval +="<dt>Text input:</dt><dd>%s</dd>\n" % cgi.escape(form_values.form["text"].value).replace('\n','<br/>')
	elif uri == "uploaded:" :
		retval +="<dt>Uploaded file</dt>\n"
	else :
		retval +="<dt>URI received:</dt><dd><code>'%s'</code></dd>\n" % cgi.escape(uri)
	if form_values.host_language :
		retval +="<dt>Media Type:</dt><dd>%s</dd>\n" % form_values.media_type
	if extracts:
		retval += "<dt>Requested graphs:</dt><dd>%s</dd>\n" % (graph_choice if graph_choice is not None else "default")
		retval += "<dt>Output serialization format:</dt><dd>%s</dd>\n" % form_values.output_format
		retval += "<dt>Space preserve:</dt><dd>%s</dd>\n" % form_values.space_preserve
	retval += "</dl>\n"
	retval += "</body>\n"
	retval += "</html>\n"
	return retval


def handle_http_exception(uri, title):
	"""Handle an HTTPError exception, by pulling together the HTTP response.
	This must be invoked from an except clause for an HTTPError
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
	retval += "<p>HTTP Error: %s (%s)</p>\n" % (h.http_code,h.msg)
	retval += "<p>On URI: <code>'%s'</code></p>\n" % cgi.escape(uri)
	retval += "</body>\n"
	retval += "</html>\n"
	return retval
