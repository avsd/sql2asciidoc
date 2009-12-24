#!/usr/bin/env python
"""
Installation script for installing sql2asciidoc
library for Oracle and AsciiDoc.

Copyright 2009 David Avsajanishvili
avsd05@gmail.com

The software is released under Modified BSD license
"""

from distutils.core import setup

setup(name='sql2asciidoc',
      version='0.1.1',
      description='Tools for SQL DDL (table creation) and DML (SELECT commands output) to AsciiDoc source',
      author='David Avsajanishvili',
      author_email='avsd05@gmail.com',
      url='',
      packages=['sql2asciidoc'],
      scripts=['scripts/ddl2asciidoc', 'scripts/sql2asciidoc'],
      license='BSD')
