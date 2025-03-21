
# Release Notes

### March 2025: version 4.3.1

* Updated bitarray dependency to allow for v3.x.

### January 2025: version 4.3.0

#### A minor update.

* Upgraded bitarray dependency to >= 3.0.0.
* Explicit support for Python 3.13.
* Added `i` and `I` struct codes for 32-bit ints. Bug #340.
* Removed the 'experimental feature' label from the new exotic floating point types.
* Fix for negative index LSB0 slicing issue. Bug #343.

### May 2024: version 4.2.3

#### More small bug fixes related to some of the new (beta) float formats.

* Some codes representing exotic float negative zero converted to positive zero. Bug #333.
* Auto-scaling rounding the wrong way on occasion. Bug #334.

### May 2024: version 4.2.2
#### A couple more minor bug fixes.

* Sometimes a `ValueError` was being raised instead of a `ReadError`. Bug #325.
* Initialising a bitstring from `None` now raises a `TypeError` rather than generating an empty bitstring. Bug #323.
* Fixed performance regression for `find`/`findall` in some situations. Bug #326.
* Fix for `AttributeError` bug when combining `Bits` with `BitStream`. Bug #329.

### April 2024: version 4.2.1

#### Fixing a few regressions introduced in 4.2.0.

* Module crashes on import with 32-bit Python. Bug #317.
* Lists of integers not converted to bytes when using the bytes constructor. Bug #318.
* Empty comma separated tokens not handled correctly. Bug #319.
* Crash on import when docstrings not present due to optimize flag. Bug #321.

## April 2024: version 4.2.0

This release contains a fairly large refactor of how different types are managed. This
shouldn't affect the end user, and the main noticeable change should be the new Dtype
class, which is optional to use.

Support for 8-bit and smaller floats has been reworked and expanded. These are still
a 'beta' feature.

#### Backwardly incompatible changes

* Dropped support for Python 3.7. Minimum version is now 3.8.
* For tokens that use a non-numeric length, a `':'` is now compulsory rather than
  recommended. For example use `'uint:foo'` instead of `'uintfoo'`.
* The previous `e4m3float` and `e5m2float` formats have become the slightly modified
  `p4binary8` and `p3binary8` formats.
* Some parameters are now enforced as positional only, such as `auto` in constructors.

#### Other changes

* The `Array` class is no longer 'beta'.

* A new `Dtype` class can be optionally used to specify types.

* The `bitstring.options` object is now the preferred method for changing module options.
  The `bitstring.lsb0` and `bitstring.bytealigned` variables are now deprecated, use
  `bitstring.options.lsb0` and `bitstring.options.bytealigned` instead.

* New `fromstring` method as another way to create bitstrings from formatted strings.
  Instead of relying on the `auto` parameter you can now optionally use `fromstring`.
  ```pycon
  >>> s1 = BitArray('u24=1000')             # This is still fine.
  >>> s2 = BitArray.fromstring('u24=1000')  # This may be clearer and more efficient.
  ```
* More types can now be pretty printed. For example integer and float formats can be used.
  ```pycon
  >>> s.pp('u15, bin')
  ```

* Pretty printing is now prettier - optional terminal colours added.

* A range of 8-bit, 6-bit and even 4-bit float formats added (beta):
  * `p3binary8`: IEEE 8-bit floating point with 3 bit precision.
  * `p4binary8`: IEEE 8-bit floating point with 4 bit precision.
  * `e5m2mxfp`: OCP 8-bit floating point with 3 bit precision.
  * `e4m3mxfp`: OCP 8-bit floating point with 4 bit precision.
  * `e2m3mxfp`: OCP 6-bit floating point with 4 bit precision.
  * `e3m2mxfp`: OCP 6-bit floating point with 3 bit precision.
  * `e2m1mxfp`: OCP 4-bit floating point with 2 bit precision.
  * `e8m0mxfp`: OCP 8-bit unsigned floating point designed to scale the other formats.
  * `mxint`: OCP 8-bit floating point that is a scaled integer representation.

* Performance improvements.

### November 2023: version 4.1.4

Fixing a regression introduced in 4.1.3

* `'bytes'` token can't be used without explicit length. Bug #303.

### November 2023: version 4.1.3

A maintenance release, with some changes to the beta features introduced in 4.1.

* Removed a couple of files that accidentally got included in the previous release. Bug #293.
* The 8-bit float formats have been renamed `e4m3float` and `e5m2float`.
* Some refactoring and performance optimizations.

### September 2023: version 4.1.2 released

Another maintenance release. Once again some small changes to the 'beta' `Array` class,
plus new Array functionality.

* Fix for the module command-line usage. Bug #290.
* Fix for when creating bitstrings from `memoryview` objects.
* Renamed the `fmt` parameter for Arrays to `dtype`.
* More Array operator coverage.
* Added operators that act on two Arrays of the same size.
* Added comparison operators for Arrays that return an Array of bools.
* Added `Array.equals` method as `==` will now return an `Array` (see above item).
* Added `astype()` method for Arrays to easily cast to a new dtype.

### August 2023: version 4.1.1 released

A maintenance release, with some changes to the Array class which is still in beta.

* bitarray dependency now pinned to `">=2.8.0, <3.0.0"` rather than a specific version. Bug #283.
* Fix for using numpy integers as integer parameters. Bug #286.
* Removed ability to extend an Array with the `+` operator. Use the `extend` method instead.
* Improvements when pretty-printing the Array.
* `Array.count()` can now count `float('nan')` values for floating point types.

## August 2023: version 4.1.0 released

This has turned into a surprisingly big release, with a major refactor and a brand-new
class (the first for 12 years!)

There are also a couple of small possibly breaking changes
detailed below, in particular 'auto' initialising bitstrings from integers is now disallowed.

#### Speed increased with bitarray dependency.

The major weakness of bitstring has been its poor performance for computationally
intensive tasks relative to lower level alternatives. This was principally due to
relying on pure Python code to achieve things that the base language often didn't have
fast ways of doing.

This release starts to address that problem with a fairly extensive rewrite to replace
much of the pure Python low-level bit operations with methods from the bitarray package.
This is a package that does many of the same things as bitstring, and the two packages
have co-existed for a long time. While bitarray doesn't have all of the options and
facilities of bitstring it has the advantage of being very fast as it is implemented in C.
By replacing the internal datatypes I can speed up bitstring's operations while keeping
the same API.

Huge kudos to Ilan Schnell for all his work on bitarray.

#### New Array class for homogeneous data (beta)

If your data is all of a single type you can make use of the new `Array` class, which
mirrors much of the functionality of the standard `array.array` type, but doesn't restrict
you to just a dozen formats.

```pycon
>>> from bitstring import Array
>>> a = Array('uint7', [9, 100, 3, 1])
>>> a.data
BitArray('0x1390181')
>>> b = Array('float16', a.tolist())
>>> b.append(0.25)
>>> b.tobytes()
b'H\x80V@B\x00<\x004\x00'
>>> b.tolist()
[9.0, 100.0, 3.0, 1.0, 0.25]
```
The data is stored efficiently in a `BitArray` object, and you can manipulate both the
data and the `Array` format freely. See the main documentation for more details. Note that
this feature carries the 'beta' flag so may change in future point versions.

#### Other changes

* Added two new floating point interpretations: `float8_143` and `float8_152`. These are 8-bit
  floating point formats, with very limited range and precision, but useful in some fields,
  particularly machine learning. This is an experimental feature - the formats haven't
  even been standardised yet.

  ```pycon
  >>> a = Bits(float8_143=16.5)
  >>> a.bin
  '01100000'
  >>> a.float8_143
  16.0
  ```

