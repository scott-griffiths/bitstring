#!/usr/bin/env python
from distutils.core import setup

setup(name='bitstring',
      version='0.3.1',
      description='Simple construction, analysis and modification of binary data.',
      author='Scott Griffiths',
      author_email='scott@griffiths.name',
      url='http://python-bitstring.googlecode.com',
      download_url='http://python-bitstring.googlecode.com',
      license='The MIT License: http://www.opensource.org/licenses/mit-license.php',
      py_modules=['bitstring'],
      data_files=[('test', ['test/test.m1v', 'test/smalltestfile'])],
      long_description="""A pure Python module for analysing, constructing and modifying binary data.
                          The underlying binary data can be interpreted as, or constructed from,
                          hexadecimal, octal or binary strings, signed or unsigned integers,
                          and signed or unsigned Exponential Golomb coded integers. It can
                          also be used as and created from plain Python strings.""",
      platforms='all'
      )
