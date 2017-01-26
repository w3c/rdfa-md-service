.. RDFa and Microdata Services documentation master file, created by
   sphinx-quickstart on Wed Jan 25 17:22:50 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

RDFa and Microdata Services's documentation
===========================================

This package collects the functionalities of three different services at W3C:

- the `“RDFa 1.1 Distiller and Parser” <https://www.w3.org/2012/pyRdfa/>`_
- the `“RDFa Validator” <https://www.w3.org/2012/pyRdfa/Validator.html>`_
- the `“Microdata to RDF Distiller” <https://www.w3.org/2012/pyMicrodata/>`_

All three services use a server side Python script, doing the work and returning the requested data. The Python scripts themselves rely on the RDFa and Microdata parsers, respectively, that are part of the standard `RDFLib <https://github.com/RDFLib/rdflib>`_` distribution. The scripts need, therefore, just a thin layer to get and interpret keyword arguments of an HTTP request, hand over the real work to RDFLib, and convert the result back through an HTTP Response. This package/repository collects this “thin layer” in one package. Furthermore, the repository includes (in the `CGI-scripts` folder) two python scripts that can be installed on a server to set up the service locally.

Dependencies
------------

The dependencies of the package are:

* `RDFlib <https://github.com/RDFLib/rdflib>`_ which does all the heavy lifting for parsing. Use the latest release, currently 4.2.\*.
* `RDFLib-JSONLD <https://github.com/RDFLib/rdflib-jsonld>`_ to serialize the output into JSON-LD
* `html5lib <https://pypi.python.org/pypi/html5lib>`_ to parse HTML

The package requires Python2.7. The package has not yet been tested for Python3 although, manually, the code has been written in a Python3 compatible way; the real issue is whether the dependencies are Python3 ready or not. (Current situation, in January 2017: unknown for rdflib-jsonld, should be o.k. for html5lib, and rdflib must be installed separately for Python3. The rdflib issue should be solved, i.e., the same code should run on both Python2 and Python3 starting with version 5. That version should become official by the end of 2017)

Additional scripts
------------------

The repository also includes two scripts that can be used as CGI entries for RDFa Distiller and Validator and for Microdata Distiller, respectively.

History
-------

These services exist since 2012 but, at that time, the structure and set up was different. The RDFa, respectively the Microdata parsers were separate packages *on top* of RDFLib, and the server side processing relied on that. In other words, installation and maintenance of the service required maintaining a rather large package that was maintained by one individual. However, around 2014, both parsers *have been incorporated into RDFLib* and are now part of the standard distribution. Maintaining the separate package has become obsolete, hence this new package that relies exclusively on the latest version of RDFLib.


Metadata
--------

* Version: |version|
* Document creation date: |today|
* Author: Ivan Herman
* Contact: ivan@w3.org
* Repository: <https://github.com/w3c/rdfa-md-service>
* License: Copyright(c) 2017 W3C® (MIT, ERCIM, Keio, Beihang), see `W3C Software and Document Notice and License <https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document>`_ for details.


2. Table of Contents
====================

.. toctree::
  :numbered:
  :maxdepth: 2

  init
  mdata
  rdfa
  validator
  validator_errors
  validator_html
  utils
  cleanhtml
  RDFa_cgi.rst
  mData_cgi

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
