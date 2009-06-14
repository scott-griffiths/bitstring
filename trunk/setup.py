#!/usr/bin/env python
from distutils.core import setup

setup(name='bitstring',
      version='0.4.3',
      description='Simple construction, analysis and modification of binary data.',
      author='Scott Griffiths',
      author_email='scott@griffiths.name',
      url='http://python-bitstring.googlecode.com',
      download_url='http://python-bitstring.googlecode.com',
      license='The MIT License: http://www.opensource.org/licenses/mit-license.php',
      py_modules=['bitstring'],
      long_description="""bitstring is a pure Python module designed to help make the creation and analysis of binary data as painless as possible. BitString objects can be constructed from integers, hexadecimal, octal, binary, strings or files. They can be sliced, joined, reversed, inserted into, overwritten, etc. with simple functions or slice notation. They can also be read from, searched, and navigated in, similar to a file or stream.""",
      platforms='all',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ]
      )

