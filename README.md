

![bitstring](https://github.com/scott-griffiths/bitstring/blob/d85c22504882d93b8c0cec373ef03b375e9ea7f8/doc/bitstring_logo_small.png?raw=true "bitstring")

**bitstring** is a pure Python module designed to help make
the creation and analysis of binary data as simple and natural as possible.

It has been maintained since 2006 and now has about [20 million downloads](https://pypistats.org/packages/bitstring) per year.

bitstring version 4.0 only supports Python 3.7 and later. Use
bitstring version 3.1 if you're using Python 2.7 or 3.6 or earlier.

Overview
--------

* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit level slicing, joining, searching, replacing and more.
* Read from and interpret bitstrings as streams of binary data.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Open source software, released under the MIT licence.


Documentation
-------------
The manual for the bitstring module is available at [Read the Docs](https://bitstring.readthedocs.org).
It contains a walk-through of all the features and a complete [reference section](https://bitstring.readthedocs.io/en/latest/quick_ref.html).


Simple Examples
---------------

### [Creation](https://bitstring.readthedocs.io/en/latest/creation.html)

     >>> a = BitArray(bin='00101')
     >>> b = Bits(a_file_object)
     >>> c = BitArray('0xff, 0b101, 0o65, uint:6=22')
     >>> d = pack('intle:16, hex=a, 0b1', 100, a='0x34f')
     >>> e = pack('<16h', *range(16))

### [Different interpretations, slicing and concatenation](https://bitstring.readthedocs.io/en/latest/interpretation.html)

     >>> a = BitArray('0x1af')
     >>> a.hex, a.bin, a.uint
     ('1af', '000110101111', 431)
     >>> a[10:3:-1].bin
     '1110101'
     >>> '0b100' + 3*a
     BitArray('0x835e35e35, 0b111')

### [Reading data sequentially](https://bitstring.readthedocs.io/en/latest/reading.html)

     >>> b = BitStream('0x160120f')
     >>> b.read(12).hex
     '160'
     >>> b.pos = 0
     >>> b.read('uint:12')
     352
     >>> b.readlist('uint:12, bin:3')
     [288, '111']

### [Searching, inserting and deleting](https://bitstring.readthedocs.io/en/latest/reading.html#finding-and-replacing)

     >>> c = BitArray('0b00010010010010001111')   # c.hex == '0x1248f'
     >>> c.find('0x48')
     (8,)
     >>> c.replace('0b001', '0xabc')
     >>> c.insert('0b0000', pos=3)
     >>> del c[12:16]

Unit Tests
----------

The 600+ unit tests should all pass. They can be run from the root of the project with

     python -m unittest


Credits
-------

Created by Scott Griffiths in 2006 to help with ad hoc parsing and creation of compressed video files.
Maintained and expanded ever since as it became unexpectedly popular. Thanks to all those who have contributed ideas
and code (and bug reports) over the years.


<sub>Copyright (c) 2006 Scott Griffiths</sub>