* Auto initialization from ints has been removed and now raises a `TypeError`. Creating a
  bitstring from an int still creates a zeroed bitstring of that length but ints won't
  be promoted to bitstrings as that has been a constant source of errors and confusion.
  ```pycon
  >>> a = BitArray(100)  # Fine - create with 100 zeroed bits
  >>> a += 0xff   # TypeError - previously this would have appended 0xff (=255) zero bits.
  >>> a += '0xff'  # Probably what was meant - append eight '1' bits.
  >>> a += Bits(255)  # Fine, append 255 zero bits.
  ```

  This is a breaking change, but it breaks loudly with an exception, it is easily recoded,
  and it removes a confusing wrinkle.

* Explicitly specifying the `auto` parameter is now disallowed rather than discouraged.
  It was always meant to be a positional-only parameter (and will be once I can drop
  Python 3.7 support) but for now it's renamed to `__auto`. In the unlikely event
  this breaks code, the fix should be just to delete the `auto=` if it's already the
  first parameter.
  ```pycon
  >>> s = Bits(auto='0xff')  # Now raises a CreationError
  >>> s = Bits('0xff')  # Fine, as always
  ```
* Deleting, replacing or inserting into a bitstring resets the bit position to 0 if the
  bitstring's length has been changed. Previously the bit position was adjusted but
  this was not well-defined.

* Only empty bitstring are now considered false in a boolean sense. Previously `s` was
  `False` if no bits in `s` were set to `1`, but this goes against what it means to be a
  container in Python, so I consider this to be a bug, even if it was documented. I'm
  guessing it's related to `__nonzero__` in Python 2 becoming `__bool__` in Python 3, and
  it's never been fixed before now.

* Casting to `bytes` now behaves as expected, so that `bytes(s)` gives the same result as
  `s.tobytes()`. Previously it created a byte per bit.

* Pretty printing with the `'bytes'` format now uses characters from the 'Latin Extended-A'
  unicode block for non-ASCII and unprintable characters instead of replacing them with `'.'`

* When using struct-like codes you can now use `'='` instead of `'@'` to signify native-
  endianness. They behave identically, but the new `'='` is now preferred.

* More fixes for LSB0 mode. There are now no known issues with this feature.

### April 2023: version 4.0.2 released

#### A maintenance release

* Added `py.typed` file and converted the module to a package to let mypy find type
  annotations. Bug 248.
* Fix to shifting operations when using LSB0 mode. Bug 251.
* A few more fixes for LSB0 mode.
* Improved LSB0 documentation.
* Added build-system section to `pyproject.toml`. Bug 243.
* Rewrote the walkthrough documentation as a jupyter notebook.
* Updated the project's logo.

## November 2022: version 4.0 released

This is a major release which drops support for Python 2.7 and has a new minimum
requirement of Python 3.7. Around 95% of downloads satisfy this - users of
older versions can continue to use bitstring 3.1, which will still be supported
with fixes, but no new features.

Other breaking changes are minimal, and there are a few cool features added.

#### Breaking changes

* Minimum supported Python version is now Python 3.7.
* Removed `ConstBitArray` and `BitString` class aliases. Use `Bits` and `BitStream` instead.
* The `cut()` method will now also yield the final bits of a bitstring, even if they
  are shorter than the requested cut size.
* Removed default `uint` interpretation. This wasn't being applied uniformly - the default
  is now always to return a bitstring object of the given length and not to interpret
  it as a `uint`. Bug 220.
* If an overwrite goes beyond the end of the bitstring it will now extend the bitstring
  rather than raise an exception. Bug 148.

#### New features and improvements

* Type hints added throughout the code.
* Underscores are now allowed in strings representing number literals.
* The `copy()` method now works on `Bits` as well as `BitArray` objects.
* The experimental command-line feature is now official. Command-line
  parameters are concatenated and a bitstring created from them. If
  the final parameter is either an interpretation string or ends with
  a `'.'` followed by an interpretation string then that interpretation
  of the bitstring will be used when printing it.
  ```pycon
  $ python -m bitstring int:16=-400
  0xfe70
  $ python -m bitstring float:32=0.2 bin
  00111110010011001100110011001101
  ```

* New `pp()` method that pretty-prints the bitstring in various formats - useful
  especially in interactive sessions. Thanks to Omer Barak for the suggestion
  and discussion.

  ```pycon
  >>> s.pp()
    0: 10001000 01110110 10001110 01110110 11111000 01110110 10000111 00101000
   64: 01110010 11111001 10000111 10011000 11110111 10011110 10000111 11111101
  128: 11111001 10001100 01111111 10111100 10111111 11011011 11101011 11111011
  192: 1100
  >>> s.pp('bin, hex')
    0: 10001000 01110110 10001110 01110110 11111000 01110110   88 76 8e 76 f8 76
   48: 10000111 00101000 01110010 11111001 10000111 10011000   87 28 72 f9 87 98
   96: 11110111 10011110 10000111 11111101 11111001 10001100   f7 9e 87 fd f9 8c
  144: 01111111 10111100 10111111 11011011 11101011 11111011   7f bc bf db eb fb
  192: 1100                                                    c
  ```

* Shorter and more versatile properties. The `bin`, `oct`, `hex`, `float`, `uint` and `int`
  properties can now be shortened to just their first letter. They can also have
  a length in bits after them - allowing Rust-like data types.

  ```pycon
  >>> s = BitArray('0x44961000')
  >>> s.h
  '44961000'
  >>> s.f32
  1200.5
  >>> s.u
  1150685184
  >>> s.i7 = -60
  >>> s.b
  '1000100'
  >>> t = Bits('u12=160, u12=120, b=100')
  ```

* Other types with bit lengths can also be used as properties:
  ```pycon
  >>> s.floatle64 = 10.511
  ```
* A colon is no longer required in format strings before a bit length. So for
  example `Bits('int:15=-101')` could be written as `Bits('int15=-101')`. This is
  now the preferred usage in the documentation except where the colon improves
  readability.

* Support for IEEE 16 bit floats. Floating point types can now be 16 bits long as well
  as 32 and 64 bits. This is using the `'e'` format from the struct module.

* Support for bfloats. This is a specialised 16-bit floating point format
  mostly used in machine learning. It's essentially a truncated IEEE 32-bit
  format that keeps its range but only has a couple of significant figures of
  accuracy.


### July 20th 2021: version 3.1.9 released

(version 3.1.8 was pulled due to serious issues)
Another maintenance release.

* Fixed a couple of outdated results in the readme (Issue 214).
* Some more documentation tidying.
* Turned off some debug code by default.
* Fixed a couple of failing tests in different Python versions.
* Fix for consistent pos initialisation semantics for different types.
* Change to allow wheels to be uploaded to PyPI.
* More work for LSB0 mode, but still not finished or documented (sorry).

### May 5th 2020: version 3.1.7 released

This is a maintenance release with a few bug fixes plus an experimental
feature to allow bits to be indexed in the opposite direction.

* Fixing del not working correctly when stop value negative (Issue 201)
* Removed deprecated direct import of ABC from collections module (Issue 196)
* Tested and added explicit support for Python 3.7 and 3.8. (Issue 193)
* Fixing a few stale links to documentation. (Issue 194)
* Allowing initialisation with an io.BytesIO object. (Issue 189)

#### Experimental LSB0 mode

This feature allows bitstring to use Least Significant Bit Zero
(LSB0) bit numbering; that is the final bit in the bitstring will
be bit `0`, and the first bit will be bit `(n-1)`, rather than the
other way around. LSB0 is a more natural numbering
system in many fields, but is the opposite to Most Significant Bit
Zero (MSB0) numbering which is the natural option when thinking of
bitstrings as standard Python containers.

To switch from the default MSB0, use the module level function
```pycon
>>> bitstring.set_lsb0(True)
```

Getting and setting bits should work in this release, as will some
other methods. Many other methods are not tested yet and might not
work as expected. This is mostly a release to get feedback before
finalising the interface.

Slicing is still done with the start bit smaller than the end bit.
For example:
```pycon
>>> s = Bits('0b000000111')
>>> s[0:5]
Bits('0b00111')
>>> s[0]
True
```

Negative indices work as (hopefully) you'd expect, with the first stored
bit being `s[-1]` and the final stored bit being `s[-n]`.

