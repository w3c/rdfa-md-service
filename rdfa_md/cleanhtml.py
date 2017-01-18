#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cleanhtml - Wrapper functions to prevent XSS in HTML output"""
# <http://dev.w3.org/2004/PythonLib-IH/cleanhtml.py>
#
# Copyright © 2013 World Wide Web Consortium, (Massachusetts Institute
# of Technology, European Research Consortium for Informatics and
# Mathematics, Keio University, Beihang). All Rights Reserved. This
# work is distributed under the W3C® Software License [1] in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.
#
# [1] http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
#
# Written October 2013 by Brett Smith <brett@w3.org>
#
# Disclaimer:
# These functions were designed to make them as easy as possible to use
# with the current style of CGI scripts.  If you're writing a new CGI from
# scratch, please consider using a more robust system for HTML output
# than Python's string interpolation.

from __future__ import print_function

__all__ = ['clean_str', 'clean_strs', 'multi_format', 'clean_format',
           'multi_print', 'clean_print']

from cgi import escape
from itertools import chain

def clean_str(s):
    """Make s a string and escape all important entities."""
    try:
        return escape(s, quote=True)
    except AttributeError:  # not a string type
        return escape(str(s), quote=True)

def clean_strs(*args):
    """Iterate over each argument run through clean_str."""
    return (clean_str(x) for x in args)

def multi_format(s, *params):
    """Format a string with many iterators.

    Pass in a format string and any number of iterators.  The iterators
    will be chained together in sequence to make format arguments."""
    return s % tuple(chain(*params))

def clean_format(s, *args):
    """Interpolate a string after passing arguments through cgi.escape.

    Pass in a format string and any number of arguments.  The extra arguments
    will be run through clean_strs and then used to format the string."""
    return multi_format(s, clean_strs(*args))

def multi_print(s, *params):
    """Print a string formatted with many iterators.

    This is a convenience function that prints multi_format(s, *params)."""
    print(multi_format(s, *params))

def clean_print(s, *args):
    """Print a string after passing arguments through cgi.escape.

    This is a convenience function that prints clean_format(s, *args)."""
    print(clean_format(s, *args))

if __name__ == '__main__':
    test_input = [42, '<foo>', '<a b="c&d">']
    test_results = ['42', '&lt;foo&gt;', '&lt;a b=&quot;c&amp;d&quot;&gt;']
    for expect, actual in zip(test_results, clean_strs(*test_input)):
        assert (actual == expect), "got %r instead of %r" % (actual, expect)

    format_s = '%s %r %s'
    assert (multi_format(format_s, test_input) ==
            "42 '<foo>' <a b=\"c&d\">"), "multi_format test failed"
    assert (clean_format(format_s, *test_input) ==
            "42 '&lt;foo&gt;' &lt;a b=&quot;c&amp;d&quot;&gt;"), \
            "clean_format test failed"

    clean_print("%s %s.", "Tests", "passed")
