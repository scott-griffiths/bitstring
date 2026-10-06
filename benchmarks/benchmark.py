#!/usr/bin/env python3
"""Version-neutral benchmarks for bitstring.

Runs unchanged on both the 4.x line and 5.0, so the same workloads can be timed
against each version and the results compared. Workloads are adapted from the
older tests/stress.py script and tests/test_benchmarks.py.

Nothing here imports from the repository directly - plain `import bitstring` is
used, so whichever bitstring is first on sys.path gets measured. The resolved
path is printed in the header so it is always clear what was timed. There are no
third-party dependencies, which keeps the 4.x side installable in a bare venv.

Typical use:

    # in a 5.0 environment
    python benchmarks/benchmark.py --json new.json
    # in a 4.x environment
    python benchmarks/benchmark.py --json old.json
    # then, in either
    python benchmarks/benchmark.py --compare old.json new.json

Every workload returns a checksum value that is asserted against a constant, so
a version that quietly does less work fails rather than looking fast.
"""

import argparse
import functools
import json
import math
import platform
import random
import sys
import time

import bitstring
from bitstring import Bits, BitArray


# --- Compatibility shims -----------------------------------------------------
#
# Feature detection rather than version parsing: 5.0 added the from_* factories
# and replaced ConstBitStream with Reader, but the workloads themselves only
# need "give me N zero bits" and "give me a sequential reader".

_HAS_FACTORIES = hasattr(Bits, "from_zeros")
_READER_CLS = getattr(bitstring, "Reader", None) or getattr(bitstring, "ConstBitStream")


def zeros(length):
    """An immutable all-zeros bitstring of the given length."""
    return Bits.from_zeros(length) if _HAS_FACTORIES else Bits(length)


def mutable_zeros(length):
    """A mutable all-zeros bitstring of the given length."""
    return BitArray.from_zeros(length) if _HAS_FACTORIES else BitArray(length)


def from_uint(value, length):
    """A mutable bitstring holding `value` as an unsigned int of `length` bits.

    The `uint=`/`length=` keyword form is accepted by both lines; in 5.0 `uint`
    is a compatibility alias for `u`.
    """
    return BitArray(uint=value, length=length)


def from_bytes(data):
    """An immutable bitstring wrapping the given bytes."""
    return Bits.from_bytes(data) if _HAS_FACTORIES else Bits(bytes=data)


@functools.lru_cache(maxsize=None)
def random_bytes(nbytes, seed):
    """Deterministic random bytes, cached so generating them isn't timed after the first repeat."""
    return random.Random(seed).randbytes(nbytes)


def to_list(a):
    """The Array's items as a list. 5.0 renamed tolist() to to_list()."""
    return a.to_list() if hasattr(a, "to_list") else a.tolist()


def reader(bits):
    """A sequential reader positioned at bit 0."""
    return _READER_CLS(bits)


def read_value(r, fmt):
    """Read and interpret one dtype, whatever the reader class calls it."""
    return r.read_value(fmt) if _HAS_FACTORIES else r.read(fmt)


def read_list(r, fmt):
    """Read and interpret a comma-separated list of dtypes."""
    return r.read_list(fmt) if _HAS_FACTORIES else r.readlist(fmt)


def insert(a, pos, bs):
    """Insert into a BitArray. 5.0 swapped the argument order to match list.insert."""
    if _HAS_FACTORIES:
        a.insert(pos, bs)
    else:
        a.insert(bs, pos)


def find(s, pattern):
    """First match position or None. 4.x returned (pos,) or ()."""
    result = s.find(pattern)
    if isinstance(result, tuple):
        return result[0] if result else None
    return result


def rfind(s, pattern):
    """Last match position or None."""
    result = s.rfind(pattern)
    if isinstance(result, tuple):
        return result[0] if result else None
    return result


# --- Workloads ---------------------------------------------------------------
#
# Each takes a scale factor and returns a checksum. Sizes are picked so a single
# repetition lands in roughly the 0.02-0.1s range on 5.0; 4.x is slower, so use
# --scale to shrink everything proportionally when iterating.
#
# The set aims to cover what people actually do with the library, roughly in
# proportion: lots of small objects (creating, interpreting, slicing, packing),
# whole-buffer work on large ones (searching, counting, bitwise, editing), and
# sequential parsing. Random data comes from random_bytes() so the timed region
# measures bitstring rather than input generation.


# Creating and interpreting small bitstrings - per-call overhead dominates.

