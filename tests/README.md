# Tests

This directory contains unit tests for the Unity Terrain Exporter plugin.

## Running Tests

### Using the test runner script:

```bash
# Run all tests
python tests/run_tests.py

# Verbose output
python tests/run_tests.py -v

# Run specific test class
python -m unittest tests.test_utm_detection.TestUTMDetection
```

### Using unittest directly:

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_utm_detection

# Run with verbose output
python -m unittest discover tests -v
```

## Test Structure

- `test_utm_detection.py` - Tests for UTM zone detection functionality (5 tests)
- `test_algorithm.py` - Tests for the ConvertToUnityRaw algorithm class (9 tests)
- `test_processing.py` - Tests for the main processing function logic (3 tests)
- `test_edge_cases.py` - Tests for edge cases and critical scenarios (9 tests)

**Total: 26 tests**

## Test Requirements

The tests use Python's built-in `unittest` framework and `unittest.mock` for mocking.

Some tests may require:
- GDAL/OGR libraries (for processing tests)
- QGIS Python bindings (for algorithm tests)
- Test data files (GeoTIFF files for integration tests)

## Coverage Analysis

Code coverage analysis is available using `coverage.py`. This helps identify which parts of the code are tested.

### Using Makefile:

```bash
# Run tests with coverage report
make coverage

# Generate HTML coverage report
make coverage-html

# Quick coverage summary
make coverage-summary
```

### Using coverage directly:

```bash
# Run tests with coverage
coverage run --source=unity_terrain_exporter -m unittest discover tests

# View coverage report
coverage report -m

# Generate HTML report
coverage html

# Open HTML report (Linux/Mac)
xdg-open htmlcov/index.html  # or open htmlcov/index.html on Mac
```

### Coverage Configuration

Coverage settings are configured in `setup.cfg` (under `[coverage:*]` sections):
- Measures coverage for `unity_terrain_exporter` package
- Excludes test files and cache directories
- Enables branch coverage for more thorough analysis
- Generates HTML reports in `htmlcov/` directory

## Note

Some tests use mocks to avoid requiring actual QGIS/GDAL environments. For full integration testing, you may need to run tests within a QGIS environment or use Docker containers with QGIS installed.

