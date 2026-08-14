# Performance opportunities, and what they need from tibs

Notes from profiling bitstring 5.0 against the raw tibs calls underneath. Numbers are
µs/op on a 256-byte operand (or 256-item Array), measured with `benchmarks/benchmark.py`
and ad-hoc timeit runs, best of three. They will drift; the ratios are the durable part.

The pattern that keeps paying off is the one behind the `Array` bulk work: find a tibs
call that does in one step what bitstring does in a Python loop. `Tibs` exposes 77
public methods and bitstring calls 37 of them, so there is still unexplored surface.

## Doable in bitstring today

These need no tibs change - the capability is already there and unused. All of the
originally listed items are now done:

- `unpack`/`read_list`/`pack` with several tokens - via `DtypeTuple`.
- `Array[i]` and `Array[i] = v` - via the cached `_tibs_dtype`.
- `Array.count(v)` - bulk read then `list.count`.
- `split(delimiter)` - `ConstBitStore.split_on` does one `find_all` plus one
  `split_at` (~5x; the mutable case keeps the find() loop, since the pieces
  would need copying into `Mutibs` anyway).
- `findall` - `find_all` collects every position in one call when no `count` is
  given (~9x on a list-consuming caller; `count=` stays on the lazy iterator).
- `Array[a:b] = values` - bulk pack via `from_values`, like `extend` (~90x on
  256 items).
- `Array[a:b]` - a lean clone that skips `__init__` (~1.7x).
- `Reader.read(fmt)` - a per-fmt cache of `(bitlength, tibs dtype)` feeding
  `to_value` directly, plus a fast path for integer fmts (sequential_read ~2x;
  the actual `to_u` was only ~4% of the old per-read cost).
- String promotion - `_create_from_bitstype` shares one immutable `Bits` per
  string, so comparing/searching against a string literal in a loop no longer
  allocates each time (cut_and_compare ~1.2x).

### The `chunks_iter` TODO was misplaced, and overstates the gain

`bits.py` carried `# TODO: Delegate to Tibs.chunks_iter` inside `split()`, which splits on
a *delimiter* - `chunks_iter` produces fixed-size chunks, so it belongs on `cut()` instead.
On `cut()` it is worth much less than it looks:

- `b.cut(8)` today: 119.8 µs
- `tb.chunks_iter(8)` raw: 21.4 µs
- `chunks_iter` plus the leanest possible wrap of each chunk into a `Bits`: 95.8 µs

So the achievable win is ~1.25x, not ~5x. Roughly 74 µs of the 96 is allocating 256
`Bits` wrappers, which no tibs change can remove while `cut()` yields `Bits` objects.
`split()` was the one actually worth rewriting, via `find_all` + `split_at` (see above).

## Wants from tibs

Ordered by value to bitstring.

### 1. The float formats bitstring implements in Python - done, tibs 2.0rc2

`DtypeKind` used to cover only Uint, Int, Float, Bool, Bytes, Bin, Hex, Oct, Bits, and
everything else in bitstring's register was implemented here in Python via lookup tables
in `fp8.py` and `mxfp.py`: `bfloat`/`bfloatbe`/`bfloatle`, `e2m1mxfp`, `e2m3mxfp`,
`e3m2mxfp`, `e4m3mxfp_saturate`, `e4m3mxfp_overflow`, `e5m2mxfp_saturate`,
`e5m2mxfp_overflow`, `e8m0mxfp`, `mxint`, `p3binary`, `p4binary`.

tibs 2.0rc2 added all of them (`bf16`, `binary8p3`/`binary8p4` and the `ocp_*` kinds), so
they're now in `_TIBS_EQUIVALENT_DTYPES` and on `Array`'s bulk path, and the three Python
modules are gone. Building a 10,000-item `e4m3mxfp_saturate` `Array` went from 26 ms to
0.2 ms, and reading one back from 7.5 ms to 0.4 ms. Packing also got more accurate: tibs
rounds once from the Python float where the lookup tables went via a float16 first.

`array_ops_fallback` in `benchmarks/benchmark.py` used to track this with `e3m2mxfp`; it
now uses `bits8`, which is the only fixed-length dtype left with no bulk equivalent in
the core. (It briefly used a scaled dtype instead, but the `Dtype` scale factor was
removed in 5.0.)

### 2. `Tibs`/`Mutibs` as acceptable base types - investigated, don't do it

The idea was that if `ConstBitStore` subclassed `Tibs`, the query methods (`__len__`,
`count`, `to_u`, `find`, `starts_with`) would become inherited C methods and the Python
pass-through frame - about 0.12 µs on every operation - would disappear. tibs already
uses `#[pyclass(subclass)]` on its own `Dtype`, so it looked like a one-word change.

It isn't, and there are good reasons the flag is absent:

- **`Mutibs` has `freelist = 8`, which PyO3 treats as incompatible with subclassing.**
  In pyo3 0.29, `free_with_freelist` is documented as requiring "a valid pointer to an
  instance of T (**not a subclass**)" and enforces it only with a `debug_assert_eq!`,
  which compiles out in release. `alloc_with_freelist` does guard itself, falling back to
  `PyType_GenericAlloc` when `subtype != self_type`, but the free side does not - a
  subclass instance would inherit `tp_free` and push its block onto a freelist that later
  hands it back as a plain `Mutibs`. So `Mutibs` would have to give up the freelist, which
  is exactly the optimisation its allocate/free churn wants. `Tibs` (frozen, sequence)
  has no freelist and doesn't hit this.
