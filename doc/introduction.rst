.. currentmodule:: bitstring

************
Introduction
************

While it is not difficult to manipulate binary data in Python, for example using the :mod:`struct` and :mod:`array` modules, it can be quite fiddly and time consuming even for quite small tasks, especially if you are not dealing only with whole-byte data.

The bitstring module provides four classes, :class:`BitStream`, :class:`BitArray`, :class:`ConstBitStream` and :class:`Bits`, instances of which can be constructed from integers, floats, hex, octal, binary, strings or files, but they all just represent a string of binary digits. I shall use the general term 'bitstring' when referring generically to any of the classes, and use the class names for parts that apply to only one or another.

:class:`BitArray` objects can be sliced, joined, reversed, inserted into, overwritten, packed, unpacked etc. with simple functions or slice notation. :class:`BitStream` objects can also be read from, searched in, and navigated in, similar to a file or stream. 

Bitstrings are designed to be as lightweight as possible and can be considered to be just a list of binary digits. They are however stored efficiently - although there are a variety of ways of creating and viewing the binary data, the bitstring itself just stores the byte data, and all views are calculated as needed, and are not stored as part of the object.

The different views or interpretations on the data are accessed through properties such as :attr:`~Bits.hex`, :attr:`~Bits.bin` and :attr:`~Bits.int`, and an extensive set of functions is supplied for modifying, navigating and analysing the binary data.

A complete reference for the module is given in the :ref:`reference` section, while the rest of this manual acts more like a tutorial or guided tour. Below are just a few examples to whet your appetite; everything here will be covered in greater detail in the rest of this manual. ::

    from bitstring import BitArray

Just some of the ways to create bitstrings::

    # from a binary string
    a = BitArray('0b001')
    # from a hexadecimal string
    b = BitArray('0xff470001')
    # straight from a file
    c = BitArray(filename='somefile.ext')
    # from an integer
    d = BitArray(int=540, length=11)
    # using a format string
    d = BitArray('int:11=540')
 
Easily construct new bitstrings::

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
    '9249cdcd'
    >>> print(e.int)
    -1840656947
    >>> print(e.uint)
    2454310349


Getting Started
---------------

The easiest way to install :mod:`bitstring` is to use ``pip`` via::

   pip install bitstring
 
or similar.

If you want an earlier version, or need other files in the full package, you can download it from the project's website.

If you then extract the contents of the zip file you should find files organised in these directories

* ``bitstring/`` : The bitstring module files.
* ``test/`` : Unit tests for the module, plus some example files for testing purposes.
* ``doc/`` : This manual as a PDF and as HTML.

If you downloaded the source and want to install, run::

    python setup.py install

You might need to add a 'sudo' to the start of that command, depending on your system. This will copy the source files to your Python installation's ``site-packages`` directory.

The module comes with comprehensive unit tests. To run them yourself use your favourite unit test running method, mine is::
 
    python -m unittest discover

which when run in the `test` folder should run all the tests (almost 500) and say OK. If tests fail then either your version of Python isn't supported (you need Python 2.7 or 3.x) or something unexpected has happened - in which case please tell me about it.

