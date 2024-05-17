import sys
sys.path.insert(0, '..')
import bitstring
import random
import math


def test_cutting(benchmark):
    def cut():
        s = bitstring.Bits('0xef1356a6200b3, 0b0')
        s *= 6000
        c = 0
        for triplet in s.cut(3):
            if triplet == '0b001':
                c += 1
        return c
    c = benchmark(cut)
    assert c == 12000, c

def test_count(benchmark):
    def count():
        s = bitstring.BitArray(100000000)
        s.set(1, [10, 100, 1000, 10000000])
        return s.count(1)
    c = benchmark(count)
    assert c == 4

def test_token_parsing(benchmark):
    def token_parsing():
        s = bitstring.BitArray()
        for i in range(10000):
            s += 'uint:12=244, float:32=0.4'
            s += '0x3e44f, 0b11011, 0o75523'
            s += [0, 1, 2, 0, 0, 1, 2, 0, -1, 0, 'hello']
            s += bitstring.BitArray(104)
    benchmark(token_parsing)

def test_findall(benchmark):
    def finding():
        random.seed(999)
        i = random.randrange(0, 2 ** 20000000)
        s = bitstring.BitArray(uint=i, length=20000000)
        for ss in ['0b11010010101', '0xabcdef1234, 0b000101111010101010011010100100101010101', '0x4321']:
            x = len(list(s.findall(ss)))
        return x
    c = benchmark(finding)
    assert c == 289

def test_repeated_reading(benchmark):
    def repeating_reading():
        random.seed(1414)
        i = random.randrange(0, 2 ** 800000)
        s = bitstring.ConstBitStream(uint=i, length=800000)
        for _ in range(800000 // 40):
            _ = s.readlist('uint:4, float:32, bool, bool, bool, bool')
    benchmark(repeating_reading)

def test_primes(benchmark):
    def primes():
        limit = 1000000
        is_prime = bitstring.BitArray(limit)
        is_prime.set(True)
        # Manually set 0 and 1 to be not prime.
        is_prime.set(False, [0, 1])
        # For every other integer, if it's set as prime then unset all of its multiples
        for i in range(2, math.ceil(math.sqrt(limit))):
            if is_prime[i]:
                is_prime.set(False, range(i * i, limit, i))
        twin_primes = len(list(is_prime.findall('0b101')))
        return twin_primes
    c = benchmark(primes)
    assert c == 8169
