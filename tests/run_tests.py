#!/usr/bin/env python3
"""
Test runner script for Unity Terrain Exporter plugin tests.

Usage:
    python tests/run_tests.py              # Run all tests
    python tests/run_tests.py -v           # Verbose output
    python tests/run_tests.py TestUTMDetection  # Run specific test class
"""

import sys
import os
import unittest

# Add the parent directory to the path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_tests():
    """Load all test cases."""
    # Discover and load all test modules
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    return suite


def main():
    """Run the test suite."""
    # Create test suite
    suite = load_tests()
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()

