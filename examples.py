#!/usr/bin/env python

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

# From hexadecimal string. The leading '0x' is optional.
h = BitString(hex='0x000001b3')

# From a binary string.
b = BitString(bin='0010011')

# With integers the length of the bitstring in bits needs to be supplied.
# It must be long enough to contain the integer.
ui = BitString(uint=15, length=6)

# From an integer represented as a signed exponential goulomb code.
e = BitString(se=-10)

## Interpreting bitstrings

# The BitString properties such as bin, hex and int offer a view on the data.
print(h.hex)   # 0x000001b3
print(h.bin)   # 00000000000000000000000110110011
print(ui.uint) # 15
print(ui.bin)  # 001111 (note the leading zeros because we gave it a length of 6)
print(e.se)    # -10
print(e.bin)   # 000010101

## Manipulating bitstrings

# Slicing
print(h[24:32].hex) # 0xb3

# Joining lists
bsl = [BitString(bin=b) for b in ['0', '1', '000', '111']]
print(join(bsl).bin)  # 01000111

# Using a bitstring as a source for other bitstrings
s = BitString(hex='0x00112233445566778899aabbccddeeff')
print(s.readbit().bin) # 0
s.advancebits(7)       # Move on 7 bits to byte align.
print(s.readbytes(3).hex) # 0x112233


s = BitString(hex='0x112233', offset = 4)
t = BitString(hex='0x23')
s.findbytealigned(t)
