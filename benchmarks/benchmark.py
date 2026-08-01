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


def to_list(a):
    """The Array's items as a list. 5.0 renamed tolist() to to_list()."""
    return a.to_list() if hasattr(a, "to_list") else a.tolist()


def reader(bits):
    """A sequential reader positioned at bit 0."""
    return _READER_CLS(bits)


# --- Workloads ---------------------------------------------------------------
#
# Each takes a scale factor and returns a checksum. Sizes are picked so a single
# repetition lands in roughly the 0.1-1s range on 5.0; 4.x is slower, so use
# --scale to shrink everything proportionally when iterating.


def cut_and_compare(scale):
    """Chop a long bitstring into 3-bit chunks and count matches (stress perf1)."""
    s = Bits("0xef1356a6200b3, 0b0") * int(6000 * scale)
    count = 0
    for triplet in s.cut(3):
        if triplet == "0b001":
            count += 1
    return count


def count_set_bits(scale):
    """Set a handful of bits in a large buffer and count them (stress perf2)."""
    length = int(100_000_000 * scale)
    total = 0
    # Repeated so the timing is well clear of timer noise on the faster core.
    for _ in range(20):
        s = mutable_zeros(length)
        # Positions scale with the buffer so --scale stays in range and the checksum holds.
        s.set(1, [0, length // 4, length // 2, length - 1])
        total += s.count(1)
    return total


def build_from_tokens(scale):
    """Parse format-string tokens repeatedly and join the results (stress perf3)."""
    parts = []
    for _ in range(int(20_000 * scale)):
        parts.append(Bits("u12=244, f32=0.4"))
        parts.append(Bits("0x3e44f, 0b11011, 0o75523"))
        parts.append(zeros(104))
    return len(Bits().join(parts))


def findall_patterns(scale):
    """Search a large random bitstring for bit patterns (stress perf4)."""
    random.seed(999)
    length = int(4_000_000 * scale)
    s = from_uint(random.randrange(0, 2 ** length), length)
    found = 0
    for pattern in ("0b11010010101", "0xabcdef1234", "0x4321"):
        found += len(list(s.findall(pattern)))
    return found


def bitwise_or(scale):
    """Tight loop of small bitwise ors, dominated by call overhead (stress perf6)."""
    a = zeros(64)
    b = Bits("0xf0f0f0f0f0f0f0f0")
    acc = 0
    for _ in range(int(200_000 * scale)):
        acc += len(a | b)
    return acc


def prime_sieve(scale):
    """Sieve of Eratosthenes over a bit buffer, then find twin primes (stress perf7)."""
    limit = int(1_000_000 * scale)
    is_prime = mutable_zeros(limit)
    is_prime.set(True)
    is_prime.set(False, [0, 1])
    for i in range(2, math.ceil(math.sqrt(limit))):
        if is_prime[i]:
            is_prime.set(False, range(i * i, limit, i))
    return len(list(is_prime.findall("0b101")))


def sequential_read(scale):
    """Read a buffer as a stream of 8-bit unsigned ints."""
    data = from_bytes(bytes(range(256)) * 200)
    total = 0
    for _ in range(int(5 * scale)):
        r = reader(data)
        for _ in range(len(data) // 8):
            total += r.read("u8")
    return total


def slicing(scale):
    """Take many overlapping slices out of a medium-sized bitstring."""
    s = Bits("0xef1356a6200b3, 0b0") * 1000
    length = len(s)
    total = 0
    for i in range(int(100_000 * scale)):
        start = (i * 37) % (length - 64)
        total += len(s[start:start + 64])
    return total


def array_ops(scale):
    """Build an Array of items and read them back, elementwise (stress perf3's cousin)."""
    values = [i % 200 for i in range(int(50_000 * scale))]
    a = bitstring.Array("u8", values)
    total = sum(to_list(a))
    total += sum(v for v in a)
    total += sum(to_list(a + 1))
    total += sum(to_list(a == 100))
    return total


def array_ops_fallback(scale):
    """As array_ops, but with a dtype that has no bulk equivalent in the core."""
    values = [0.5, 1.0, 2.0, 4.0] * int(1_000 * scale)
    a = bitstring.Array("e3m2mxfp", values)
    return sum(to_list(a)) + sum(v for v in a)


def pack_unpack(scale):
    """Round-trip values through a multi-token format string."""
    total = 0
    for i in range(int(20_000 * scale)):
        b = bitstring.pack("u8, i8, u16, f32", i % 200, -1, 1000, 0.5)
        values = b.unpack("u8, i8, u16, f32")
        total += values[0] + values[2]
    return total


def array_indexing(scale):
    """Read and write single Array elements, one at a time."""
    a = bitstring.Array("u8", [i % 200 for i in range(1_000)])
    total = 0
    for _ in range(int(20 * scale)):
        for i in range(0, 1_000, 10):
            total += a[i]
            a[i] = (a[i] + 1) % 200
    return total


WORKLOADS = [
    # (name, function, expected checksum at scale 1.0)
    ("cut_and_compare", cut_and_compare, 12000),
    ("count_set_bits", count_set_bits, 80),
    ("build_from_tokens", build_from_tokens, 3_760_000),
    ("findall_patterns", findall_patterns, 2054),
    ("bitwise_or", bitwise_or, 12_800_000),
    ("prime_sieve", prime_sieve, 8169),
    ("sequential_read", sequential_read, 32_640_000),
    ("slicing", slicing, 6_400_000),
    ("array_ops", array_ops, 14_975_250),
    ("array_ops_fallback", array_ops_fallback, 15_000.0),
    ("pack_unpack", pack_unpack, 21_990_000),
    ("array_indexing", array_indexing, 199_000),
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
