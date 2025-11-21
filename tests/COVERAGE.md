# Code Coverage Report

## Current Coverage Status

As of the latest test run, the code coverage is:

```
Name                                          Stmts   Miss Branch BrPart   Cover   Missing
------------------------------------------------------------------------------------------
unity_terrain_exporter/__init__.py               13     11      0      0  15.38%   12-34
unity_terrain_exporter/convert_unity_raw.py     150     66     24      2  51.72%   51->55, 69, 108-228
unity_terrain_exporter/main_provider.py          13     13      0      0   0.00%   4-38
------------------------------------------------------------------------------------------
TOTAL                                           176     90     24      2  46.00%
```

## Coverage Notes

### Why Some Code Has Low Coverage

1. **`__init__.py` (15.38%)**: The `classFactory()` function requires a QGIS environment to test properly, as it needs the `iface` parameter from QGIS.

2. **`main_provider.py` (0%)**: The provider class methods are called by QGIS's processing framework. Testing these requires a full QGIS environment or complex mocking of QGIS internals.

3. **`convert_unity_raw.py` (51.72%)**: 
   - The core logic functions (normalization, etc.) are well tested
   - The `get_utm_epsg_code` function is tested but no longer used in the main workflow (v0.1.2+ removed automatic reprojection)
   - The main processing function (`process_geotiff_for_unity`) has lower coverage because:
     - It requires actual GDAL datasets to test fully
     - File I/O operations are difficult to test without real files
     - GDAL operations (Translate) need real data

### Improving Coverage

Future work for improving coverage may include:

1. **Integration Tests**: Add tests that run within a QGIS environment
2. **Test Data**: Create small test GeoTIFF files for processing tests
3. **Mock GDAL**: More sophisticated GDAL mocks for file operations
4. **QGIS Mocking**: Mock QGIS's processing framework for provider tests

### Running Coverage

```bash
# Quick summary
make coverage-summary

# Full report
make coverage

# HTML report (visual)
make coverage-html
```

The HTML report provides line-by-line coverage information, making it easy to identify untested code paths.

## Configuration File

Coverage settings are stored in `setup.cfg` (standard Python configuration file format). This format is better recognized by IDEs and avoids syntax highlighting issues.

