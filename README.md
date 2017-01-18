# rdfa-md-service

Python modules to run the [“RDFa 1.1 Distiller”](https://www.w3.org/2012/pyRdfa/), [“RDFa 1.1 Validator”](https://www.w3.org/2012/pyRdfa/Validator.html), and [“Microdata to RDF”](https://www.w3.org/2012/pyMicrodata/) services at W3C.

All three services are based on the newest releases of [RDFLib](https://github.com/RDFLib/rdflib), that include the parsers for both RDFa and for Microdata. This module includes the scripts to 

* serve as a CGI entries on Apache
* check the error handling for each of these services
* collect the form data coming from the HTML pages, call out to the RDF parsing and return the serialized graph or (in the case of the RDFa Validator) generate a proper HTML response.

## Warning in January 2017

This module is in development for now. The current services rely on a different, and outdated architecture, whereby the CGI scripts called out to a full, and separate, RDFa (resp. Microdata) module that is *on top* of RDFLib. That was the right approach when the corresponding parsers had not yet been incorporated into RDFLib. It is now time to remove that separate layer; hopefully, this module will be finalized sometimes in 2017.
