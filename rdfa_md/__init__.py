#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
"""
These error handling methods are not meant to be used by the rest of the package but, rather, the CGI interface doing extra checks before proceeding with the real RDF data extraction.

"""
from __future__ import print_function

__version__ = "1.0"
__author__  = 'Ivan Herman'
__contact__ = 'Ivan Herman, ivan@w3.org'
__license__ = 'W3C® SOFTWARE NOTICE AND LICENSE, https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document'

import sys
PY3 = (sys.version_info[0] >= 3)
if PY3:
	from io import StringIO
	from urllib.error import HTTPError
else :
	from StringIO import StringIO
	from urllib2 import HTTPError

from .rdfa  import extract_rdf, validate_rdfa
from .mdata import extract_microdata
import traceback, cgi


#########################################################################################
#  Helper functions to pre-process and check the incoming form data; used by the CGI scripts
#########################################################################################
def err_message(uri, msg):
	"""
	Prints an error message as an HTTP response in HTML.
	
	:param str uri: The URI used to start up the script
	:param str msg: The extra message to be displayed

	This function is called on the topmost CGI level, before the extraction/validation has started.
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
	if len(msg) != 0:
		print("<p>")
		clean_print(msg)
		print("</p>")
	print("</body>")
	print("</html>")


def brett_test(uri):
	"""
	Test, when running on W3C, the safety of the URL.

	:param str uri: The URI used to start up the script
	:return: result of the check
	:rtype: Boolean

	If the the test does not pass, ie an exception is raised somewhere down the line, an error message is sent back (via HTTP) to the caller.

	Contributed by Brett Smith, W3C, and relying on an external library (``check_url_safety``) running at the W3C. *This method runs only on the W3C site and its invocation must be preceded by an appropriate check*.
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
		args = len(e.args)
		msg = "" if args == 0 else (e.args[0] if args == 1 else repr(e.args))
		err_message(uri, 'Exception raised: "%s"' % msg)

	# If we got here one of the exceptions were handled, ie, the result of the check
	# is False...
	return False
