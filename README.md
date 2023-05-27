

![bitstring](https://raw.githubusercontent.com/scott-griffiths/bitstring/main/doc/bitstring_logo_small.png "bitstring")

**bitstring** is a pure Python module designed to help make
the creation and analysis of binary data as simple and natural as possible.

It has been maintained since 2006 and now has many millions of downloads per year.


You can try out the interactive walkthrough notebook on [binder](https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb), or take a look at the [static version](https://github.com/scott-griffiths/bitstring/blob/main/doc/walkthrough.ipynb).


[![CI badge](https://github.com/scott-griffiths/bitstring/actions/workflows/.github/workflows/ci.yml/badge.svg)](https://github.com/scott-griffiths/bitstring/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/readthedocs/bitstring)](https://bitstring.readthedocs.io/en/latest/)
[![Downloads](https://img.shields.io/pypi/dm/bitstring?color=blue)](https://pypistats.org/packages/bitstring) &nbsp; &nbsp; 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb)

# \<<< 4.1 beta now available - the _speed_ update \>>>

This version concentrats on what is perhaps bitstring's major weakness - speed.
It's always been a pure Python module with no dependencies, which has a few advantages, but means it can't compete with C-coded extensions in terms of raw speed of operation.

Version 4.1 of bitstring has been rewritten to use the `bitarray` type from the package of the same name as its underlying data type.
This lets us keep the API and functionality of bitstring but gains (most of) the speed of bitarray.

The 4.1 beta should be fully functional - there are no known issues.
To install the beta you need to specify the precise version:

    python -m pip install bitstring==4.1.0b1

Please try it out and report any problems or observations.
You shouldn't need to change any code - everything should just work the same as version 4.0, just faster.

Overview
--------

* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit-level slicing, joining, searching, replacing and more.
* Read from and interpret bitstrings as streams of binary data.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Open source software, released under the MIT licence.


> **Note** \
> Version 4 of bitstring only supports Python 3.7 and later. \
> Use bitstring version 3.1 if you're using Python 2.7 or 3.6 or earlier.


Documentation
-------------
The manual for the bitstring module is available at [Read the Docs](https://bitstring.readthedocs.org).
It contains a walk-through of all the features and a complete [reference section](https://bitstring.readthedocs.io/en/stable/quick_ref.html).


Examples
--------

### Installation

    $ pip install bitstring

### [Creation](https://bitstring.readthedocs.io/en/stable/creation.html)

     >>> from bitstring import Bits, BitArray, BitStream, pack
     >>> a = BitArray(bin='00101')
     >>> b = Bits(a_file_object)
     >>> c = BitArray('0xff, 0b101, 0o65, uint6=22')
     >>> d = pack('intle16, hex=a, 0b1', 100, a='0x34f')
     >>> e = pack('<16h', *range(16))

### [Different interpretations, slicing and concatenation](https://bitstring.readthedocs.io/en/stable/interpretation.html)

     >>> a = BitArray('0x3348')
     >>> a.hex, a.bin, a.uint, a.float, a.bytes
     ('3348', '0011001101001000', 13128, 0.2275390625, b'3H')
     >>> a[10:3:-1].bin
     '0101100'
     >>> '0b100' + 3*a
     BitArray('0x866906690669, 0b000')

### [Reading data sequentially](https://bitstring.readthedocs.io/en/stable/reading.html)

     >>> b = BitStream('0x160120f')
     >>> b.read(12).hex
     '160'
     >>> b.pos = 0
     >>> b.read('uint12')
     352
     >>> b.readlist('uint12, bin3')
     [288, '111']

### [Searching, inserting and deleting](https://bitstring.readthedocs.io/en/stable/reading.html#finding-and-replacing)

     >>> c = BitArray('0b00010010010010001111')   # c.hex == '0x1248f'
     >>> c.find('0x48')
     (8,)
     >>> c.replace('0b001', '0xabc')
     >>> c.insert('0b0000', pos=3)
     >>> del c[12:16]


New in version 4.0
------------------

* New Python 3.7 minimum requirement. The code has been updated with type hints and legacy code removed.
* Shorter and more versative properties are available.

      >>> a = BitArray('u8=20')
      >>> a += '0b0011, f16=5.52'
      >>> a[12:].f16
      5.51953125

* A useful new pretty printing method. Gives a formatted view of a singe or two interpretations of the
  binary data.

      >>> a = Bits(bytes=b'hello world!!')
      >>> a.pp('bin, hex', width=40)
        0: 01101000 01100101   68 65
       16: 01101100 01101100   6c 6c
       32: 01101111 00100000   6f 20
       48: 01110111 01101111   77 6f
       64: 01110010 01101100   72 6c
       80: 01100100 00100001   64 21
       96: 00100001            21   

* LSB0 option (beta). This indexes the bits with the least significant bit being bit zero. This is the
  opposite way to the standard Python containers but is usual in some relevant fields.
      
      >>> bitstring.lsb0 = True
      >>> s = BitArray('0b00000')
      >>> s[0] = 1
      >>> s.bin
      '00001'

  This feature is still considered a beta as there may be issues with edge cases, especially around the
  interaction with the 'stream' features of the `BitStream` and `ConstBitStream` classes. For most usage
  cases it should be solid though, so please report any bugs in the issue tracker.
      
* Command line usage. Useful for quick interpretations of binary data.

        $ python -m bitstring int:16=-400
        0xfe70

* Support for 16 bit floating point types (both IEEE and bfloat).


Unit Tests
----------

The 600+ unit tests should all pass. They can be run from the root of the project with

     python -m unittest


Credits
-------

Created by Scott Griffiths in 2006 to help with ad hoc parsing and creation of compressed video files.
Maintained and expanded ever since as it became unexpectedly popular. Thanks to all those who have contributed ideas
and code (and bug reports) over the years.


<sub>Copyright (c) 2006 - 2023 Scott Griffiths</sub>
