#!/usr/bin/env python3

import os
import unittest

if __name__ == "__main__":

    parent_dir = os.path.dirname(__file__)

    tests = unittest.TestLoader().discover(
        top_level_dir=parent_dir,
        start_dir=os.path.join(parent_dir, "svet"),
        pattern="*.py")

    unittest.runner.TextTestRunner(buffer=True).run(tests)
