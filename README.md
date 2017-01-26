# rdfa-md-service

Python modules to run the [“RDFa 1.1 Distiller”](https://www.w3.org/2012/pyRdfa/), [“RDFa 1.1 Validator”](https://www.w3.org/2012/pyRdfa/Validator.html), and [“Microdata to RDF”](https://www.w3.org/2012/pyMicrodata/) services at W3C.

## Repo content:

- `rdfa_md`: The relevant Python package covering both the RDFa and the Microdata branches. Put this module somewhere in $PYTHONPATH.
- `CGI-scripts`: Python scripts that can be used as CGI entry points on a web site. These scripts are minimal; after a rudimentary checking on the incoming URI-s they dive into the functionalities in `rdf_md`.

## External dependencies

The module has the following dependencies (beyond the standard Python modules)

* [RDFlib](https://github.com/RDFLib/rdflib) which does all the heavy lifting for parsing. Use the latest release, currently 4.2.\*.
* [RDFLib-JSONLD](https://github.com/RDFLib/rdflib-jsonld) to serialize the output into JSON-LD
* [html5lib](https://pypi.python.org/pypi/html5lib) to parse HTML

### Python3

The package has not yet been tested for Python3 although, manually, the code has been written in a Python3 way; the real issue is whether the dependencies are Python3 ready or not. (Current situation: unknown for rdflib-jsonld, should be o.k. for html5lib, and rdflib must be installed separately for Python3. The rdflib issue should be solved, ie, the same code should run on both Python2 and Python3 starting with version 5.)



## Status in January 2017

*This module is in development for now.* The current services rely on a different, and outdated architecture, whereby the CGI scripts called out to a full, and separate, RDFa (resp. Microdata) module that is *on top* of RDFLib. That was the right approach when the corresponding parsers had not yet been incorporated into RDFLib. It is now time to remove that separate layer; hopefully, this module will be finalized sometimes in 2017.
