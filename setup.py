#!/usr/bin/env python
from distutils.core import setup
import sys

kwds = {}
kwds['long_description'] = open('README.txt').read()

if sys.version_info[:2] < (2, 6):
    raise Exception('This version of bitstring needs Python 2.6 or later. '
                    'For Python 2.4 / 2.5 please use bitstring version 1.0 instead.')

setup(name='bitstring',
      version='1.3.0',
      description='Simple construction, analysis and modification of binary data.',
      author='Scott Griffiths',
      author_email='scott@griffiths.name',
      url='http://python-bitstring.googlecode.com',
      download_url='http://python-bitstring.googlecode.com',
      license='The MIT License: http://www.opensource.org/licenses/mit-license.php',
      py_modules=['bitstring'],
      platforms='all',
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      **kwds
      )

