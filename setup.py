# -*- coding: utf-8 -*-
from distutils.core import setup
import rdfa_md

setup(
	name='rdfa_md',
	version=rdfa_md.__version__,
	packages=['rdfa_md'],
	scripts=['CGI_scripts/mData_cgi.py', 'CGI_scripts/Rdfa_cgi.py'],
	url='https://github.com/w3c/rdfa-md-service',
	download_url='https://github.com/w3c/rdfa-md-service/archive/master.zip',
	license='W3C © SOFTWARE NOTICE AND LICENSE <http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231>',
	maintainer=rdfa_md.__author__,
	maintainer_email=rdfa_md.__email__,
	author=rdfa_md.__author__,
	author_email=rdfa_md.__email__,
	description='Fron-end layer to set up an RDFa and Microdata distiller service on top of RDFLib',
	keywords='W3C EPUB3',
	platforms='any',
	requires=['RDFLib', 'rdflib-jsonld', 'html5lib'],
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'Intended Audience :: End Users/Desktop',
		'Intended Audience :: Information Technology',
		'License :: W3C Software Notice and License',
		'Programming Language :: Python :: 2.7'
		'Programming Language :: Python :: 2 :: Only',
		'Topic :: Documentation :: Sphinx',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
		'Topic :: Utilities'
	]
)