See https://github.com/scott-griffiths/bitstring/issues/156 for
discussions and to add any further comments.

### July 9th 2019: version 3.1.6 released
A long overdue maintenance release with some fixes.

* Fixed immutability bug. Bug 176. 
* Fixed failure of `__contains__` in some circumstances. Bug 180.
* Better handling of open files. Bug 186.
* Better Python 2/3 check.
* Making unit tests easier to run.
* Allowing length of 1 to be specified for bools. (Thanks to LemonPi)

### May 17th 2016: version 3.1.5 released

* Support initialisation from an array.
* Added a separate LICENSE file.

### March 19th 2016: version 3.1.4 released
This is another bug fix release.

* Fix for bitstring types when created directly from other bitstring types.
* Updating contact, website details.

### March 4th 2014: version 3.1.3 released
This is another bug fix release.

* Fix for problem with prepend for bitstrings with byte offsets in their data store.

### April 18th 2013: version 3.1.2 released
This is another bug fix release.

* Fix for problem where unpacking bytes would by eight times too long

### March 21st 2013: version 3.1.1 released
This is a bug fix release.

* Fix for problem where concatenating bitstrings sometimes modified method's arguments

## February 26th 2013: version 3.1.0 released
This is a minor release with a couple of new features and some bug fixes.

#### New 'pad' token

This token can be used in reads and when packing/unpacking to indicate that
you don't care about the contents of these bits. Any padding bits will just
be skipped over when reading/unpacking or zero-filled when packing.

```pycon
>>> a, b = s.readlist('pad:5, uint:3, pad:1, uint:3')
```
Here only two items are returned in the list - the padding bits are ignored.

#### New clear and copy convenience methods

These methods have been introduced in Python 3.3 for lists and bytearrays,
as more obvious ways of clearing and copying, and we mirror that change here.

`t = s.copy()` is equivalent to `t = s[:]`, and `s.clear()` is equivalent to `del s[:]`.

#### Other changes

* Some bug fixes.

### February 7th 2012: version 3.0.2 released
This is a minor update that fixes a few bugs.

* Fix for subclasses of bitstring classes behaving strangely (Issue 121).
* Fix for excessive memory usage in rare cases (Issue 120).
* Fixes for slicing edge cases.

There has also been a reorganisation of the code to return it to a single
`bitstring.py` file rather than the package that has been used for the past
several releases. This change shouldn't affect users directly.

### November 21st 2011: version 3.0.1 released
This release fixed a small but very visible bug in bitstring printing.

## November 21st 2011: version 3.0.0 released
This is a major release which breaks backward compatibility in a few places.

### Backwardly incompatible changes

#### Hex, oct and bin properties don't have leading 0x, 0o and 0b

If you ask for the hex, octal or binary representations of a bitstring then
they will no longer be prefixed with `'0x'`, `'0o'` or `'0b'`. This was done as it
was noticed that the first thing a lot of user code does after getting these
representations was to cut off the first two characters before further
processing.


```pycon
>>> a = BitArray('0x123')
>>> a.hex, a.oct, a.bin
('123', '0443', '000100100011')
```
Previously this would have returned `('0x123', '0o0443', '0b000100100011')`

This change might require some recoding, but it should all be simplifications.

#### ConstBitArray renamed to Bits

Previously `Bits` was an alias for `ConstBitStream` (for backward compatibility).
This has now changed so that `Bits` and `BitArray` loosely correspond to the
built-in types `bytes` and `bytearray`.

If you were using streaming/reading methods on a `Bits` object then you will
have to change it to a `ConstBitStream`.

The `ConstBitArray` name is kept as an alias for `Bits`.

#### Stepping in slices has conventional meaning

The step parameter in `__getitem__`, `__setitem__` and `__delitem__` used to act
as a multiplier for the start and stop parameters. No one seemed to use it
though and so it has now reverted to the conventional meaning for containers.

If you are using step then recoding is simple: `s[a:b:c]` becomes `s[a*c:b*c]`.

Some examples of the new usage:

```pycon
>>> s = BitArray('0x0000')
s[::4] = [1, 1, 1, 1]
>>> s.hex
'8888'
>>> del s[8::2]
>>> s.hex
'880'
```

### New features

#### New readto method

This method is a mix between a find and a read - it searches for a bitstring
and then reads up to and including it. For example:

```pycon
>>> s = ConstBitStream('0x47000102034704050647')
>>> s.readto('0x47', bytealigned=True)
BitStream('0x47')
>>> s.readto('0x47', bytealigned=True)
BitStream('0x0001020347')
>>> s.readto('0x47', bytealigned=True)
BitStream('0x04050647')
```

#### pack function accepts an iterable as its format

Previously only a string was accepted as the format in the `pack` function.
This was an oversight as it broke the symmetry between `pack` and `unpack`.
Now you can use formats like this:

```python
fmt = ['hex:8', 'bin:3']
a = pack(fmt, '47', '001')
a.unpack(fmt)
```


## June 18th 2011: version 2.2.0 released
This is a minor upgrade with a couple of new features.

### New interleaved exponential-Golomb interpretations

New bit interpretations for interleaved exponential-Golomb (as used in the
Dirac video codec) are supplied via `uie` and `sie`:

```pycon
>>> s = BitArray(uie=41)
>>> s.uie
41
>>> s.bin
'0b00010001001'
```

These are pretty similar to the non-interleaved versions - see the manual
for more details. Credit goes to Paul Sargent for the patch.

### New package-level bytealigned variable

A number of methods take a `bytealigned` parameter to indicate that they
should only work on byte boundaries (e.g. `find`, `replace`, `split`). Previously
this parameter defaulted to `False`. Instead, it now defaults to
`bitstring.bytealigned`, which itself defaults to `False`, but can be changed
to modify the default behaviour of the methods. For example:

```pycon
>>> a = BitArray('0x00 ff 0f ff')
>>> a.find('0x0f')
(4,)    # found first not on a byte boundary
>>> a.find('0x0f', bytealigned=True)
(16,)   # forced looking only on byte boundaries
>>> bitstring.bytealigned = True  # Change default behaviour
>>> a.find('0x0f')
(16,)
>>> a.find('0x0f', bytealigned=False)
(4,)
```

If you're only working with bytes then this can help avoid some errors and
save some typing!

### Other changes

* Fix for Python 3.2, correcting for a change to the binascii module.
* Fix for bool initialisation from 0 or 1.
* Efficiency improvements, including interning strategy.

### February 23rd 2011: version 2.1.1 released
This is a release to fix a couple of bugs that were introduced in 2.1.0.

* Bug fix: Reading using the `'bytes'` token had been broken (Issue 102).
* Fixed problem using some methods on `ConstBitArrays`.
* Better exception handling for tokens missing values.
* Some performance improvements.

## January 23rd 2011: version 2.1.0 released

### New class hierarchy introduced with simpler classes
Previously there were just two classes, the immutable `Bits` which was the base
class for the mutable `BitString` class. Both of these classes have the concept
of a bit position, from which reads etc. take place so that the bitstring could
be treated as if it were a file or stream.

Two simpler classes have now been added which are purely bit containers and 
don't have a bit position. These are called `ConstBitArray` and `BitArray`. As you
can guess the former is an immutable version of the latter.

The other classes have also been renamed to better reflect their capabilities.
Instead of `BitString` you can use `BitStream`, and instead of `Bits` you can use
`ConstBitStream`. The old names are kept as aliases for backward compatibility.

The classes hierarchy is:

```
        ConstBitArray
           /    \
          /      \
    BitArray   ConstBitStream (formerly Bits)
          \      /
           \    /
          BitStream (formerly BitString)
```

### Other changes
A lot of internal reorganisation has taken place since the previous version,
most of which won't be noticed by the end user. Some things you might see are:

* New package structure. Previous versions have been a single file for the
  module and another for the unit tests. The module is now split into many
  more files so it can't be used just by copying `bitstring.py` any more.
