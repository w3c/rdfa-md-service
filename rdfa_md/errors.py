# -*- coding: utf-8 -*-
"""
RDFa 1.1 validator. Separate shell to generate error/warning messages

@summary: RDFa validator
@requires: Python version 2.5 or up
@requires: U{RDFLib<http://rdflib.net>}; version 3.X is preferred, it has a more readable output serialization.
@requires: U{html5lib<http://code.google.com/p/html5lib/>} for the HTML5 parsing.
@requires: U{httpheader<http://deron.meranda.us/python/httpheader/>}; however, a small modification had to make on the original file, so for this reason and to make distribution easier this module (single file) is added to the distributed tarball.
@requires: U{pyRdfa<http://www.w3.org/2007/08/pyrdfa/>}, version 3.X (i.e., corresponding to RDFa 1.1)
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@var html_page: the XHTML code as a template for the output
"""

import sys

import rdflib
from rdflib	import RDF  as ns_rdf
from rdflib	import RDFS as ns_rdfs
from rdflib.plugins.parsers.pyRdfa         import ns_rdfa, ns_xsd, ns_distill
from rdflib.plugins.parsers.pyRdfa.options import ns_dc, ns_ht
from rdflib.plugins.parsers.pyRdfa         import RDFA_Error, RDFA_Warning, RDFA_Info
from pyRdfa.options	import ns_dc, ns_ht

class Errors :
	"""
	Shell to generate error and warning messages to the output
	@ivar domtree: the Document Node of the target DOM tree
	@ivar target: the Element node for the error messages
	@ivar error_graph: the RDFLib Graph to extract the error messages from
	"""
	def __init__(self, validator) :
		"""
		@param validator: the validator instance that creates this instance
		"""
		# This is where the error messages are to be added
		self.domtree		= validator.domtree
		self.target			= validator.message
		self.error_graph	= validator.processor_graph
		self.validator		= validator

	def _add_element_and_string(self, parent, element, str, **attrs) :
		"""
		Helper method: add a DOM element to the parent (unless element == "") and add a text node to the results
		@param parent: where to add the content
		@type parent: DOM Element Node
		@param element: element name for the new node; if "", this is skipped
		@type element: string
		@param str: text to add as a text node
		@param attrs: key value pairs for attributes to be added to the new element
		"""
		if element != "" :
			e = self.domtree.createElement(element)
			for key in list(attrs.keys()) :
				e.setAttribute(key,"%s" % attrs[key])
			e.appendChild(self.domtree.createTextNode(str))
			parent.appendChild(e)
		else :
			parent.appendChild(self.domtree.createTextNode(str))

	def _add_string(self, str, element = "p") :
		"""
		Helper method: add a DOM element to the error block (unless element == "") and add a text node to the results
		@param element: element name for the new node; if "", this is skipped
		@type element: string
		@param str: text to add as a text node
		@param attrs: key value pairs for attributes to be added to the new element
		"""
		self._add_element_and_string(self.target,element,str)

	def header(self, e,w,i) :
		"""
		Generate a header for 'e' errors, 'w' warnings and 'i' information elements. Care is taken to produce
		a gramatically correct English sentence. The restult is added to the DOM tree.
		@param e: number of errors
		@type e: integer
		@param w: number of warnings
		@type w: integer
		@param i: number of information elements
		@type i: integer
		"""
		if e != 0 :
			if e == 1 : error = "is one error "
			elif e > 1 : error = "are %s errors " % e

			if i + w > 0 :
				if w > 0 :
					if w == 1 : warning = "one warning"
					else :      warning = "%s warnings" % w
					if i == 0 : info = ""
					elif i== 1 : info = " plus one informational message"
					else :      info = " plus %s informational messages" % i
					str = "There %s (and %s%s) in your RDFa content" % (error,warning,info)
				else :
					if i == 0 : info = ""
					elif i == 1 : info = "(and one informational message)"
					else :      info = "(and %s informational messages)" % i
					str = "There %s %s in your RDFa content" % (error,info)
			else :
				str = "There " + error + "in your RDFa content"
		else :
			if w > 0 :
				if w == 1 : warning = "is one warning"
				else :      warning = "are %s warnings" % w
				if i == 0 : info = ""
				elif i== 1 : info = " and one informational message"
				else :      info = " and %s informational messages" % i
				str = "Congratulations, your RDFa source is valid; however there %s %s in your RDFa content that you might want to check" % (warning,info)
			else :
				if i == 1 : info = "is one informational message"
				else :      info = "are %s informational messages" % i
				str = "Congratulations, your RDFa source is valid; however there %s in your RDFa content that you might want to check" % info
		self._add_string(str)

	def one_message(self, subj, header) :
		"""
		Add a single message to the output
		@param subj: RDF subject for the error
		@type subj: RDFLib URIRef or BNode
		@param header: one of "Error", "Warning", or "Info", added to the final message's span as a class name, used for CSS
		"""
		for (x,y,desc) in self.error_graph.triples((subj,ns_dc["description"],None)) :
			p = self.domtree.createElement("p")
			self.target.appendChild(p)
			p.setAttribute("class", header)
			self._add_element_and_string(p,"span", header)
			self._add_element_and_string(p,"",": ")
			self._add_element_and_string(p, "span", desc)

	def messages(self, title, msgs, header) :
		"""
		Add blocks of messages, preceded by an <h3> element for the title.
		@param title: title string for the header
		@param msgs: array of error subjects (ie, RDFLib Nodes)
		@param header: one of "Error", "Warning", or "Info", added to the final message's span as a class name, used for CSS
		"""
		self._add_element_and_string(self.target, "h3", title)
		for msg in msgs :
			self.one_message(msg, header)

	def sort_array(self, arr) :
		"""
		Sort the entries of the arrays consiting of subjects of messages. Sorting is based on the time stamp that is
		added to each of those messages.
		"""
		to_sort = []
		for subj in arr :
			date = ""
			for (x,y,date) in self.error_graph.triples((subj, ns_dc["date"], None)) :
				break
			to_sort.append((subj,date))
		to_sort.sort(cmp = lambda x,y : cmp(x[1],y[1]))
		return [subj for (subj,obj) in to_sort]

	def interpret(self) :
		"""
		Interpret the processor graph. Separates the warnings, errors, and information elements by message type,
		and displays the generated message strings in three different categories.
		"""
		def _add_info() :
			if self.validator.rdfa_lite :
				self._add_string("(Checked RDFa %s Lite, with %s as host language.)" % (self.validator.processor.rdfa_version, self.validator.processor.options.host_language))
			else :
				self._add_string("(Checked RDFa %s, with %s as host language.)" % (self.validator.processor.rdfa_version, self.validator.processor.options.host_language))

		errors   = self.sort_array([ b for (b,x,y) in self.error_graph.triples((None, ns_rdf["type"], RDFA_Error)) ])
		warnings = self.sort_array([ b for (b,x,y) in self.error_graph.triples((None, ns_rdf["type"], RDFA_Warning)) ])
		infos    = self.sort_array([ b for (b,x,y) in self.error_graph.triples((None, ns_rdf["type"], RDFA_Info)) ])
		if len(errors) == 0 and len(warnings) == 0 and len(infos) == 0 :
			self._add_string("Congratulations, your RDFa source is valid!")
			_add_info()
			return

		self.header(len(errors),len(warnings),len(infos))
		_add_info()

		if len(errors) != 0 :
			self.messages("Errors", errors, "Error")
		if len(warnings) != 0 :
			self.messages("Warnings", warnings, "Warning")
		if len(infos) != 0 :
			self.messages("Informational messages", infos, "Info")
