# Performance opportunities, and what they need from tibs

Notes from profiling bitstring 5.0 against the raw tibs calls underneath. Numbers are
µs/op on a 256-byte operand (or 256-item Array), measured with `benchmarks/benchmark.py`
and ad-hoc timeit runs, best of three. They will drift; the ratios are the durable part.

The pattern that keeps paying off is the one behind the `Array` bulk work: find a tibs
call that does in one step what bitstring does in a Python loop. `Tibs` exposes 77
public methods and bitstring calls 37 of them, so there is still unexplored surface.

## Doable in bitstring today

These need no tibs change - the capability is already there and unused.

| opportunity | now | achievable | note |
|---|---|---|---|
| `unpack`/`read_list`/`pack` with several tokens | 7.6 µs (4 tokens) | 0.69 µs | `DtypeTuple.unpack`/`.pack` do the whole token list in one call |
| `Array[i]` single item | 1.58 µs | 0.11 µs | `Array` already caches `_tibs_dtype`; `DtypeSingle.unpack(tibs, start, end)` |
| `Array.count(v)` | 26.0 µs | 7.6 µs | currently `sum(i == value for i in self)`; bulk read then `list.count` |
| `split(delimiter)` | 32.6 µs | 9.9 µs | `find_all` for the positions, then `split_at(positions)` - both single calls |
| `findall` when the caller wants a list | 67.1 µs | 8.1 µs | `find_all` returns a list; bitstring only uses `find_all_iter` |

`Array.__setitem__` (6.6 µs) and `Array[a:b]` (5.1 µs) are also well off the floor and
would follow the same shape, though neither has been prototyped.

### The `chunks_iter` TODO is misplaced, and overstates the gain

`bits.py` carries `# TODO: Delegate to Tibs.chunks_iter` inside `split()`, which splits on
a *delimiter* - `chunks_iter` produces fixed-size chunks, so it belongs on `cut()` instead.
On `cut()` it is worth much less than it looks:

- `b.cut(8)` today: 119.8 µs
- `tb.chunks_iter(8)` raw: 21.4 µs
- `chunks_iter` plus the leanest possible wrap of each chunk into a `Bits`: 95.8 µs

So the achievable win is ~1.25x, not ~5x. Roughly 74 µs of the 96 is allocating 256
`Bits` wrappers, which no tibs change can remove while `cut()` yields `Bits` objects.
`split()` is the one actually worth rewriting, via `find_all` + `split_at` (see above).

## Wants from tibs

Ordered by value to bitstring.

### 1. The float formats bitstring implements in Python

`DtypeKind` covers Uint, Int, Float, Bool, Bytes, Bin, Hex, Oct, Bits. Everything else in
bitstring's register is implemented here in Python, via lookup tables in `fp8.py` and
`mxfp.py`: `bfloat`/`bfloatbe`/`bfloatle`, `e2m1mxfp`, `e2m3mxfp`, `e3m2mxfp`,
`e4m3mxfp_saturate`, `e4m3mxfp_overflow`, `e5m2mxfp_saturate`, `e5m2mxfp_overflow`,
`e8m0mxfp`, `mxint`, `p3binary`, `p4binary`.

Those are exactly the dtypes that miss `Array`'s bulk path and stay on the per-element
loop - roughly 2.3 µs per item-pass against 0.1 µs for a bulk-capable dtype, so about
20x. The `array_ops_fallback` workload in `benchmarks/benchmark.py` tracks this: if tibs
grows any of these kinds, add the name to `_TIBS_EQUIVALENT_DTYPES` in `bitstore.py` and
that workload should drop to match `array_ops`.

This is the single largest tibs-side win available.

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

### 3. A count/limit on `find_all`

`findall(count=n)` wraps the tibs iterator in a Python generator purely to stop early.
`chunks_iter` already takes a `count`; `find_all`/`find_all_iter` taking one would remove
that wrapper.

### 4. Papercut: `bytes` dtype length units

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
