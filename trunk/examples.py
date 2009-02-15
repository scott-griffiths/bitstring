#!/usr/bin/env python
# Some simple examples of bitstring usage.
#
# see http://python-bitstring.googlecode.com
license = """
The MIT License

Copyright (c) 2006-2008 Scott Griffiths

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from bitstring import *

## Creating bitstrings

# From a hexadecimal string. The leading '0x' is optional if you use 'hex='
h = BitString(hex='0x000001b3')

# From a binary string. The leading '0b' is also optional.
b = BitString(bin='0b0010011')

# Alternatively, use the 'auto' initialiser, which is the first parameter in the
# __init__ function. This will recognise strings starting with '0x' and '0b'.
h = BitString('0x000001b3')
b = BitString('0b0010011')

# With integers the length of the bitstring in bits needs to be supplied.
# It must be long enough to contain the integer.
ui = BitString(uint=15, length=6)

# From an integer represented as a signed exponential Golomb code.
e = BitString(se=-10)

# From an ordinary string
s1 = BitString(data='\xff\x00\x00\x01')
s2 = BitString(data=open('test/test.m1v', 'rb').read())

# From a file
f = BitString(filename='test/test.m1v')

## Interpreting bitstrings

# The BitString properties such as bin, hex and int offer a view on the data.
print h.hex    # 0x000001b3
print h.bin    # 0b00000000000000000000000110110011
print ui.uint  # 15
print ui.bin   # 0b001111 (note the leading zeros because we gave it a length of 6)
print e.se     # -10
print e.bin    # 0b000010101
print f[0:80].hex    # 0x000001b31601208302d0 (slice gives first 80 bits only)

## Manipulating bitstrings

# Slicing
print h[24:32].hex  # 0xb3

# Joining lists
bsl = [BitString(bin=b) for b in ['0', '1', '000', '111']]
print join(bsl).bin   # 0b01000111

# Using a bitstring as a source for other bitstrings
s = BitString(hex='0x00112233445566778899aabbccddeeff')
print s.readbit().bin     # 0b0
s.advancebits(7)          # Move on 7 bits to byte align.
print s.readbytes(3).hex  # 0x112233

# Use offsets to ignore some bits at the start
s = BitString(hex='0xf1223f', offset=4, length=16)
print s.hex               # '0x1223'

# find() and findbytealigned() search for one BitString in another
t = BitString(hex='0x23')
s.findbytealigned(t)
print s.bytepos, s.readbyte().hex    # 1, '0x23'
