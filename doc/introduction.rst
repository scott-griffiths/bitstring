
************
Introduction
************

While it is not difficult to manipulate binary data in Python, for example using the ``struct`` and ``array`` modules, it can be quite fiddly and time consuming even for quite small tasks, especially if you are not dealing only with whole-byte data.

The bitstring module provides two classes, ``BitString`` and ``Bits``, instances of which can be constructed from integers, floats, hex, octal, binary, strings or files, but they all just represent a string of binary digits. The ``Bits`` class differs from ``BitString`` in that it is immutable and so does not support methods that would modify it after creation. I shall use the general term 'bitstring' when referring to either the ``Bits`` or ``BitString`` class, and use the class names for parts that apply to only one or the other.

``BitString`` objects can be sliced, joined, reversed, inserted into, overwritten, packed, unpacked etc. with simple functions or slice notation. They can also be read from, searched in, and navigated in, similar to a file or stream. 

Bitstrings are designed to be as lightweight as possible and can be considered to be just a list of binary digits. They are however stored efficiently - although there are a variety of ways of creating and viewing the binary data, the bitstring itself just stores the byte data, and all views are calculated as needed, and are not stored as part of the object.

The different views or interpretations on the data are accessed through properties such as ``hex``, ``bin`` and ``int``, and an extensive set of functions is supplied for modifying, navigating and analysing the binary data.

A complete reference for the module is given in Appendix A, while the rest of this manual acts more like a tutorial or guided tour. Below are just a few examples to whet your appetite; everything here will be covered in greater detail in the rest of this manual. ::

 from bitstring import BitString

Just some of the ways to create BitStrings::

 # from a binary string
 a = BitString('0b001')
 # from a hexadecimal string
 b = BitString('0xff470001')
 # straight from a file
 c = BitString(filename='somefile.ext')
 # from an integer
 d = BitString(int=540, length=11)
 # using a format string
 d = BitString('int:11=540')
 
Easily construct new BitStrings::

 # 5 copies of 'a' followed by two new bytes
 e = 5*a + '0xcdcd' 
 # put a single bit on the front
 e.prepend('0b1')                           
 # take a slice of the first 7 bits
 f = e[7:]                                  
 # replace 3 bits with 9 bits from octal string
 f[1:4] = '0o775'                           
 # find and replace 2 bit string with 16 bit string
 f.replace('0b01', '0xee34')                

Interpret the bitstring however you want::

 >>> print(e.hex)
 '0x9249cdcd'
 >>> print(e.int)
 -1840656947
 >>> print(e.uint)
 2454310349


Getting Started
---------------

The easiest way to install ``bitstring`` is to use ``easy_install`` via::

 sudo easy_install bitstring
 
or similar.

If you want an earlier version, or need other files in the full package you can download and extract the contents of the .zip provided on the project's website.

First download the latest release for either Python 2.4 / 2.5 or Python 2.6 / 3.0 / 3.1 (see the Downloads tab on the project’s homepage). Note that this manual covers only the Python 2.6 and later version. An earlier version is available for Python 2.4 / 2.5, which is available on the project's homepage.

If you then extract the contents of the zip file you should find:

* ``bitstring.py`` : The bitstring module itself.
* ``test_bitstring.py`` : Unit tests for the module.
* ``setup.py`` : The setup script.
* ``readme.txt`` : A short readme.
* ``release_notes.txt`` : History of changes in this and previous versions.
* ``test/test.m1v`` : An example file (MPEG-1 video) for testing purposes.
* ``test/smalltestfile`` : Another small file for testing.
* ``bitstring_manual.pdf`` : This document.

To install, run::

 python setup.py install

This will copy ``bitstring.py`` to your Python installation's ``site-packages`` directory. If you prefer you can do this by hand, or just make sure that your Python program can see ``bitstring.py``, for example by putting in the same directory as the program that will use it.

The module comes with comprehensive unit tests. To run them yourself use::
 
 python test_bitstring.py

which should run all the tests (over 300) and say OK. If tests fail then either your version of Python isn't supported (there's one version of bitstring for Python 2.4 and 2.5 and a separate version for Python 2.6, 3.0 and 3.1) or something unexpected has happened - in which case please tell me about it.
