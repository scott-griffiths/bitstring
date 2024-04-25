#!/usr/bin/env python
import sys
sys.path.insert(0, '..')
from bitstring import Bits, BitStream
import bitstring
import time
import random
import cProfile
import pstats
import math
# Some performance tests. Each is a task - it is permissible to rewrite
# to do it in a different way.


# TEST 1: Create a bitstring, read every 3 bits and count how many equal '001'.
def perf1():
    s = bitstring.Bits('0xef1356a6200b3, 0b0')
    s *= 6000
    c = 0
    for triplet in s.cut(3):
        if triplet == '0b001':
            c += 1
    assert c == 12000, c


def perf2():
    s = bitstring.BitArray(100000000)
    s.set(1, [10, 100, 1000, 100000])
    count = s.count(1)
    assert count == 4
            
            
def perf3():
    s = bitstring.BitArray()
    for i in range(10000):
        s += 'uint:12=244, float:32=0.4'
        s += '0x3e44f, 0b11011, 0o75523'
        s += [0, 1, 2, 0, 0, 1, 2, 0, -1, 0, 'hello']
        s += bitstring.BitArray(104)


def perf4():
    random.seed(999)
    i = random.randrange(0, 2**20000000)
    s = bitstring.BitArray(uint=i, length=20000000)
    for ss in ['0b11010010101', '0xabcdef1234, 0b000101111010101010011010100100101010101', '0x4321']:
        x = len(list(s.findall(ss)))
    assert x == 289


def perf5():
    s = set()
    s2 = set()
    random.seed(12)
    for _ in range(20000):
        v = random.randint(0, 2**10)
        s.add(bitstring.ConstBitStream(uint=v, length=1001, pos=v % 1000))
        s2.add(v)
    assert len(s) == len(s2)


def perf6():
    random.seed(1414)
    i = random.randrange(0, 2 ** 800000)
    s = bitstring.ConstBitStream(uint=i, length=800000)
    for _ in range(800000 // 40):
        _ = s.readlist('uint:4, float:32, bool, bool, bool, bool')

def perf7():
    limit = 1000000
    is_prime = bitstring.BitArray(limit)
    is_prime.set(True)
    # Manually set 0 and 1 to be not prime.
    is_prime.set(False, [0, 1])
    # For every other integer, if it's set as prime then unset all of its multiples
    for i in range(2, math.ceil(math.sqrt(limit))):
        if is_prime[i]:
            is_prime.set(False, range(i*i, limit, i))
    twin_primes = len(list(is_prime.findall('0b101')))
    assert twin_primes == 8169

def run(f):
    start_time = time.perf_counter()
    print("Running {0}".format(str(f)))
    f()
    print("Took {0} s".format(time.perf_counter() - start_time))


def main():
    start_time = time.perf_counter()
    run(perf1)
    run(perf2)
    run(perf3)
    run(perf4)
    run(perf5)
    run(perf6)
    run(perf7)
    print("Total time {0} s".format(time.perf_counter() - start_time))


if __name__ == '__main__':
    print(f"bitstring version {bitstring.__version__}")
    cProfile.run('main()', 'stats')
    p = pstats.Stats('stats')
    p.sort_stats('time').print_stats(10)
