#!/usr/bin/env python
import sys
import os
sys.path.insert(0, 'test')
sys.path.insert(0, 'bitstring')

print("Running bitstring module unit tests:")
try:
    import test_bitstring
    test_bitstring.unittest.main(test_bitstring)
except ImportError:
    print("Error: cannot find test_bitstring.py")