* To run the unit tests there is now a script called `runtests.py` in the test
  directory.
* File based bitstring are now implemented in terms of an mmap. This should
  be just an implementation detail, but unfortunately for 32-bit versions of
  Python this creates a limit of 4GB on the files that can be used. The work
  around is either to get a 64-bit Python, or just stick with version 2.0.
* The `ConstBitArray` and `ConstBitStream` classes no longer copy byte data when
  a slice or a read takes place, they just take a reference. This is mostly
  a very nice optimisation, but there are occasions where it could have an
  adverse effect. For example if a very large bitstring is created, a small
  slice taken and the original deleted. The byte data from the large
  bitstring would still be retained in memory.
* Optimisations. Once again this version should be faster than the last.
  The module is still pure Python but some of the reorganisation was to make
  it more feasible to put some of the code into Cython or similar, so
  hopefully more speed will be on the way.

### July 26th 2010: version 2.0.3 released
* Bug fix: Using peek and read for a single bit now returns a new bitstring
  as was intended, rather than the old behaviour of returning a bool.
* Removed HTML docs from source archive - better to use the online version.

## July 2010: version 2.0 released
This is a major release, with a number of backwardly incompatible changes.
The main change is the removal of many methods, all of which have simple
alternatives. Other changes are quite minor but may need some recoding.

There are a few new features, most of which have been made to help the
stream-lining of the API. As always there are performance improvements and
some API changes were made purely with future performance in mind.

### Backwardly incompatible changes

#### Methods removed.

About half of the class methods have been removed from the API. They all have
simple alternatives, so what remains is more powerful and easier to remember.
The removed methods are listed here on the left, with their equivalent
replacements on the right:

```
s.advancebit()              ->   s.pos += 1
s.advancebits(bits)         ->   s.pos += bits
s.advancebyte()             ->   s.pos += 8
s.advancebytes(bytes)       ->   s.pos += 8*bytes
s.allunset([a, b])          ->   s.all(False, [a, b])
s.anyunset([a, b])          ->   s.any(False, [a, b])
s.delete(bits, pos)         ->   del s[pos:pos+bits]
s.peekbit()                 ->   s.peek(1)
s.peekbitlist(a, b)         ->   s.peeklist([a, b])
s.peekbits(bits)            ->   s.peek(bits)
s.peekbyte()                ->   s.peek(8)
s.peekbytelist(a, b)        ->   s.peeklist([8*a, 8*b])
s.peekbytes(bytes)          ->   s.peek(8*bytes)
s.readbit()                 ->   s.read(1)
s.readbitlist(a, b)         ->   s.readlist([a, b])
s.readbits(bits)            ->   s.read(bits)
s.readbyte()                ->   s.read(8)
s.readbytelist(a, b)        ->   s.readlist([8*a, 8*b])
s.readbytes(bytes)          ->   s.read(8*bytes)
s.retreatbit()              ->   s.pos -= 1
s.retreatbits(bits)         ->   s.pos -= bits
s.retreatbyte()             ->   s.pos -= 8
s.retreatbytes(bytes)       ->   s.pos -= 8*bytes
s.reversebytes(start, end)  ->   s.byteswap(0, start, end)
s.seek(pos)                 ->   s.pos = pos
s.seekbyte(bytepos)         ->   s.bytepos = bytepos
s.slice(start, end, step)   ->   s[start:end:step]
s.tell()                    ->   s.pos
s.tellbyte()                ->   s.bytepos
s.truncateend(bits)         ->   del s[-bits:]
s.truncatestart(bits)       ->   del s[:bits]
s.unset([a, b])             ->   s.set(False, [a, b])
```

Many of these methods have been deprecated for the last few releases, but
there are some new removals too. Any recoding needed should be quite
straightforward, so while I apologise for the hassle, I had to take the
opportunity to streamline and rationalise what was becoming a bit of an
overblown API.

#### set / unset methods combined.

The set/unset methods have been combined in a single method, which now
takes a boolean as its first argument:

```
s.set([a, b])               ->   s.set(1, [a, b])
s.unset([a, b])             ->   s.set(0, [a, b])
s.allset([a, b])            ->   s.all(1, [a, b])
s.allunset([a, b])          ->   s.all(0, [a, b])
s.anyset([a, b])            ->   s.any(1, [a, b])
s.anyunset([a, b])          ->   s.any(0, [a, b])
```

#### all / any only accept iterables.

The `all` and `any` methods (previously called `allset`, `allunset`, `anyset` and
`anyunset`) no longer accept a single bit position. The recommended way of
testing a single bit is just to index it, for example instead of:

```pycon
>>> if s.all(True, i):
```

just use
```pycon
>>> if s[i]:
```

If you really want to you can of course use an iterable with a single
element, such as `s.any(False, [i])`, but it's clearer just to write
`not s[i]`.

#### Exception raised on reading off end of bitstring.

If a read or peek goes beyond the end of the bitstring then a `ReadError`
will be raised. The previous behaviour was that the rest of the bitstring
would be returned and no exception raised.

#### BitStringError renamed to Error.

The base class for errors in the bitstring module is now just `Error`, so
it will likely appear in your code as `bitstring.Error` instead of
the rather repetitive `bitstring.BitStringError`.

#### Single bit slices and reads return a bool.

A single index slice (such as `s[5]`) will now return a bool (i.e. `True` or
`False`) rather than a single bit bitstring. This is partly to reflect the
style of the bytearray type, which returns an integer for single items, but
mostly to avoid common errors like:

```pycon
>>> if s[0]:
...     do_something()
```
While the intent of this code snippet is quite clear (i.e. do_something if
the first bit of s is set) under the old rules `s[0]` would be true as long
as `s` wasn't empty. That's because any one-bit bitstring was true as it was a
non-empty container. Under the new rule `s[0]` is `True` if `s` starts with a `1`
bit and `False` if `s` starts with a `0` bit.

The change does not affect reads and peeks, so `s.peek(1)` will still return
a single bit bitstring, which leads on to the next item...

#### Empty bitstrings or bitstrings with only zero bits are considered False.

Previously a bitstring was `False` if it had no elements, otherwise it was `True`.
This is standard behaviour for containers, but wasn't very useful for a container
of just 0s and 1s. The new behaviour means that the bitstring is False if it
has no `1` bits. This means that code like this:

```pycon
>>> if s.peek(1):
...     do_something()
```
should work as you'd expect. It also means that `Bits(1000)`, `Bits(0x00)` and
`Bits('uint:12=0')` are all also `False`. If you need to check for the emptiness of
a bitstring then instead check the len property:

```
if s                ->   if s.len
if not s            ->   if not s.len
```
#### Length and offset disallowed for some initialisers.

Previously you could create bitstring using expressions like:

```pycon
>>> s = Bits(hex='0xabcde', offset=4, length=13)
```

This has now been disallowed, and the offset and length parameters may only
be used when initialising with bytes or a file. To replace the old behaviour
you could instead use

```pycon
>>> s = Bits(hex='0xabcde')[4:17]
```

#### Renamed 'format' parameter 'fmt'.

Methods with a `format` parameter have had it renamed to `fmt`, to prevent
hiding the built-in `format`. Affects methods `unpack`, `read`, `peek`, `readlist`,
`peeklist` and `byteswap` and the `pack` function. 

#### Iterables instead of *format accepted for some methods.

This means that for the affected methods (`unpack`, `readlist` and `peeklist`) you
will need to use an iterable to specify multiple items. This is easier to
show than to describe, so instead of

```pycon
>>> a, b, c, d = s.readlist('uint:12', 'hex:4', 'bin:7')
```
you would instead write

```pycon
>>> a, b, c, d = s.readlist(['uint:12', 'hex:4', 'bin:7'])
```

Note that you could still use the single string `'uint:12, hex:4, bin:7'` if
you preferred.

#### Bool auto-initialisation removed.

