#!/usr/bin/env python

import unittest
import test_bitstring
import test_bitarray
import test_constbitarray
import test_constbitstream
import test_bitstream


for module in [test_bitstring, test_constbitarray, test_constbitstream,
               test_bitarray, test_bitstream]:
    print("Running {0}".format(module.__name__))
    try:
        unittest.main(module)
    except SystemExit:
        pass


