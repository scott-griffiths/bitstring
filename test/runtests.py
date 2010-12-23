#!/usr/bin/env python

import sys
import os
import unittest
import test_bitstring
import test_bitarray
import test_constbitarray
import test_constbitstream
import test_bitstream

print("Running bitstring tests")
unittest.main(test_bitstring, exit=False)
print("Running constbitarray tests")
unittest.main(test_constbitarray, exit=False)
print("Running constbitstream tests")
unittest.main(test_constbitstream, exit=False)
print("Running bitarray tests")
unittest.main(test_bitarray, exit=False)
print("Running bitstream tests")
unittest.main(test_bitstream, exit=False)
