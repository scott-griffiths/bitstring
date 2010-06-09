
Examples
========

Creation
--------

There are lots of ways of creating new bitstrings. The most flexible is via the ``auto`` parameter, which is used in this example. ::

 # Multiple parts can be joined with a single expression...
 s = BitString('0x000001b3, uint:12=352, uint:12=288, 0x1, 0x3') 
 
 # and extended just as easily
 s += 'uint:18=48000, 0b1, uint:10=4000, 0b100'
 
 # To covert to an ordinary string use the bytes property
 open('video.m2v', 'wb').write(s.bytes)
 
 # The information can be read back with a similar syntax
 start_code, width, height = s.readlist('hex:32, uint:12, uint:12')
 aspect_ratio, frame_rate = s.readlist('bin:4, bin:4')

Manipulation
------------

::

 s = BitString('0x0123456789abcdef')
 
 del s[4:8]                      # deletes the '1'
 s.insert('0xcc', 12)            # inserts 'cc' between the '3' and '4'
 s.overwrite('0b01', 30)         # changes the '6' to a '5'
 
 # This replaces every '1' bit with a 5 byte Ascii string!
 s.replace('0b1', BitString(bytes='hello'))
 
 del s[-1001:]                   # deletes final 1001 bits
 s.reverse()                     # reverses whole BitString
 s.prepend('uint:12=44')         # prepend a 12 bit integer

Parsing
-------

This example creates a class that parses a structure that is part of the H.264 video standard. ::

 class seq_parameter_set_data(object):
     def __init__(self, s):
         """Interpret next bits in BitString s as an SPS."""
         # Read and interpret bits in a single expression:
         self.profile_idc = s.read('uint:8')
         # Multiple reads in one go returns a list:
         self.constraint_flags = s.readlist('uint:1, uint:1, uint:1, uint:1')
         self.reserved_zero_4bits = s.read('bin:4')
         self.level_idc = s.read('uint:8')
         self.seq_parameter_set_id = s.read('ue')
         if self.profile_idc in [100, 110, 122, 244, 44, 83, 86]:
             self.chroma_format_idc = s.read('ue')
             if self.chroma_format_idc == 3:
                 self.separate_colour_plane_flag == s.read('uint:1')
             self.bit_depth_luma_minus8 = s.read('ue')
             self.bit_depth_chroma_minus8 = s.read('ue')
             # etc.

::
 
 >>> s = BitString('0x6410281bc0')
 >>> sps = seq_parameter_set_data(s)
 >>> print(sps.profile_idc)
 100
 >>> print(sps.level_idc)
 40
 >>> print(sps.reserved_zero_4bits)
 0b0000
 >>> print(sps.constraint_flags)
 [0, 0, 0, 1]
 
Sieve of Eratosthenes
---------------------

This classic (though inefficient) method of calculating prime numbers uses a bitstring to store whether each bit position represents a prime number. This takes much less memory than an ordinary array. ::

 
 def prime_sieve(top=1000000):
     b = BitString(top) # bitstring of '0' bits
     for i in xrange(2, top):
         if not b[i]:
             yield i
             # i is prime, so set all its multiples to '1'.
             b.set(True, xrange(i*i, top, i))
                 




