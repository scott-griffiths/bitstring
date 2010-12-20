#!/usr/bin/env python

import sys
import os
import unittest
import test_bitstring
import test_bitarray
import test_constbitarray

print("Running constbitarray tests")
unittest.main(test_constbitarray, exit=False)
print("Running bitarray tests")
unittest.main(test_bitarray, exit=False)
print("Running bitstream tests")
unittest.main(test_bitstream, exit=False)