You can no longer use `True` and `False` to initialise single bit bitstrings.
The reasoning behind this is that as `bool` is a subclass of `int`, it really is
bad practice to have `Bits(False)` be different to `Bits(0)` and to have `Bits(True)`
different to `Bits(1)`.

If you have used bool auto-initialisation then you will have to be careful to
replace it as the bools will now be interpreted as ints, so `Bits(False)` will
be empty (a bitstring of length 0), and `Bits(True)` will be a single zero bit
(a bitstring of length 1). Sorry for the confusion, but I think this will
prevent bigger problems in the future.

There are a few alternatives for creating a single bit bitstring. My favourite
it to use a list with a single item:

```
Bits(False)            ->   Bits([0])
Bits(True)             ->   Bits([1])
```
#### New creation from file strategy

Previously if you created a bitstring from a file, either by auto-initialising
with a file object or using the filename parameter, the file would not be read
into memory unless you tried to modify it, at which point the whole file would
be read.

The new behaviour depends on whether you create a `Bits` or a `BitString` from the
file. If you create a `Bits` (which is immutable) then the file will never be
read into memory. This allows very large files to be opened for examination
even if they could never fit in memory.

If however you create a `BitString`, the whole of the referenced file will be read
to store in memory. If the file is very big this could take a long time, or fail,
but the idea is that in saying you want the mutable `BitString` you are implicitly
saying that you want to make changes and so (for now) we need to load it into
memory.

The new strategy is a bit more predictable in terms of performance than the old.
The main point to remember is that if you want to open a file and don't plan to
alter the bitstring then use the `Bits` class rather than `BitString`.

Just to be clear, in neither case will the contents of the file ever be changed -
if you want to output the modified `BitString` then use the `tofile` method, for
example.

#### find and rfind return a tuple instead of a bool.

If a find is unsuccessful then an empty tuple is returned (which is `False` in a
boolean sense) otherwise a single item tuple with the bit position is returned
(which is `True` in a boolean sense). You shouldn't need to recode unless you
explicitly compared the result of a `find` to `True` or `False`, for example this
snippet doesn't need to be altered:

```pycon
>>> if s.find('0x23'):
...     print(s.bitpos)        
```

but you could now instead use
```pycon
>>> found = s.find('0x23')
>>> if found:
...     print(found[0])
```

The reason for returning the bit position in a tuple is so that finding at
position zero can still be `True` - it's the tuple `(0,)` - whereas not found can
be False - the empty tuple `()`.

### New features

#### New count method.

This method just counts the number of 1 or 0 bits in the bitstring.
```pycon
>>> s = Bits('0x31fff4')
>>> s.count(1)
16
```

#### read and peek methods accept integers.

The `read`, `readlist`, `peek` and `peeklist` methods now accept integers as parameters
to mean "read this many bits and return a bitstring". This has allowed a number
of methods to be removed from this release, so for example instead of:

```pycon
>>> a, b, c = s.readbits(5, 6, 7)
>>> if s.peekbit():
...     do_something()
```

you should write:

```pycon
>>> a, b, c = s.readlist([5, 6, 7])
>>> if s.peek(1):
...     do_something()

```

#### byteswap used to reverse all bytes.

The `byteswap` method now allows a format specifier of 0 (the default) to signify
that all of the whole bytes should be reversed. This means that calling just
`byteswap()` is almost equivalent to the now removed `bytereverse()` method (a small
difference is that `byteswap` won't raise an exception if the bitstring isn't a
whole number of bytes long).

#### Auto initialise with bytearray or (for Python 3 only) bytes.

So rather than writing:

```pycon
>>> a = Bits(bytes=some_bytearray)

```

you can just write

```pycon
>>> a = Bits(some_bytearray)
```

This also works for the `bytes` type, but only if you're using Python 3.
For Python 2 it's not possible to distinguish between a `bytes` object and a
`str`. For this reason this method should be used with some caution as it will
make you code behave differently with the different major Python versions.

```pycon
>>> b = Bits(b'abcd\x23\x00') # Only Python 3!
```
  
#### set, invert, all and any default to whole bitstring.

This means that you can for example write:

```pycon
>>> a = BitString(100)       # 100 zero bits
>>> a.set(1)                 # set all bits to 1
>>> a.all(1)                 # are all bits set to 1?
True
>>> a.any(0)                 # are any set to 0?
False
>>> a.invert()               # invert every bit
```
  
#### New exception types.

As well as renaming `BitStringError` to just `Error` 
there are also new exceptions which use Error as a base class.

These can be caught in preference to `Error` if you need finer control.
The new exceptions sometimes also derive from built-in exceptions:

```

ByteAlignError(Error) # whole byte position or length needed.

ReadError(Error, IndexError) # reading or peeking off the end of the bitstring.

CreationError(Error, ValueError) # inappropriate argument during bitstring creation.

InterpretError(Error, ValueError) # inappropriate interpretation of binary data.

```

## March 18th 2010: version 1.3.0 for Python 2.6 and 3.x released

### New features

#### byteswap method for changing endianness.

Changes the endianness in-place according to a format string or
integer(s) giving the byte pattern. See the manual for details.

```pycon
>>> s = BitString('0x00112233445566')
>>> s.byteswap(2)
3
>>> s
BitString('0x11003322554466')
>>> s.byteswap('h')
3
>>> s
BitString('0x00112233445566')
>>> s.byteswap([2, 5])
1
>>> s
BitString('0x11006655443322')
```

#### Multiplicative factors in bitstring creation and reading.

For example:

```pycon
>>> s = Bits('100*0x123')
```

#### Token grouping using parenthesis.

For example:

```pycon
>>> s = Bits('3*(uint:6=3, 0b1)')
```

#### Negative slice indices allowed.

The `start` and `end` parameters of many methods may now be negative, with the
same meaning as for negative slice indices. Affects all methods with these
parameters.

#### Sequence ABCs used.

The `Bits` class now derives from `collections.Sequence`, while the `BitString`
class derives from `collections.MutableSequence`.

#### Keywords allowed in readlist, peeklist and unpack.

Keywords for token lengths are now permitted when reading. So for example,
you can write

```pycon
>>> s = bitstring.pack('4*(uint:n)', 2, 3, 4, 5, n=7)
>>> s.unpack('4*(uint:n)', n=7)
[2, 3, 4, 5]
```

#### start and end parameters added to rol and ror.

#### join function accepts other iterables.

Also its parameter has changed from `bitstringlist` to `sequence`. This is
technically a backward incompatibility in the unlikely event that you are
referring to the parameter by name.

#### `__init__` method accepts keywords.

Rather than a long list of initialisers the `__init__` methods now use a
`**kwargs` dictionary for all initialisers except `auto`. This should have no
effect, except that this is a small backward incompatibility if you use
positional arguments when initialising with anything other than auto
(which would be rather unusual).

#### More optimisations.

#### Bug fixed in replace method (it could fail if start != 0).

### January 19th 2010: version 1.2.0 for Python 2.6 and 3.x released

#### New `Bits` class.

Introducing a brand new class, `Bits`, representing an immutable sequence of
bits.

The `Bits` class is the base class for the mutable `BitString`. The differences
between `Bits` and `BitStrings` are:

1) `Bits` are immutable, so once they have been created their value cannot change.
This of course means that mutating methods (`append`, `replace`, `del` etc.) are not
available for `Bits`.

2) `Bits` are hashable, so they can be used in sets and as keys in dictionaries.

3) `Bits` are potentially more efficient than `BitStrings`, both in terms of
computation and memory. The current implementation is only marginally
more efficient though - this should improve in future versions.

You can switch from `Bits` to a `BitString` or vice versa by constructing a new
object from the old.

```pycon
>>> s = Bits('0xabcd')
>>> t = BitString(s)
>>> t.append('0xe')
>>> u = Bits(t)
```

The relationship between `Bits` and `BitString` is supposed to loosely mirror that
between `bytes` and `bytearray` in Python 3.

#### Deprecation messages turned on.

A number of methods have been flagged for removal in version 2. Deprecation
warnings will now be given, which include an alternative way to do the same
thing. All of the deprecated methods have simpler equivalent alternatives.

