.. currentmodule:: bitstring

Optimisation Techniques
=======================

The :mod:`bitstring` module aims to be as fast as reasonably possible, and since version 4.1 has used the ``bitarray`` C extension to power its core.

There are however some pointers you should follow to make your code efficient, so if you need things to run faster then this is the section for you.

Use combined read and interpretation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When parsing a bitstring one way to write code is in the following style::

    width = s.read(12).uint
    height = s.read(12).uint
    flags = s.read(4).bin
 
This works fine, but is not very quick. The problem is that the call to :meth:`~ConstBitStream.read` constructs and returns a new bitstring, which then has to be interpreted. The new bitstring isn't used for anything else and so creating it is wasted effort. Instead it is better to use a string parameter that does the read and interpretation together::

    width = s.read('uint12')
    height = s.read('uint12')
    flags = s.read('bin4')
 
This is much faster, although probably not as fast as the combined call::

    width, height, flags = s.readlist('uint12, uint12, bin4')
 
Choose the simplest class you can
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you don't need to modify your bitstring after creation then prefer the immutable :class:`Bits` over the mutable :class:`BitArray`. This is typically the case when parsing, or when creating directly from files.

The speed difference between the classes is noticeable, and there are also memory usage optimisations that are made if objects are known to be immutable.

You should also prefer :class:`ConstBitStream` to :class:`BitStream` if you won't need to modify any bits.

One anti-pattern to watch out for is using ``+=`` on a :class:`Bits` object. For example, don't do this::

 s = Bits()
 for i in range(1000):
     s += '0xab'
    
Now this is inefficient for a few reasons, but the one I'm highlighting is that as the immutable bitstring doesn't have an ``__iadd__`` special method the ordinary ``__add__`` gets used instead.
In other words ``s += '0xab'`` gets converted to ``s = s + '0xab'``, which creates a new :class:`Bits` from the old on every iteration. This isn't what you'd want or possibly expect. If ``s`` had been a :class:`BitArray` then the addition would have been done in-place, and have been much more efficient.

Another problem is that the string ``0xab`` needs to be converted to a bitstring on every iteration.
There are cacheing mechanisms that will make this faster after the first time, but if there is a constant conversion happening in a loop like this it is better to hoist it out of the loop by declaring ``ab = Bits('0xab')`` first and then adding this object instead of the string.


Use dedicated functions for bit setting and checking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to set or check individual bits then there are special functions for this. For example one way to set bits would be::

 s = BitArray(1000)
 for p in [14, 34, 501]:
     s[p] = '0b1'
     
This creates a 1000 bit bitstring and sets three of the bits to '1'. Unfortunately the crucial line spends most of its time creating a new bitstring from the '0b1' string. You could make it slightly quicker by using ``s[p] = True``, but it is much faster (and I mean at least an order of magnitude) to use the :meth:`~BitArray.set` method::

 s = BitArray(1000)
 s.set(True, [14, 34, 501])
 
As well as :meth:`~BitArray.set` and :meth:`~BitArray.invert` there are also checking methods :meth:`~Bits.all` and :meth:`~Bits.any`. So rather than using ::

 if s[100] and s[200]:
     do_something()
     
it's better to say ::

 if s.all(True, (100, 200)):
     do_something()
     

If the pattern of setting or getting can be expressed as a ``range`` then it is much faster to pass in the range object so that it can be used to optimize the pattern. For example, instead of ::

 for i in range(0, len(s), 2):
     s.set(True, i)

you should just write ::

 s.set(True, range(0, len(s), 2))