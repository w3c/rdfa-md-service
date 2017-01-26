#!/usr/bin/python
# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
"""
CGI entry point for the Microdata extraction via RDFLib.

This version is adapted, for Python paths, to the particualarities of the W3C setup as well as my own machine. On a specific installation things have to be re-adapted in a fairly straightforward manner.

"""
from __future__ import print_function
__version__ = "1.0"
import cgi
import cgitb
import sys, os
#cgi.print_environ()

# Necessary setup on various environments. This may have to be adapted when
# installing the scripts on another architecture. "darwin" refers to my local
# Mac (and is therefore used for testing); W3C runs on linux machines.
if sys.platform == "darwin" :
	# this is my local machine
	sys.path.insert(0,"/Users/ivan/Library/Python")
	os.environ['PyRdfaCacheDir'] = '/Users/ivan/.pyrdfa-cache'
	running_at_w3c = False
	cgitb.enable()
else :
	# this is the server on W3C
	sys.path.insert(0,"/usr/local/lib/python2.4/site-packages/PythonLib-IH")
	sys.path.insert(0,"/usr/local/lib/python2.4/site-packages/PythonLib-IH/rdfa-1.1")
	os.environ['PyRdfaCacheDir'] = '/usr/local/apache/cgi/cgi-bin-other/RDFa/data-local'
	running_at_w3c = True
	cgitb.enable(display=0, logdir="/home/nobody/tracebacks/")

from rdfa_md import extract_microdata, err_message, brett_test


def uri_test(uri) :
	"""Testing, when running on W3C, the safety of the URL.
	If the the test does not pass, ie an exception is raised somewhere down the line, an error message is sent back (via HTTP) to the caller, and everything stops.

	If this test reveals any problem, the script exits!!!

	:param uri: the URI to be checked.
	"""
	if running_at_w3c and not brett_test(uri): sys.exit(1)

def process_input(form):
	"""Pre-rocess the form data. If all checking and processing is fine, call out to processURI
	to do the real work.

	:param form: form data, as returned by Python's FieldStorage
	"""

	uri = ""
	# The 'uri' term is modified to be turned into a 'fake' value to denote the upload and text cases.
	if "uploaded" in form and form["uploaded"].file :
		# The real data is stored in the form as a reference to a file
		uri = "uploaded:"
	elif "text" in form and form["text"].value != None and len(form["text"].value.strip()) != 0 :
		uri  = "text:"
	else :
		# Either there is an error, and we have to stop there, or it is a real URI
		if not "uri" in form :
			print('Content-type: text/html; charset=utf-8')
			print('Status: 400 Invalid Input')
			print("")
			print("<html>")
			print("<head>")
			print("<title>Error in Microdata processing</title>")
			print("</head><body>")
			print("<h1>Error in converting Microdata</h1>")
			print("<p>No URI has been specified</p>")
			print("</body>")
			print("</html>")
			sys.exit(1)

		try :
			uri = form.getfirst("uri")
		except :
			print('Content-type: text/html; charset=utf-8')
			print('Status: 400 Invalid Input')
			print("")
			print("<html>")
			print("<head>")
			print("<title>Error in Microdata processing</title>")
			print("</head><body>")
			print("<h1>rror in converting Microdata</h1>")
			print("No URI has been specified")
			print("</body>")
			print("</html>")
			sys.exit(1)

	# If we got here, we should have the data hidden, in some way or other, behind the form data
	# and/or the URI
	try :
		# Thanks to Sergio and Diego for the idea and code for the referer branch
		if uri == "referer" :
			uri = os.getenv('HTTP_REFERER')
			if uri is None:
				newuri = "http://www.w3.org/2012/pyMicrodata/no_referer.html"
			else:
				uri_test(uri)
				newuri = "http://www.w3.org/2012/pyMicrodata/extract?uri=" + uri
			print("Status: 307 Moved Temporarily")
			print("Location: " + newuri)
			print("")
		else :
			# last point of check: use Brett's script to check the validity of the URI
			# Note that if the test reveals any problems, the script returns a message and exists
			if not (uri == 'text:' or uri == 'uploaded:') : uri_test(uri)

			print( extract_microdata(uri, form) )
	except Exception as e :
		l = len(e.args)
		msg = "" if l == 0 else (e.args[0] if l == 1 else repr(e.args))
		err_message(uri, 'Exception raised: "%s"' % msg)



#######################################################################################
if __name__ == '__main__':
	process_input(cgi.FieldStorage())

# The real CGI processing!!
