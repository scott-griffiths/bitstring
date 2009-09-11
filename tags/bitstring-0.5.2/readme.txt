================
bitstring module
================

**bitstring** is a pure Python module designed to help make
the creation and analysis of binary data as painless as possible.

BitString objects can be constructed from integers, hexadecimal,
octal, binary, strings or files. They can be sliced, joined,
reversed, inserted into, overwritten, etc. with simple functions
or slice notation. They can also be read from, searched, and
navigated in, similar to a file or stream.


Installation
------------
To install run the ``setup.py`` script with the 'install' argument::

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

The unit tests should all pass for Python 2.4, 2.5 and 2.6.

---

The bitstring module has been released as open source under the MIT License.
Copyright (c) 2009 Scott Griffiths

For more information see the project's homepage on Google Code:
<http://python-bitstring.googlecode.com>
