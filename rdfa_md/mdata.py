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

if PY3 :
	from urllib.error import HTTPError
else :
	from urllib2 import HTTPError

from rdflib import Graph
from rdflib.plugins.parsers.pyRdfa.host import MediaTypes
from .validator import Validator
from .utils import FormValues, handle_http_exception, handle_general_exception