def create_small(scale):
    """Create small bitstrings from the common initialisers."""
    total = 0
    for i in range(int(25_000 * scale)):
        total += len(Bits("0xdeadbeef"))
        total += len(Bits("0b1011"))
        total += len(from_bytes(b"\x01\x02\x03"))
        total += len(Bits(uint=i % 256, length=8))
    return total


def interpret_small(scale):
    """Interpret 32-bit fields sliced from a buffer as int, float, hex and bytes."""
    buf = from_bytes(random_bytes(4096, 11))
    limit = len(buf) - 32
    total = 0
    for i in range(int(25_000 * scale)):
        field = buf[(i * 13) % limit:(i * 13) % limit + 32]
        total += field.u + field.i + len(field.hex) + len(field.bytes)
        total += field.f == field.f  # False for NaNs, so the checksum is exact
    return total


def build_from_tokens(scale):
    """Parse format-string tokens repeatedly and join the results (stress perf3)."""
    parts = []
    for _ in range(int(40_000 * scale)):
        parts.append(Bits("u12=244, f32=0.4"))
        parts.append(Bits("0x3e44f, 0b11011, 0o75523"))
        parts.append(zeros(104))
    return len(Bits().join(parts))


def pack_unpack(scale):
    """Round-trip values through a multi-token format string."""
    total = 0
    for i in range(int(40_000 * scale)):
        b = bitstring.pack("u8, i8, u16, f32", i % 200, -1, 1000, 0.5)
        values = b.unpack("u8, i8, u16, f32")
        total += values[0] + values[2]
    return total


def slicing(scale):
    """Take many overlapping slices out of a medium-sized bitstring."""
    s = Bits("0xef1356a6200b3, 0b0") * 1000
    length = len(s)
    total = 0
    for i in range(int(200_000 * scale)):
        start = (i * 37) % (length - 64)
        total += len(s[start:start + 64])
    return total


def cut_and_compare(scale):
    """Chop a long bitstring into 3-bit chunks and count matches (stress perf1)."""
    s = Bits("0xef1356a6200b3, 0b0") * int(12_000 * scale)
    count = 0
    for triplet in s.cut(3):
        if triplet == "0b001":
            count += 1
    return count


def bitwise_or(scale):
    """Tight loop of small bitwise ors, dominated by call overhead (stress perf6)."""
    a = zeros(64)
    b = Bits("0xf0f0f0f0f0f0f0f0")
    acc = 0
    for _ in range(int(200_000 * scale)):
        acc += len(a | b)
    return acc


# Whole-buffer operations on large bitstrings - the core's own speed dominates.

def findall_patterns(scale):
    """Search a large random bitstring for bit patterns, forwards and backwards (stress perf4)."""
    s = from_bytes(random_bytes(int(4_000_000 * scale), 999))
    found = 0
    for pattern in ("0b11010010101", "0xabcdef", "0x4321"):
        found += len(list(s.findall(pattern)))
    for pattern in ("0b1101001010111", "0xabcdef", "0x1234567890"):
        pos = find(s, pattern)
        found += -1 if pos is None else pos % 1000
        pos = rfind(s, pattern)
        found += -1 if pos is None else pos % 1000
    return found


def count_set_bits(scale):
    """Count bits in a large random buffer, both byte-aligned and not (stress perf2)."""
    s = from_bytes(random_bytes(int(32_000_000 * scale), 22))
    total = 0
    for _ in range(25):
        total += s.count(1)
        total += s[3:-5].count(0)
    return total


def bitwise_large(scale):
    """And, or, xor, invert and shift whole multi-megabyte bitstrings."""
    a = from_bytes(random_bytes(int(16_000_000 * scale), 33))
    b = from_bytes(random_bytes(int(16_000_000 * scale), 44))
    total = 0
    for _ in range(10):
        c = (a & b) ^ (~a | b)
        total += len(c << 3) + len(a >> 5)
    return total + c[:64].u


def edit_inplace(scale):
    """Flip and set single bits in a BitArray, then reverse, byteswap, shift, rotate and replace."""
    a = BitArray(from_bytes(random_bytes(int(250_000 * scale), 55)))
    for i in range(int(50_000 * scale)):
        a.invert(i)
        a[i * 3] = 1
    a.set(0, range(0, len(a), 7))
    a.reverse()
    a.byteswap(4)
    a <<= 3
    a.rol(5)
    replaced = a.replace("0b1111", "0b0000")
    return a.count(1) + replaced


