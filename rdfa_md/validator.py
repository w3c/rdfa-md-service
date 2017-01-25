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
	Shell around the distiller and the error message management.
	@ivar default_graph: default graph for the results
	@ivar processor_graph: processor graph (ie, errors and warnings)
	@ivar uri: file like object or URI of the source
	@ivar base: base value for the generated RDF output
	@ivar media_type: media type of the source
	@ivar vocab_expansion: whether vocabulary expansion should occur or not
	@ivar check_lite: whether RDFa 1.1 Lite should be checked
	@ivar hturtle: whether the embedded turtle should be included in the output
	@ivar domtree: the Document Node of the final domtree where the final HTML code should be added
	@ivar message: the Element Node in the final DOM Tree where the error/warning messages should be added
	@ivar code: the Element Node in the final DOM Tree where the generated code should be added
	@ivar errors: separate class instance to generate the error code
	@type errors: L{Errors}
	"""
	def __init__(self, uri, base, media_type = "", vocab_expansion = False, check_lite = False, embedded_rdf = False):
		"""
		@param uri: the URI for the content to be analyzed
		@type uri: file-like object (e.g., when content goes through an HTTP Post) or a string
		@param base: the base URI for the generated RDF
		@type base: string
		@param media_type: Media Type, see the media type management of pyRdfa. If "", the distiller will try to find the media type out.
		@type media_type: pyRdfa.host.MediaTypes value
		"""
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
		Parse the RDFa input and store the processor and default graphs. The final media type is also updated.
		"""
		#
		# The reason why we have to go down the 'guts' of the RDFa parser plugin is in the
		# RDFa lite checking below. What that extra 'transformer' does in the parser is to
		# add RDFa Lite specific triples into the processor graph which is used to generate
		# the relevant warning. If that step was not used or necessary, we could remain on the
		# "user" level and simply use the 'official' parsing of the incoming data.
		# Oh well...
		#
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
		Add the generated graph, in turtle encoding, as well as the error messages, to the final DOM tree
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
		Run the two steps of validation, and return the serialized version of the DOM Tree, ready to be displayed
		"""
		self.parse()
		self.complete_DOM()
		return self.domtree.toxml(encoding="utf-8")