```pycon
>>> t = s.slice(0, 2)
__main__:1: DeprecationWarning: Call to deprecated function slice.
Instead of 's.slice(a, b, c)' use 's[a:b:c]'.
```

The deprecated methods are: `advancebit`, `advancebits`, `advancebyte`, `advancebytes`,
`retreatbit`, `retreatbits`, `retreatbyte`, `retreatbytes`, `tell`, `seek`, `slice`, `delete`,
`tellbyte`, `seekbyte`, `truncatestart` and `truncateend`.

#### Initialise from bool.

Booleans have been added to the list of types that can 'auto'
initialise a bitstring.

```pycon
>>> zerobit = BitString(False)
>>> onebit = BitString(True)
```

#### Improved efficiency.

More methods have been sped up, in particular some deletions and insertions.

#### Bug fixes.

A rare problem with truncating the start of bitstrings was fixed.

A possible problem outputting the final byte in `tofile()` was fixed.

### December 22nd 2009: version 1.1.3 for Python 2.6 and 3.x released

This version hopefully fixes an installation problem for platforms with
case-sensitive file systems. There are no new features or other bug fixes.

### December 18th 2009: version 1.1.2 for Python 2.6 and 3.x released

This is a minor update with (almost) no new features.

* Improved efficiency.

The speed of many typical operations has been increased, some substantially.

* Initialise from integer.

A BitString of '0' bits can be created using just an integer to give the length
in bits. So instead of

```pycon
>>> s = BitString(length=100)
```

you can write just

```pycon
>>> s = BitString(100)
```

This matches the behaviour of bytearrays and (in Python 3) bytes.

* A defect related to using the `set` / `unset` functions on BitStrings initialised
from a file has been fixed.

### November 24th 2009: version 1.1.0 for Python 2.6 and 3.x released

Note that this version will not work for Python 2.4 or 2.5. There may be an
update for these Python versions some time next year, but it's not a priority
quite yet. Also note that only one version is now provided, which works for
Python 2.6 and 3.x (done with the minimum of hackery!)

#### Improved efficiency.

A fair number of functions have improved efficiency, some quite dramatically.

#### New bit setting and checking functions.

Although these functions don't do anything that couldn't be done before, they
do make some common use cases much more efficient. If you need to set or check
single bits then these are the functions you need.
```
set / unset : Set bit(s) to 1 or 0 respectively.
allset / allunset : Check if all bits are 1 or all 0.
anyset / anyunset : Check if any bits are 1 or any 0.
```
For example

```pycon
>>> s = BitString(length=1000)
>>> s.set((10, 100, 44, 12, 1))
>>> s.allunset((2, 22, 222))
True
>>> s.anyset(range(7, 77))
True
```
#### New rotate functions.

  `ror` / `rol` : Rotate bits to the right or left respectively.

```pycon
>>> s = BitString('0b100000000')
>>> s.ror(2)
>>> s.bin
'0b001000000'
>>> s.rol(5)
>>> s.bin
'0b000000100'
```
#### Floating point interpretations.

  New float initialisations and interpretations are available. These only work
  for BitStrings of length 32 or 64 bits.
  
```pycon
>>> s = BitString(float=0.2, length=64)
>>> s.float
0.200000000000000001
>>> t = bitstring.pack('<3f', -0.4, 1e34, 17.0)
>>> t.hex
'0xcdccccbedf84f67700008841'
```
#### 'bytes' token reintroduced.

This token returns a bytes object (equivalent to a str in Python 2.6).

```pycon
>>> s = BitString('0x010203')
>>> s.unpack('bytes:2, bytes:1')
['\x01\x02', '\x03']
```
#### 'uint' is now the default token type.

So for example these are equivalent:

```pycon
a, b = s.readlist('uint:12, uint:12')
a, b = s.readlist('12, 12')
```
### October 10th 2009: version 1.0.1 for Python 3.x released

This is a straight port of version 1.0.0 to Python 3.

For changes since the last Python 3 release read all the way down in this
document to version 0.4.3.

This version will also work for Python 2.6, but there's no advantage to using
it over the 1.0.0 release. It won't work for anything before 2.6.

## October 9th 2009: version 1.0.0 for Python 2.x released

Version 1 is here!

This is the first release not to carry the 'beta' tag. It contains a couple of
minor new features but is principally a release to fix the API. If you've been
using an older version then you almost certainly will have to recode a bit. If
you're not ready to do that then you may wish to delay updating.

So the bad news is that there are lots of small changes to the API. The good
news is that all the changes are pretty trivial, the new API is cleaner and
more 'Pythonic', and that by making it version 1.0 I'm promising not to
tweak it again for some time.

### API Changes

#### New `read` / `peek` functions for returning multiple items.

The functions `read`, `readbits`, `readbytes`, `peek`, `peekbits` and `peekbytes` now only
ever return a single item, never a list.

The new functions `readlist`, `readbitlist`, `readbytelist`, `peeklist`, `peekbitlist`
and `peekbytelist` can be used to read multiple items and will always return a
list.

So a line like:

```pycon
>>> a, b = s.read('uint:12, hex:32')
```
becomes

```pycon
>>> a, b = s.readlist('uint:12, hex:32')
```
#### Renaming / removing functions.

Functions have been renamed as follows:

```
seekbit -> seek
tellbit -> tell
reversebits -> reverse
deletebits -> delete
tostring -> tobytes
```
and a couple have been removed altogether:

```
deletebytes - use delete instead.
empty - use 'not s' rather than 's.empty()'.
```
#### Renaming parameters.

The parameters `startbit` and `endbit` have been renamed `start` and `end`.
This affects the functions `slice`, `find`, `findall`, `rfind`, `reverse`, `cut` and `split`.

The parameter `bitpos` has been renamed to `pos`. The affects the functions
`seek`, `tell`, `insert`, `overwrite` and `delete`.

#### Mutating methods return `None` rather than `self`.

This means that you can't chain functions together so

```pycon
>>> s.append('0x00').prepend('0xff')
>>> t = s.reverse()
```
Needs to be rewritten

```pycon
>>> s.append('0x00')
>>> s.prepend('0xff')
>>> s.reverse()
>>> t = s
```
Affects `truncatestart`, `truncateend`, `insert`, `overwrite`, `delete`, `append`,
`prepend`, `reverse` and `reversebytes`.

#### Properties renamed.

The `data` property has been renamed to `bytes`. Also, if the `BitString` is not a
whole number of bytes then a `ValueError` exception will be raised when using
`bytes` as a 'getter'.

Properties `len` and `pos` have been added to replace `length` and `bitpos`,
although the longer names have not been removed, so you can continue to use them
if you prefer.

#### Other changes.

The `unpack` function now always returns a list, never a single item.

BitStrings are now 'unhashable', so calling hash on one or making a set will
fail.

The colon separating the token name from its length is now mandatory. So for
example `BitString('uint12=100')` becomes `BitString('uint:12=100')`.

Removed support for the `'bytes'` token in format strings. Instead of
`s.read('bytes:4')` use `s.read('bits:32')`.

### New features

#### Added endswith and startswith functions

These do much as you'd expect; they return `True` or `False` depending on whether
the BitString starts or ends with the parameter.

```pycon
>>> BitString('0xef342').startswith('0b11101')
True
```
### September 11th 2009: version 0.5.2 for Python 2.x released

Finally some tools for dealing with endianness!

* New interpretations are now available for whole-byte BitStrings that treat
them as big, little, or native-endian.

```pycon
>>> big = BitString(intbe=1, length=16) # or BitString('intbe:16=1') if you prefer.
>>> little = BitString(intle=1, length=16)
>>> print big.hex, little.hex
0x0001 0x0100
>>> print big.intbe, little.intle
1 1
```
* 'Struct'-like compact format codes

To save some typing when using pack, unpack, read and peek, compact format
codes based on those used in the struct and array modules have been added.
These must start with a character indicating the endianness (>, < or @ for
big, little and native-endian), followed by characters giving the format:

