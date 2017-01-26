# -*- coding: utf-8 -*-
"""
Separate shell to generate human readable error/warning messages
"""
from __future__ import print_function
import sys

import rdflib
from rdflib import RDF  as ns_rdf
from rdflib import RDFS as ns_rdfs
from rdflib.plugins.parsers.pyRdfa         import ns_rdfa, ns_xsd, ns_distill
from rdflib.plugins.parsers.pyRdfa.options import ns_dc, ns_ht
from rdflib.plugins.parsers.pyRdfa         import RDFA_Error, RDFA_Warning, RDFA_Info
from pyRdfa.options import ns_dc, ns_ht


class Errors:
	"""
	Shell to generate error and warning messages to the output

	:param Validator validator: the validator instance that creates this instance

	**Class variables:**

	.. py:attribute:: domtree

	   the Document Node of the target DOM tree; originates from the instantiating :py:class:`~.validator.Validator` instance.

	.. py:attribute:: target

	   the Element node for the error messages; originates from the instantiating :py:class:`~.validator.Validator` instance.

	.. py:attribute:: error_graph

	   the RDFLib Graph to extract the error messages from; originates from the instantiating :py:class:`~.validator.Validator` instance.

	.. py:attribute:: validator

	   the :py:class:`~.validator.Validator` instance that has created this instance

	**Class methods:**
	"""
	def __init__(self, validator):
		# This is where the error messages are to be added
		self.domtree     = validator.domtree
		self.target	     = validator.message
		self.error_graph = validator.processor_graph
		self.validator   = validator

	def _add_element_and_string(self, parent, element, text, **attrs):
		"""
		Add a DOM element to the parent (unless element == "") and add a text node to the results

		:param Element parent: where to add the content
		:param str element: element name for the new node; if "", this is skipped
		:param str text: text to add as a text node
		:param attrs: key value pairs for attributes to be added to the new element
		"""
		if element != "":
			e = self.domtree.createElement(element)
			for key in attrs:
				e.setAttribute(key, "%s" % attrs[key])
			e.appendChild(self.domtree.createTextNode(text))
			parent.appendChild(e)
		else:
			parent.appendChild(self.domtree.createTextNode(text))

	def _add_string(self, text, element = "p"):
		"""
		Add a DOM element to the error block (unless element == "") and add a text node to the results

		:param str element: element name for the new node; if "", this is skipped
		:param str text: text to add as a text node
		"""
		self._add_element_and_string(self.target, element, text)

	def header(self, e, w, i):
		"""
		Generate a header for 'e' errors, 'w' warnings and 'i' information elements. Care is taken to produce
		a gramatically correct English sentence. The result is added to the DOM tree (via the :py:meth:`_add_string` method)

		:param int e: number of errors
		:param int w: number of warnings
		:param int i: number of information elements

		"""
		if e != 0:
			if e == 1:  error = "is one error "
			elif e > 1: error = "are %s errors " % e

			if i + w > 0:
				if w > 0:
					if w == 1: warning = "one warning"
					else:      warning = "%s warnings" % w

					if i == 0:  info = ""
					elif i== 1: info = " plus one informational message"
					else:       info = " plus %s informational messages" % i
					text = "There %s (and %s%s) in your RDFa content" % (error, warning, info)
				else:
					if i == 0:   info = ""
					elif i == 1: info = "(and one informational message)"
					else:        info = "(and %s informational messages)" % i
					text = "There %s %s in your RDFa content" % (error, info)
			else:
				text = "There " + error + "in your RDFa content"
		else:
			if w > 0:
				if w == 1: warning = "is one warning"
				else:      warning = "are %s warnings" % w
				if i == 0: info  = ""
				elif i== 1: info = " and one informational message"
				else:      info  = " and %s informational messages" % i
				text = "Congratulations, your RDFa source is valid; however there %s %s in your RDFa content that you might want to check" % (warning, info)
			else :
				if i == 1: info = "is one informational message"
				else:      info = "are %s informational messages" % i
				text = "Congratulations, your RDFa source is valid; however there %s in your RDFa content that you might want to check" % info
		self._add_string(text)

	def one_message(self, subj, header):
		"""
		Add a single message to the output in the form of a paragraph with ``<span>`` elements

		:param subj: RDF subject for the error (this is either an ``RDFLib`` ``URIRef`` or a ``BNode``)
		:param str header: one of "Error", "Warning", or "Info", added to the final message’s span as a class name, used for CSS
		"""
		for (x, y, desc) in self.error_graph.triples((subj, ns_dc["description"], None)):
			p = self.domtree.createElement("p")
			self.target.appendChild(p)
			p.setAttribute("class", header)
			self._add_element_and_string(p, "span", header)
			self._add_element_and_string(p, "", ": ")
			self._add_element_and_string(p, "span", desc)

	def messages(self, title, msgs, header):
		"""
		Add blocks of messages, preceded by an ``<h3>`` element for the title.

		:param str title: title string for the header
		:param list msgs: array of error subjects (ie, RDFLib Nodes)
		:param str header: one of "Error", "Warning", or "Info", added to the final message's span as a class name, used for CSS
		"""
		self._add_element_and_string(self.target, "h3", title)
		for msg in msgs:
			self.one_message(msg, header)

	def sort_array(self, arr):
		"""
		Sort the entries of the arrays consiting of subjects of messages. Sorting is based on the time stamp that is
		added to each of those messages by the ``RDFLib`` parser.

		:param list arr: array of RDF triples
		"""
		to_sort = []
		for subj in arr:
			date = ""
			for (x, y, date) in self.error_graph.triples((subj, ns_dc["date"], None)):
				break
			to_sort.append((subj, date))
		to_sort.sort(key = lambda x: x[1])
		# This was the Python2 version...
		# to_sort.sort(cmp = lambda x,y : cmp(x[1],y[1]))
		return [subj for (subj, obj) in to_sort]

	def interpret(self):
		"""
		Interpret the processor graph: separate the warnings, errors, and information elements by message type,
		and displays the generated message strings in three different categories.
		"""
		def _add_info():
			if self.validator.check_lite:
				self._add_string("(Checked RDFa %s Lite, with %s as host language.)" % (self.validator.processor.rdfa_version, self.validator.processor.options.host_language))
			else:
				self._add_string("(Checked RDFa %s, with %s as host language.)" % (self.validator.processor.rdfa_version, self.validator.processor.options.host_language))

		errors   = self.sort_array([b for (b, x, y) in self.error_graph.triples((None, ns_rdf["type"], RDFA_Error))])
		warnings = self.sort_array([b for (b, x, y) in self.error_graph.triples((None, ns_rdf["type"], RDFA_Warning))])
		infos    = self.sort_array([b for (b, x, y) in self.error_graph.triples((None, ns_rdf["type"], RDFA_Info))])
		if len(errors) == 0 and len(warnings) == 0 and len(infos) == 0:
			self._add_string("Congratulations, your RDFa source is valid!")
			_add_info()
			return

		self.header(len(errors), len(warnings), len(infos))
		_add_info()

		if len(errors) != 0:
			self.messages("Errors", errors, "Error")
		if len(warnings) != 0:
			self.messages("Warnings", warnings, "Warning")
		if len(infos) != 0:
			self.messages("Informational messages", infos, "Info")
