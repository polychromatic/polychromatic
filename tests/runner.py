#!/usr/bin/python3
#
# Unit test runner logic. Consider using ./run.sh instead.
#

import sys
import unittest

import internals
import effects
import fx
import middleman

loader = unittest.TestLoader()
suite  = unittest.TestSuite()

suite.addTests(loader.loadTestsFromModule(internals))
suite.addTests(loader.loadTestsFromModule(effects))
suite.addTests(loader.loadTestsFromModule(fx))
suite.addTests(loader.loadTestsFromModule(middleman))

# Initialize runner
runner = unittest.TextTestRunner()

if len(sys.argv) > 1:
    if sys.argv[1] == "--verbose":
        runner = unittest.TextTestRunner(verbosity=3)

result = runner.run(suite)

if result.wasSuccessful():
    sys.exit(0)

sys.exit(1)