```
b 	1-byte signed int
B 	1-byte unsigned int
h 	2-byte signed int
H 	2-byte unsigned int
l 	4-byte signed int
L 	4-byte unsigned int
q 	8-byte signed int
Q 	8-byte unsigned int
```
For example:

```pycon
>>> s = bitstring.pack('<4h', 0, 1, 2, 3)
```
creates a BitString with four little-endian 2-byte integers. While

```pycon
>>> x, y, z = s.read('>hhl')
```
reads them back as two big-endian two-byte integers and one four-byte big
endian integer.

Of course you can combine this new format with the old ones however you like:

```pycon
>>> s.unpack('<h, intle:24, uint:5, bin')
[0, 131073, 0, '0b0000000001100000000']
```
### August 26th 2009: version 0.5.1 for Python 2.x released

This update introduces pack and unpack functions for creating and dissembling
BitStrings.

* New pack() and unpack() functions.

The module level pack function provides a flexible new method for creating
BitStrings. Tokens for BitString 'literals' can be used in the same way as in
the constructor.

```pycon
>>> from bitstring import BitString, pack
>>> a = pack('0b11, 0xff, 0o77, int:5=-1, se=33')
```
You can also leave placeholders in the format, which will be filled in by
the values provided.

```pycon
>>> b = pack('uint:10, hex:4', 33, 'f')
```
Finally, you can use a dictionary or keywords.

```pycon
>>> c = pack('bin=a, hex=b, bin=a', a='010', b='ef')
```
The unpack function is similar to the read function except that it always
unpacks from the start of the BitString.

```pycon
>>> x, y = b.unpack('uint:10, hex')
```
If a token is given without a length (as above) then it will expand to fill the
remaining bits in the BitString. This also now works with read() and peek().

* New `tostring()` and `tofile()` functions.

The `tostring()` function just returns the data as a string, with up to seven
zero bits appended to byte align. The `tofile()` function does the same except
writes to a file object.

```pycon
>>> f = open('myfile', 'wb')
>>> BitString('0x1234ff').tofile(f)
```
* Other changes.

The use of `'='` is now mandatory in 'auto' initialisers. Tokens like `'uint12 100'` will
no longer work. Also, the use of a `':'` before the length is encouraged, but not yet
mandated. So the previous example should be written as `'uint:12=100'`.

The 'auto' initialiser will now take a file object.

```pycon
>>> f = open('myfile', 'rb')
>>> s = BitString(f)
```
### July 19th 2009: version 0.5.0 for Python 2.x released

This update breaks backward compatibility in a couple of areas. The only one
you probably need to be concerned about is the change to the default for
`bytealigned` in `find`, `replace`, `split`, etc.

See the user manual for more details on each of these items.

* Expanded abilities of 'auto' initialiser.

More types can be initialised through the 'auto' initialiser. For example
instead of

```pycon
>>> a = BitString(uint=44, length=16)
```
you can write

```pycon
>>> a = BitString('uint16=44')
```
Also, different comma-separated tokens will be joined together, e.g.

```pycon
>>> b = BitString('0xff') + 'int8=-5'
```
can be written

```pycon
>>> b = BitString('0xff, int8=-5')
```
* New formatted `read()` and `peek()` functions.

These takes a format string similar to that used in the auto initialiser.
If only one token is provided then a single value is returned, otherwise a
list of values is returned.

```pycon
>>> start_code, width, height = s.read('hex32, uint12, uint12')
```
is equivalent to

```pycon
>>> start_code = s.readbits(32).hex
>>> width = s.readbits(12).uint
>>> height = s.readbits(12).uint
```
The tokens are:

```
int n   : n bits as an unsigned integer.
uint n  : n bits as a signed integer.
hex n   : n bits as a hexadecimal string.
oct n   : n bits as an octal string.
bin n   : n bits as a binary string.
ue      : next bits as an unsigned exp-Golomb.
se      : next bits as a signed exp-Golomb.
bits n  : n bits as a new BitString.
bytes n : n bytes as a new BitString.
```
See the user manual for more details.

* `hex()` and `oct()` functions removed.

The special functions for `hex()` and `oct()` have been removed. Please use the
hex and oct properties instead.

```pycon
>>> hex(s)
```
becomes

```pycon
>>> s.hex
```
* join made a member function.

The join function must now be called on a `BitString` object, which will be
used to join the list together. You may need to recode slightly:

```pycon
>>> s = bitstring.join('0x34', '0b1001', '0b1')
```
becomes

```pycon
>>> s = BitString().join('0x34', '0b1001', '0b1')
```
* More than one value allowed in `readbits`, `readbytes`, `peekbits` and `peekbytes`

If you specify more than one bit or byte length then a list of BitStrings will
be returned.

```pycon
>>> a, b, c = s.readbits(10, 5, 5)
```
is equivalent to

```pycon
>>> a = readbits(10)
>>> b = readbits(5)
>>> c = readbits(5)
```
* `bytealigned` defaults to False, and is at the end of the parameter list

Functions that have a `bytealigned` parameter have changed so that it now
defaults to `False` rather than `True`. Also, its position in the parameter list
has changed to be at the end. You may need to recode slightly (sorry!)

* `readue` and `readse` functions have been removed

Instead you should use the new read function with a `'ue'` or `'se'` token:

```pycon
>>> i = s.readue()
```
becomes

```pycon
>>> i = s.read('ue')
```
This is more flexible as you can read multiple items in one go, plus you can
now also use the `peek` function with ue and se.

* Minor bugs fixed.

See the issue tracker for more details.

### June 15th 2009: version 0.4.3 for Python 2.x released

This is a minor update. This release is the first to bundle the bitstring
manual. This is a PDF and you can find it in the docs directory.

Changes in version 0.4.3

* New 'cut' function

This function returns a generator for constant sized chunks of a BitString.

```pycon
>>> for byte in s.cut(8):
...     do_something_with(byte)
```
You can also specify a `startbit` and `endbit`, as well as a `count`, which limits
the number of items generated:

```pycon
>>> first100TSPackets = list(s.cut(188*8, count=100))
```
* `slice` function now equivalent to `__getitem__`.

This means that a step can also be given to the `slice` function so that the
following are now the same thing, and it's just a personal preference which
to use:

```pycon
>>> s1 = s[a:b:c]
>>> s2 = s.slice(a, b, c)
```
* findall gets a 'count' parameter.

So now

```pycon
>>> list(a.findall(s, count=n))
```
is equivalent to

```pycon
>>> list(a.findall(s))[:n]
```
except that it won't need to generate the whole list and so is much more
efficient.

* Changes to 'split'.

The `split` function now has a 'count' parameter rather than 'maxsplit'. This
makes the interface closer to that for `cut`, `replace` and `findall`. The final item
generated is now no longer the whole of the rest of the `BitString`.

* A couple of minor bugs were fixed. See the issue tracker for details.

### May 25th 2009: version 0.4.2 for Python 2.x released

This is a minor update, and almost doesn't break compatibility with version
0.4.0, but with the slight exception of `findall()` returning a generator,
detailed below.

Changes in version 0.4.2

* Stepping in slices

The use of the step parameter (also known as the stride) in slices has been
added. Its use is a little non-standard as it effectively gives a multiplicative
factor to apply to the start and stop parameters, rather than skipping over
bits.

For example this makes it much more convenient if you want to give slices in
terms of bytes instead of bits. Instead of writing `s[a*8:b*8]` you can use
`s[a:b:8]`.

When using a step the BitString is effectively truncated to a multiple of the
step, so `s[::8]` is equal to `s` if `s` is an integer number of bytes, otherwise it
is truncated by up to 7 bits. So the final seven complete 16-bit words could be
written as `s[-7::16]`

Negative slices are also allowed, and should do what you'd expect. So for
example `s[::-1]` returns a bit-reversed copy of `s` (which is similar to
`s.reversebits()`, which does the same operation on `s` in-place). As another
example, to get the first 10 bytes in reverse byte order you could use
`s_bytereversed = s[0:10:-8]`.

