#!/usr/bin/env python
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import sys

kwds = {'long_description': open('README.txt').read()}

if sys.version_info[:2] < (2, 6):
    raise Exception('This version of bitstring needs Python 2.6 or later. '
                    'For Python 2.4 / 2.5 please use bitstring version 1.0 instead.')

no_assert = [('PYREX_WITHOUT_ASSERTIONS', None)]
ext_modules = [Extension('bitstring.cbitstore', ["bitstring/cbitstore.pyx"], define_macros=no_assert),
               Extension('bitstring.cbits', ["bitstring/cbits.pyx"], define_macros=no_assert),
               Extension('bitstring.bitarray', ["bitstring/bitarray.pyx"], define_macros=no_assert),
               Extension('bitstring.bitstream', ["bitstring/bitstream.pyx"], define_macros=no_assert),
               Extension('bitstring.constbitstream', ["bitstring/constbitstream.pyx"], define_macros=no_assert)]

setup(name='bitstring',
      version='2.2.0',
      description='Simple construction, analysis and modification of binary data.',
      author='Scott Griffiths',
      author_email='scott@griffiths.name',
      url='http://python-bitstring.googlecode.com',
      download_url='http://python-bitstring.googlecode.com',
      license='The MIT License: http://www.opensource.org/licenses/mit-license.php',
      cmdclass = {'build_ext': build_ext},
      ext_modules = ext_modules,
      packages=['bitstring'],
      platforms='all',
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      **kwds
      )

