#!/usr/bin/env python
from distutils.core import setup

setup(name='bitstring',
      version='0.4.1',
      description='Simple construction, analysis and modification of binary data.',
      author='Scott Griffiths',
      author_email='scott@griffiths.name',
      url='http://python-bitstring.googlecode.com',
      download_url='http://python-bitstring.googlecode.com',
      license='The MIT License: http://www.opensource.org/licenses/mit-license.php',
      py_modules=['bitstring'],
      long_description="""A pure Python module for analysing, constructing and modifying binary data.
                          The underlying binary data can be interpreted as, or constructed from,
                          hexadecimal, octal or binary strings, signed or unsigned integers,
                          and signed or unsigned exponential-Golomb coded integers. It can
                          also be used as and created from plain Python strings.""",
      platforms='all',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.0',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ]
      )

