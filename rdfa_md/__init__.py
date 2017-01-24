#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

__version__ = "1.0"
__author__  = 'Ivan Herman'
__contact__ = 'Ivan Herman, ivan@w3.org'
__license__ = 'W3C® SOFTWARE NOTICE AND LICENSE, https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document'

from .rdfa import extract_rdf, validate_rdfa

#########################################################################################
#  Helper functions to pre-process and check the incoming form data
#########################################################################################
def err_message(uri, msg) :
	"""Return an error message in HTTP/HTML and exit the script"""
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
	sys.exit(1)


def brett_test(uri) :
	"""Testing, when running on W3C, the safety of the URL.
	If the the test does not pass, ie an exception is raised somewhere down the line, an error message is sent back (via HTTP) to the caller, and everything stops.

	*Note that this runs only on the W3C site (using some local libraries)*

	@param uri: the URI to be checked.
	"""
	from checkremote import check_url_safety, UnsupportedResourceError
	if PY3:
		from urllib.error import HTTPError, URLError
	else:
		from urllib2 import HTTPError, URLError
	try:
		check_url_safety(uri)
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
