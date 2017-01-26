# -*- coding: utf-8 -*-
# Maintainer: Ivan Herman <ivan@w3.org>
"""
Class to encapsulate the common data, and relevant methods, to perform RDFa validation

"""
from __future__ import print_function
import sys
PY3 = (sys.version_info[0] >= 3)

if PY3:
	from io import StringIO
	from urllib.error import HTTPError
else:
	from StringIO import StringIO
	from urllib2 import HTTPError
import xml.dom.minidom
from datetime import date

from rdflib import Graph
from rdflib.plugins.parsers.pyRdfa.host    import MediaTypes
from rdflib.plugins.parsers.pyRdfa         import pyRdfa
from rdflib.plugins.parsers.pyRdfa.options import Options

from .validator_html	import html_page
from .validator_errors  import Errors

class Validator:
	"""
	Shell to handle the validation process

	:param uri: the URI for the content to be analyzed. Also stored as a class attribute.
	:type uri: a file-like object  (e.g, when the content is uploaded by the user) or a string.
	:param str base: the base URI for the generated RDF. Also stored as a class attribute.

	:param media_type: media type, when provided by the user. If "" or `None`, the distiller will try to find the media type itself.
	:type media_type: enumeration type class in :py:Class:`rdflib.plugins.parsers.pyRdfa.host.MediaType`

	:param bool vocab_expansion: whether the vocabulary `expansion feature of RDFa
	 <https://www.w3.org/TR/rdfa-core/#s_vocab_expansion>`_ should also be executed. Also stored as a class attribute.

	:param bool check_lite: whether extra checks on the source being valid RDFa 1.1 Lite should be executed. Also stored as a class attribute.

	:param embedded_rdf: whether extra RDF data, embedded via a ``<script>`` element and encoded in Turtle, should be added to the final results. Also stored as a class attribute.

	When initialized, a domtree is created (by the standard Python `minidom` package), using the HTML template pattern in :py:obj:`~.validator_html.html_page`. This DOM tree is completed, after parsing, with the interpretation of the error/warning triples and the encoded RDFa graph.

	**Additional class variables:**

	.. py:attribute:: default_graph

	   an ``RDFLib`` graph, holding the generated RDF data

	.. py:attribute:: processor_graph

	   an ``RDFLib`` graph, holding the error/warning/information triples

	.. py:attribute:: domtree

	   the DOM tree to hold the final message to the caller

	.. py:attribute:: message

	   element in the DOM tree where the final messages must be stored (a ``<div>`` element)

	.. py:attribute:: code

	   element in the DOM tree where the serialized output graph should be stored (a ``<code>`` element)

	.. py:attribute:: Errors

	   an instance of a :py:class:`~.validator_errors.Errors` class, initialized by this class instance

	**Class methods:**

	"""
	def __init__(self, uri, base, media_type = "", vocab_expansion = False, check_lite = False, embedded_rdf = False):
		# Create the graphs into which the content is put
		self.default_graph   = Graph()
		self.processor_graph = Graph()
		self.uri 			 = uri
		self.base			 = base
		self.media_type		 = media_type
		self.embedded_rdf	 = embedded_rdf
		self.check_lite		 = check_lite
		self.vocab_expansion = vocab_expansion

		# Get the DOM tree that will be the scaffold for the output
		self.domtree = xml.dom.minidom.parse(StringIO(html_page % date.today().isoformat()))

		# find the warning/error content
		for div in self.domtree.getElementsByTagName("div"):
			if div.hasAttribute("id") and div.getAttribute("id") == "Message":
				self.message = div
				break

		# find the turtle output content
		for pre in self.domtree.getElementsByTagName("pre"):
			if pre.hasAttribute("id") and pre.getAttribute("id") == "output":
				self.code = pre
				break

		self.errors = Errors(self)
	# end __init__

	def parse(self):
		"""
		Parse the RDFa input and store the processor and default graphs. The final media type in the class instance also updated.

		*Implementation note:* this method goes down into the "guts" of the RDFa parser plugin of `RDFLib`, instead of simply executing a simple parsing. The reason is that the parser does not "expose", on the top level, an extra "transformer" function that checks the RDFa 1.1 Lite features (and adds warning triples to the processor graph), and this can only be added to the parser using one step deeper into the plugin code. (See the :py:func:`rdflib.plugins.parsers.pyRdfa.transform.lite.lite_prune` function).
		"""
		transformers = []
		if self.check_lite:
			from rdflib.plugins.parsers.pyRdfa.transform.lite import lite_prune
			transformers.append(lite_prune)

		options = Options(output_default_graph = True, output_processor_graph = True,
						  transformers    = transformers,
						  vocab_expansion = self.vocab_expansion,
						  embedded_rdf    = self.embedded_rdf,
						  add_informational_messages = True)
		processor = pyRdfa(options = options, base = self.base, media_type = self.media_type)
		processor.graph_from_source(self.uri, graph = self.default_graph, pgraph = self.processor_graph, rdfOutput = True)
		# Extracting some parameters for the error messages
		self.processor 	= processor

	def complete_DOM(self):
		"""
		Add the generated graph, in turtle encoding, as well as the error messages, to the final DOM tree. Interpreting the the error messages is done by the separate :py:class:`.validator_errors.Errors` class instance (whose instance is initialized when this class is created).
		"""
		# Add the RDF code in the DOM tree
		outp = self.default_graph.serialize(format="turtle")
		u = outp if PY3 else unicode(outp.decode('utf-8'))
		dstr = self.domtree.createTextNode(u)
		self.code.appendChild(dstr)
		# Settle the error message
		self.errors.interpret()

	def run(self):
		"""
		Run the two steps of validation (parsing and completing the DOM), and return the serialized version of the DOM, ready to be displayed
		"""
		self.parse()
		self.complete_DOM()
		return self.domtree.toxml(encoding="utf-8")