* Removed restrictions on offset

You can now specify an offset of greater than 7 bits when creating a `BitString`,
and the use of offset is also now permitted when using the `filename` initialiser.
This is useful when you want to create a `BitString` from the middle of a file
without having to read the file into memory.

```pycon
>>> f = BitString(filename='reallybigfile', offset=8000000, length=32)
```
* Integers can be assigned to slices

You can now assign an integer to a slice of a `BitString`. If the integer doesn't
fit in the size of slice given then a `ValueError` exception is raised. So this
is now allowed and works as expected:

```pycon
>>> s[8:16] = 106
```
and is equivalent to

```pycon
>>> s[8:16] = BitString(uint=106, length=8)
```

* Fewer exceptions raised

Some changes have been made to slicing so that fewer exceptions are raised,
bringing the interface closer to that for lists. So for example trying to delete
past the end of the `BitString` will now just delete to the end, rather than
raising a `ValueError`.

* Initialisation from lists and tuples

A new option for the auto initialiser is to pass it a list or tuple. The items
in the list or tuple are evaluated as booleans and the bits in the `BitString` are
set to `1` for `True` items and `0` for `False` items. This can be used anywhere the
auto initialiser can currently be used. For example:

```pycon
>>> a = BitString([True, 7, False, 0, ()])     # 0b11000
>>> b = a + ['Yes', '']                        # Adds '0b10'
>>> (True, True, False) in a
True
```
#### Miscellany

* `reversebits()` now has optional `startbit` and `endbit` parameters.

* As an optimisation `findall()` will return a generator, rather than a list. If you
still want the whole list then of course you can just call `list()` on the
generator.

* Improved efficiency of rfind().

* A couple of minor bugs were fixed. See the issue tracker for details.

### April 23rd 2009: Python 3 only version 0.4.1 released

This version is just a port of version 0.4.0 to Python 3. All the unit tests
pass, but beyond that only limited ad hoc testing has been done and so it
should be considered an experimental release. That said, the unit test
coverage is very good - I'm just not sure if anyone even wants a Python 3
version!

### April 11th 2009: version 0.4.0 released

Changes in version 0.4.0

* New functions

Added `rfind()`, `findall()`, `replace()`. These do pretty much what you'd expect -
see the docstrings or the wiki for more information.

* More special functions

Some missing functions were added: `__repr__`, `__contains__`, `__rand__`,
`__ror__`, `__rxor__` and `__delitem__`.

* Miscellany

A couple of small bugs were fixed (see the issue tracker).

There are some small backward incompatibilities relative to version 0.3.2:

* Combined `find` and `findbytealigned`

`findbytealigned` has been removed, and becomes part of `find`. The default
start position has changed on both `find` and `split` to be the start of the
`BitString`. You may need to recode:

```pycon
>>> s1.find(bs)
>>> s2.findbytealigned(bs)
>>> s2.split(bs)
```
becomes

```pycon
>>> s1.find(bs, bytealigned=False, startbit=s1.bitpos)
>>> s2.find(bs, startbit=s1.bitpos)  # bytealigned defaults to True
>>> s2.split(bs, startbit=s2.bitpos)
```
* Reading off end of BitString no longer raises exception.

Previously a `read` or `peek` function that encountered the end of the `BitString`
would raise a `ValueError`. It will now instead return the remainder of the
`BitString`, which could be an empty `BitString`. This is closer to the file
object interface.

* Removed visibility of offset.

The `offset` property was previously read-only, and has now been removed from
public view altogether. As it is used internally for efficiency reasons you
shouldn't really have needed to use it. If you do then use the `_offset` parameter
instead (with caution).

### March 11th 2009: version 0.3.2 released

Changes in version 0.3.2

* Better performance

A number of functions (especially `find` and `findbytealigned`) have been sped
up considerably.

* Bit-wise operations

Added support for bit-wise AND (`&`), OR (`|`) and XOR (`^`). For example:

```pycon
>>> a = BitString('0b00111')
>>> print a & '0b10101'
0b00101
```
* Miscellany

Added `seekbit` and `seekbyte` functions. These complement the `advance` and
`retreat` functions, although you can still just use `bitpos` and `bytepos`
properties directly.

```pycon
>>> a.seekbit(100)                   # Equivalent to a.bitpos = 100
```
Allowed comparisons between `BitString` objects and strings. For example this
will now work:
```pycon
>>> a = BitString('0b00001111')
>>> a == '0x0f'
True
```
### February 26th 2009: version 0.3.1 released

Changes in version 0.3.1

This version only adds features and fixes bugs relative to 0.3.0, and doesn't
break backwards compatibility.

* Octal interpretation and initialisation

The oct property now joins bin and hex. Just prefix octal numbers with '0o'.

```pycon
>>> a = BitString('0o755')
>>> print a.bin
0b111101101
```
* Simpler copying

Rather than using `b = copy.copy(a)` to create a copy of a `BitString`, now you
can just use `b = BitString(a)`.

* More special methods

Lots of new special methods added, for example bit-shifting via `<<` and `>>`,
equality testing via `==` and `!=`, bit inversion (`~`) and concatenation using `*`.

Also `__setitem__` is now supported so `BitString` objects can be modified using
standard index notation.

* Proper installer

Finally got round to writing the distutils script. To install just
`python setup.py install`.

### February 15th 2009: version 0.3.0 released

Changes in version 0.3.0

* Simpler initialisation from binary and hexadecimal

The first argument in the BitString constructor is now called auto and will
attempt to interpret the type of a string. Prefix binary numbers with `'0b'`
and hexadecimals with `'0x'`.

```pycon
>>> a = BitString('0b0')         # single zero bit
>>> b = BitString('0xffff')      # two bytes
```
Previously the first argument was data, so if you relied on this then you
will need to recode:

```pycon
>>> a = BitString('\x00\x00\x01\xb3')   # Don't do this any more!
```
becomes

```pycon
>>> a = BitString(data='\x00\x00\x01\xb3')
```
or just

```pycon
>>> a = BitString('0x000001b3')
```
This new notation can also be used in functions that take a `BitString` as an
argument. For example:

```pycon
>>> a = BitString('0x0011') + '0xff'
>>> a.insert('0b001', 6)
>>> a.find('0b1111')
```
* BitString made more mutable

The functions `append`, `deletebits`, `insert`, `overwrite`, `truncatestart` and
`truncateend` now modify the `BitString` that they act upon. This allows for
cleaner and more efficient code, but you may need to rewrite slightly if you
depended upon the old behaviour:

```pycon
>>> a = BitString(hex='0xffff')
>>> a = a.append(BitString(hex='0x00'))
>>> b = a.deletebits(10, 10)
```
becomes:

```pycon
>>> a = BitString('0xffff')
>>> a.append('0x00')
>>> b = copy.copy(a)
>>> b.deletebits(10, 10)
```
Thanks to Frank Aune for suggestions in this and other areas.

* Changes to printing

The binary interpretation of a BitString is now prepended with `'0b'`. This is
in keeping with the Python 2.6 (and 3.0) bin function. The prefix is optional
when initialising using `bin=`.

Also, if you just print a `BitString` with no interpretation it will pick
something appropriate - hex if it is an integer number of bytes, otherwise
binary. If the BitString representation is very long it will be truncated
by '...' so it is only an approximate interpretation.

```pycon
>>> a = BitString('0b0011111')
>>> print a
0b0011111
>>> a += '0b0'
>>> print a
0x3e
```
* More convenience functions

Some missing functions such as `advancebit` and `deletebytes` have been added. Also
a number of peek functions make an appearance as have `prepend` and `reversebits`.
See the Tutorial for more details.

### January 13th 2009: version 0.2.0 released

Some fairly minor updates, not really deserving of a whole version point update.

## December 29th 2008: version 0.1.0 released

First release! :tada:
