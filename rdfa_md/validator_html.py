# -*- coding: utf-8 -*-
"""
RDFa 1.1 validator. HTML source template for the output

@summary: RDFa validator, html template
@organization: U{World Wide Web Consortium<http://www.w3.org>}
@author: U{Ivan Herman<a href="http://www.w3.org/People/Ivan/">}
@license: This software is available for use under the
U{W3C® SOFTWARE NOTICE AND LICENSE<href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231">}
@var html_page: the XHTML code as a template for the output
"""

html_page = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01+RDFa 1.1//EN" "http://www.w3.org/MarkUp/DTD/html401-rdfa11-1.dtd">
<html>
  <head>
	<title>RDFa 1.1 Validator (Test Version for pyRdfa 3.X)</title>
	<meta content="text/html; charset=UTF-8" http-equiv="Content-Type" />
	<link rel="icon" type="image/png" href="/2001/sw/favicon-sw.png" />
	<link rel="meta" type="application/rdf+xml" title="FOAF" href="http://www.ivan-herman.net/foaf.rdf" />
	<meta name="Author" content="Ivan Herman, Semantic Web Activity Lead, W3C" />
	<link rel="copyright" href="http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231" title="CC Copyrights" />
	<link rel="stylesheet" type="text/css" href="/StyleSheets/base.css"/>
	<link rel="stylesheet" type="text/css" href="/2001/sw/swstyle.css"/>
	<link rel="stylesheet" type="text/css" href="/2001/sw/swstyleExtras.css"/>
	<link rel="stylesheet" type="text/css" href="/2007/08/pyrdfa/style/pyrdfa.css"/>
   <style type="text/css">
        #Turtle {
            padding: 0.5em;
            border: thin inset;
            background-color: rgb(255, 255, 204);
        }
        div#Message p:first-child {
            font-weight: bold;
            font-size: 120%%;
            font-style: italic
        }
		div#Message {
			background-color: inherit
		}
        p.Error span:first-child { color: red}
        p.Warning span:first-child { color: blue}
        p.Info span:first-child { color: green}
		address { font-size:90%% }
        body {
            font-size : 100%%
        }
     </style>
  </head>
  <body prefix="doap: http://usefulinc.com/ns/doap#">
		<p class="banner"><a href="/2001/sw/" ><img src="/Icons/SW/sw-horz-w3c.png" width="241" height="48" alt="W3C SW Logo"/></a></p>
        <h1 id="title" class="title"><img src="/Icons/SW/Buttons/sw-rdfa-orange.png" alt="RDFa technology button"/>&nbsp;&nbsp;RDFa Validation results </h1>

      <h2>Validator messages</h2>

      <div id="Message">
      </div>

      <h2>Generated RDF content in Turtle format</h2>
      <div id="Turtle">
<pre id="output">
</pre>
        </div>

        <hr />
        <address>
		    <a href="http://www.w3.org/People/Ivan/">Ivan Herman</a> (<a href="mailto:ivan@w3.org">ivan@w3.org</a>)
			<br />
			%s
		</address>
  </body>
</html>
"""
