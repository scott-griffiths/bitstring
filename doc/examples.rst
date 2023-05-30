.. currentmodule:: bitstring

Examples
========

Creation
--------

There are lots of ways of creating new bitstrings. The most flexible is via the ``auto`` parameter, which is used in this example. ::

    # Multiple parts can be joined with a single expression...
    s = BitArray('0x000001b3, uint12=352, uint12=288, 0x1, 0x3')
 
    # and extended just as easily
    s += 'uint18=48000, 0b1, uint10=4000, 0b100'
 
    # To covert to an ordinary string use the bytes property
    open('video.m2v', 'wb').write(s.bytes)
 
    # The information can be read back with a similar syntax
    start_code, width, height = s.readlist('hex32, uint12, uint12')
    aspect_ratio, frame_rate = s.readlist('2*bin4')





Manipulation
------------

::

    s = BitArray('0x0123456789abcdef')
 
    del s[4:8]                      # deletes the '1'
    s.insert('0xcc', 12)            # inserts 'cc' between the '3' and '4'
    s.overwrite('0b01', 30)         # changes the '6' to a '5'
 
    # This replaces every '1' bit with a 5 byte Ascii string!
    s.replace('0b1', BitArray(bytes='hello'))
 
    del s[-1001:]                   # deletes final 1001 bits
    s.reverse()                     # reverses whole BitString
    s.prepend('uint12=44')         # prepend a 12 bit integer


Parsing
-------

This example creates a class that parses a structure that is part of the H.264 video standard. ::

 class seq_parameter_set_data(object):
     def __init__(self, s):
         """Interpret next bits in BitString s as an SPS."""
         # Read and interpret bits in a single expression:
         self.profile_idc = s.read('uint8')
         # Multiple reads in one go returns a list:
         self.constraint_flags = s.readlist('4*bool')
         self.reserved_zero_4bits = s.read('bin4')
         self.level_idc = s.read('uint8')
         self.seq_parameter_set_id = s.read('ue')
         if self.profile_idc in [100, 110, 122, 244, 44, 83, 86]:
             self.chroma_format_idc = s.read('ue')
             if self.chroma_format_idc == 3:
                 self.separate_colour_plane_flag = s.read('bool')
             self.bit_depth_luma_minus8 = s.read('ue')
             self.bit_depth_chroma_minus8 = s.read('ue')
             # etc.

::
 
    >>> s = BitStream('0x6410281bc0')
    >>> sps = seq_parameter_set_data(s)
    >>> print(sps.profile_idc)
    100
    >>> print(sps.level_idc)
    40
    >>> print(sps.reserved_zero_4bits)
    0b0000
    >>> print(sps.constraint_flags)
    [0, 0, 0, 1]
 