- **`subclass` on `Dtype` is a Rust-hierarchy mechanism, not an invitation.** It exists so
  `DtypeSingle`/`DtypeArray`/`DtypeTuple` can `extends = Dtype`. Every other type -
  `DtypeSingle`, `DtypeArray`, `DtypeTuple`, `Tibs`, `Mutibs`, `View` - is closed.
- **Python subclassing of these types doesn't work anyway.** `class MyDtype(Dtype)` then
  `MyDtype('u8')` returns a plain `DtypeSingle`: `Dtype.__new__` dispatches in Rust via
  `add_subclass(...)` and the Python subclass is silently discarded, so an overridden
  method never fires. `Tibs` would behave the same - `from_zeros`, `from_bytes` and every
  operator construct base instances in Rust.
- **It's a one-way API commitment.** `Py_TPFLAGS_BASETYPE` can't be withdrawn without
  breaking anyone who used it, and a Python subclass gets `__dict__`/`__weakref__`, so a
  `frozen` `Tibs` could carry mutable Python state - "the bits are immutable" rather than
  "the object is".

Even ignoring all that, the win was only ever partial: constructing methods return the
base type, so bitstring would have to reapply its wrapper to every result and would keep
the Python frame on precisely the operations that allocate.

### 3. Block-scaled MX formats

The MX formats are defined with a shared scale: k=32 elements of `e2m1`/`e2m3`/`e3m2`/
`e4m3`/`e5m2`/`mxint8` plus one E8M0 byte holding the scale for that block, all in the
data. bitstring has never had this. What it had until 5.0 was a `Dtype` scale factor - a
single Python float multiplier applied to a whole `Array`, out-of-band, with a
`scale='auto'` mode that picked one from the data. That was removed in 5.0, both because
it isn't what the specification describes and because keeping it would have left the name
`scale` meaning something different from the block scale when the real thing arrived.
So this is now the replacement, not an addition.

What bitstring needs:

- **Bulk pack and unpack over a whole buffer of blocks**, the `from_values`/`to_values`
  equivalent. The pack side has to choose each block's scale, which is the part that
  really wants to be in tibs: bitstring's old `'auto'` was a Python `floor(log2)`
  heuristic that saturated at `2**±127` and returned 1 for all-zero data, a case the
  specification doesn't cover.
- **Single-element access by index.** `Array.__getitem__` addresses elements, not blocks,
  so either an index-aware `to_value` or enough published layout (bits per block,
  elements per block) for bitstring to compute the offset and skip the scale bytes.
- **Read/write access to the block scales on their own**, for callers holding them
  out-of-band - a separate scale plane is a common tensor layout, and it's the one case
  the removed whole-`Array` multiplier genuinely served.

Two things this costs on the bitstring side, neither of them blocking. `_TIBS_EQUIVALENT_DTYPES`
is keyed name → `(DtypeKind, ByteOrder)` and would need a block size in the tuple. More
substantially, `Array.itemsize`, `__len__` and `trailing_bits` all assume a uniform
element size, and a block of 4-bit elements is 32×4 + 8 = 136 bits; block awareness there
is additive but it is real surgery, not just a new row in the map.

What it's worth, measured on a 10,000-item `e2m1mxfp` `Array` doing the scaling in Python
the way 5.0's documentation now recommends:

| operation | no scale | scaled in Python |
|-----------|---------:|-----------------:|
| pack      |  0.19 ms |          0.68 ms |
| unpack    |  0.25 ms |          1.08 ms |
| unpack, widening to `f64` | 0.25 ms | 1.58 ms |

So the arithmetic costs 3-6x the bulk conversion it wraps, and that is before the block
scales themselves are stored, chosen or read - all of which are currently not done at all.

New kinds are additive on the tibs side, so this needs a 2.x minor release, not a 3.0.

### 4. A count/limit on `find_all`

`findall(count=n)` wraps the tibs iterator in a Python generator purely to stop early.
`chunks_iter` already takes a `count`; `find_all`/`find_all_iter` taking one would remove
that wrapper.

### 5. Papercut: `bytes` dtype length units

`DtypeSingle` lengths are in bits for every kind, including `Bytes` - `DtypeSingle('bytes16')`
is two bytes. bitstring's own `bytes` dtype counts bytes (`multiplier=8`). Not a bug, but
it cost some time to find, and it is the one entry in `_TIBS_EQUIVALENT_DTYPES` where the
length passed to tibs is not bitstring's `length`. Anything that makes the unit explicit
in the API would help.

## Not worth pursuing

- **Removing the bitstore wrapper layer.** Priced at ~1.23x geometric mean across the
  benchmark suite (upper bound, assuming the layer's argument handling costs nothing to
  relocate), against a 190-reference refactor. See the crossing counts per workload.
- **`__new__` + attribute set instead of `type(self)(...)`** in the bitstore operators.
  Measured 1-3% on individual ops and nothing at workload level - inside the noise.