def grow_and_splice(scale):
    """Append, prepend, delete and insert on a BitArray that changes length."""
    a = BitArray()
    for _ in range(int(40_000 * scale)):
        a.append("0b101")
        a.append("0xff")
    for _ in range(int(2_000 * scale)):
        a.prepend("0x1")
    for i in range(int(10_000 * scale)):
        del a[i:i + 8]
        insert(a, i, "0xf0")
    return len(a) + a.count(1)


def prime_sieve(scale):
    """Sieve of Eratosthenes over a bit buffer, then find twin primes (stress perf7)."""
    limit = int(10_000_000 * scale)
    is_prime = mutable_zeros(limit)
    is_prime.set(True)
    is_prime.set(False, [0, 1])
    for i in range(2, math.ceil(math.sqrt(limit))):
        if is_prime[i]:
            is_prime.set(False, range(i * i, limit, i))
    return len(list(is_prime.findall("0b101")))


# Sequential reading.

def sequential_read(scale):
    """Read a buffer as a stream of 8-bit unsigned ints."""
    data = from_bytes(bytes(range(256)) * 200)
    total = 0
    for _ in range(int(5 * scale)):
        r = reader(data)
        for _ in range(len(data) // 8):
            total += read_value(r, "u8")
    return total


def read_mixed(scale):
    """Parse unaligned records of mixed dtypes, as when decoding a binary format."""
    data = from_bytes(random_bytes(int(400_000 * scale), 66))
    record = "u3, i7, bool, f32, hex8, bin2"  # 61 bits, so nothing stays byte-aligned
    r = reader(data)
    total = 0
    while r.pos + 61 + 13 <= len(data):
        values = read_list(r, record)
        total += values[0] + values[1] + values[2] + len(values[4]) + len(values[5])
        total += read_value(r, "i13")
    return total


# Arrays.

def array_ops(scale):
    """Build an Array of items and read them back, elementwise (stress perf3's cousin)."""
    values = [i % 200 for i in range(int(200_000 * scale))]
    a = bitstring.Array("u8", values)
    total = sum(to_list(a))
    total += sum(v for v in a)
    total += sum(to_list(a + 1))
    total += sum(to_list(a == 100))
    return total


def array_ops_fallback(scale):
    """As array_ops, but with a dtype that has no bulk equivalent in the core.

    'bits' is what keeps this off the fast path - it's the only fixed-length dtype
    the core can't pack or unpack in bulk, so every item goes through the per-element
    Python path. e3m2mxfp used to qualify too, but the core gained the narrow float
    formats in 5.0.
    """
    values = [Bits(uint=i % 200, length=8) for i in range(int(20_000 * scale))]
    a = bitstring.Array("bits8", values)
    return sum(b.uint for b in to_list(a)) + sum(b.uint for b in a)


def array_indexing(scale):
    """Read and write single Array elements, one at a time."""
    a = bitstring.Array("u8", [i % 200 for i in range(1_000)])
    total = 0
    for _ in range(int(200 * scale)):
        for i in range(0, 1_000, 10):
            total += a[i]
            a[i] = (a[i] + 1) % 200
    return total


WORKLOADS = [
    # (name, function, expected checksum at scale 1.0)
    ("create_small", create_small, 1_700_000),
    ("interpret_small", interpret_small, 54_018_861_503_372),
    ("build_from_tokens", build_from_tokens, 7_520_000),
    ("pack_unpack", pack_unpack, 43_980_000),
    ("slicing", slicing, 12_800_000),
    ("cut_and_compare", cut_and_compare, 24_000),
    ("bitwise_or", bitwise_or, 12_800_000),
    ("findall_patterns", findall_patterns, 17_917),
    ("count_set_bits", count_set_bits, 6_399_999_875),
    ("bitwise_large", bitwise_large, 14_408_420_857_279_000_277),
    ("edit_inplace", edit_inplace, 744_212),
    ("grow_and_splice", grow_and_splice, 856_179),
    ("prime_sieve", prime_sieve, 58_980),
    ("sequential_read", sequential_read, 32_640_000),
    ("read_mixed", read_mixed, -519_629),
    ("array_ops", array_ops, 59_901_000),
    ("array_ops_fallback", array_ops_fallback, 3_980_000),
    ("array_indexing", array_indexing, 1_990_000),
]


# --- Runner ------------------------------------------------------------------


def run_one(func, scale, repeat):
    """Time `func` `repeat` times, returning (timings, checksum)."""
    timings = []
    result = None
    for _ in range(repeat):
        start = time.perf_counter()
        result = func(scale)
        timings.append(time.perf_counter() - start)
    return timings, result


def environment():
    return {
        "bitstring_version": bitstring.__version__,
        "bitstring_path": bitstring.__file__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def run(selected, scale, repeat, verbose):
    env = environment()
    print("bitstring {0} from {1}".format(env["bitstring_version"], env["bitstring_path"]))
    print("Python {0} on {1}".format(env["python_version"], env["platform"]))
    print("scale={0}  repeat={1}\n".format(scale, repeat))
    print("{0:<20} {1:>10} {2:>10} {3:>10}".format("workload", "best (s)", "median", "worst"))
    print("-" * 52)

    results = {}
    for name, func, expected in WORKLOADS:
        if selected and name not in selected:
            continue
        try:
            timings, checksum = run_one(func, scale, repeat)
        except Exception as exc:  # a workload may not be supported on some version
            print("{0:<20} {1}: {2}".format(name, type(exc).__name__, exc))
            results[name] = {"error": "{0}: {1}".format(type(exc).__name__, exc)}
            continue

        if expected is not None and scale == 1.0 and checksum != expected:
            print("{0:<20} CHECKSUM MISMATCH: got {1}, expected {2}".format(name, checksum, expected))
            results[name] = {"error": "checksum {0} != {1}".format(checksum, expected)}
            continue

        ordered = sorted(timings)
        best = ordered[0]
        median = ordered[len(ordered) // 2]
        worst = ordered[-1]
        results[name] = {
            "best": best,
            "median": median,
            "worst": worst,
            "timings": timings,
            "checksum": checksum,
        }
        print("{0:<20} {1:>10.4f} {2:>10.4f} {3:>10.4f}".format(name, best, median, worst))
        if verbose:
            print("    checksum={0} timings={1}".format(checksum, ["%.4f" % t for t in timings]))

    total = sum(r["best"] for r in results.values() if "best" in r)
    print("-" * 52)
    print("{0:<20} {1:>10.4f}".format("total (best)", total))
    return {"environment": env, "scale": scale, "repeat": repeat, "results": results}


def compare(old_path, new_path):
    with open(old_path) as f:
        old = json.load(f)
    with open(new_path) as f:
        new = json.load(f)

    print("old: bitstring {0}  (scale={1})".format(old["environment"]["bitstring_version"], old["scale"]))
    print("new: bitstring {0}  (scale={1})".format(new["environment"]["bitstring_version"], new["scale"]))
    if old["scale"] != new["scale"]:
        print("WARNING: scales differ - the two runs did different amounts of work.")
    print()
    print("{0:<20} {1:>12} {2:>12} {3:>10}".format("workload", "old (s)", "new (s)", "speedup"))
    print("-" * 56)

    speedups = []
    for name in old["results"]:
        o = old["results"].get(name, {})
        n = new["results"].get(name, {})
        if "best" not in o or "best" not in n:
            reason = o.get("error") or n.get("error") or "missing"
            print("{0:<20} {1}".format(name, reason))
            continue
        speedup = o["best"] / n["best"]
        speedups.append(speedup)
        print("{0:<20} {1:>12.4f} {2:>12.4f} {3:>9.2f}x".format(name, o["best"], n["best"], speedup))

    print("-" * 56)
    if speedups:
        geomean = math.exp(sum(math.log(s) for s in speedups) / len(speedups))
        print("{0:<20} {1:>36.2f}x".format("geometric mean", geomean))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scale", type=float, default=1.0,
                        help="scale all workload sizes (default 1.0; use e.g. 0.1 on slower versions)")
    parser.add_argument("--repeat", type=int, default=5, help="repetitions per workload (default 5)")
    parser.add_argument("--only", action="append", default=[],
                        help="run only the named workload; repeatable")
    parser.add_argument("--list", action="store_true", help="list workload names and exit")
    parser.add_argument("--json", metavar="PATH", help="write results to PATH as JSON")
    parser.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"),
                        help="compare two saved JSON result files and exit")
    parser.add_argument("--verbose", action="store_true", help="show checksums and every timing")
    args = parser.parse_args()

    if args.compare:
        compare(*args.compare)
        return 0

    if args.list:
        for name, _, _ in WORKLOADS:
            print(name)
        return 0

    known = {name for name, _, _ in WORKLOADS}
    unknown = set(args.only) - known
    if unknown:
        parser.error("unknown workload(s): {0}".format(", ".join(sorted(unknown))))

    data = run(set(args.only), args.scale, args.repeat, args.verbose)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(data, f, indent=2)
        print("\nWrote {0}".format(args.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
