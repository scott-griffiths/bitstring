
Optimisation Techniques
=======================

The :mod:`bistring` module aims to be as fast as reasonably possible, and although there is more work to be done optimising some operations it is currently quite well optimised without resorting to C extensions.

There are however some pointers you should follow to make your code efficient, so if you need things to run faster then this is the section for you.

Use combined read and interpretation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When parsing a bitstring one way to write code is in the following style::

 width = s.readbits(12).uint
 height = s.readbits(12).uint
 flags = s.readbits(4).bin
 
This works fine, but is not very quick. The problem is that the call to :meth:`Bits.readbits` constructs and returns a new bitstring, which then has to be interpreted. The new bitstring isn't used for anything else and so creating it is wasted effort. Instead of using :meth:`Bits.readbits` (or similar methods) it is better to use a single method that does the read and interpretation together::

 width = s.read('uint:12')
 height = s.read('uint:12')
 flags = s.read('bin:4')
 
This is much faster, although not as fast as the combined call::

 width, height, flags = s.readlist('uint:12, uint:12, bin:4')
 
Choose between Bits and BitString
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you don't need to modify your bitstring after creation then prefer the immutable :class:`Bits` over the mutable :class:`BitString`. This is typically the case when parsing, or when creating directly from files.

As of version 1.2.0 the speed difference between the classes is marginal, but the speed of :class:`Bits` is expected to improve. There are also memory usage optimisations that can be made if objects are known to be immutable so there should be improvements in this area too.

One anti-pattern to watch out for is using ``+=`` on a :class:`Bits` object. For example, don't do this::

 s = Bits()
 for i in range(1000):
     s += '0xab'
    
Now this is inefficient for a few reasons, but the one I'm highlighting is that as the immutable bitstring doesn't have an ``__iadd__`` special method the ordinary ``__add__`` gets used instead. In other words ``s += '0xab'`` gets converted to ``s = s + '0xab'``, which creates a new :class:`Bits` from the old on every iteration. This isn't what you'd want or possibly expect. If ``s`` had been a :class:`BitString` then the addition would have been done in-place, and have been much more efficient.


Use dedicated functions for bit setting and checking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to set or check individual bits then there are special functions for this. For example one way to set bits would be::

 s = BitString(1000)
 for p in [14, 34, 501]:
     s[p] = '0b1'
     
This creates a 1000 bit bitstring and sets three of the bits to '1'. Unfortunately the crucial line spends most of its time creating a new bitstring from the '0b1' string. It is much faster (and I mean at least an order of magnitude) to use the :meth:`BitString.set` method::

 s = BitString(1000)
 s.set([14, 34, 501])
 
As well as :meth:`BitString.set`, :meth:`BitString.unset` and :meth:`BitString.invert` there are also checking methods :meth:`Bits.allset` and :meth:`Bits.allunset`. So rather than using ::

 if s[100] == '0b1' and s[200] == '0b1':
     do_something()
     
it's much better to say ::

 if s.allset((100, 200)):
     do_something()
     

 
