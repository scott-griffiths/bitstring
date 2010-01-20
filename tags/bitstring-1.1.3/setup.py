#!/usr/bin/env python
from distutils.core import setup

#kwds = {}
#kwds['long_description'] = open('README.txt').read()

setup(name='bitstring',
      version='1.1.3',
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
      long_description="""\
================
bitstring module
================

**bitstring** is a pure Python module designed to help make
the creation and analysis of binary data as simple and natural as possible.

BitStrings can be constructed from integers (big and little endian), hex,
octal, binary, strings or files. They can be sliced, joined, reversed,
inserted into, overwritten, etc. with simple functions or slice notation.
They can also be read from, searched and replaced, and navigated in,
similar to a file or stream.

This version supports Python 2.6 and 3.x. For Python 2.4 and 2.5 you should
instead download version 1.0.

Documentation
-------------
The manual for the bitstring module is available as a PDF. It contains a
walk-through of all the features and a complete reference section. It can be
dowloaded or viewed on the project's homepage.

Simple Examples
---------------
Creation::

     >>> a = BitString(bin='00101')
     >>> b = BitString(a_file_object)
     >>> c = BitString('0xff, 0b101, 0o65, uint:6=22')
     >>> d = pack('intle:16, hex=a, 0b1', 100, a='0x34f')
     >>> e = pack('<16h', *range(16))

Different interpretations, slicing and concatenation::

     >>> a = BitString('0x1af')
     >>> a.hex, a.bin, a.uint
     ('0x1af', '0b000110101111', 431)
     >>> a[10:3:-1].bin
     '0b1110101'
     >>> 3*a + '0b100'
     BitString('0o0657056705674')

Reading data sequentially::

     >>> b = BitString('0x160120f')
     >>> b.readbits(12).hex
     '0x160'
     >>> b.pos = 0
     >>> b.read('uint:12')
     352
     >>> b.readlist('uint:12, bin:3')
     [288, '0b111']

Searching, inserting and deleting::

     >>> c = BitString('0b00010010010010001111')   # c.hex == '0x1248f'
     >>> c.find('0x48')
     True
     >>> c.replace('0b001', '0xabc')
     >>> c.insert('0b0000')
     >>> c.delete(4, 12)

Installation
------------
First try::

     easy_install bitstring
     
If you don't have easy_install then download the zip file and run the
``setup.py`` script with the 'install' argument::

     python setup.py install

This should put ``bitstring.py`` in your ``site-packages`` directory. You may
need to run this with root privileges on Unix-like systems.

Alternatively just copy the ``bitstring.py`` file to where you want it!

If you're using Windows then there is an installer available from the
downloads tab on the project's homepage.

Unit Tests
----------
To run the unit tests::

     python test_bitstring.py

The unit tests for version 1.1 should all pass for Python 2.6, 3.0 and 3.1.

----

The bitstring module has been released as open source under the MIT License.
Copyright (c) 2009 Scott Griffiths

For more information see the project's homepage on Google Code:
<http://python-bitstring.googlecode.com>
"""
      )
