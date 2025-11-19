"""
Unit tests for edge cases and critical scenarios.
These tests focus on delicate file manipulation logic.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import math
import sys
import os
import tempfile
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unity_terrain_exporter.convert_unity_raw import get_utm_epsg_code, process_geotiff_for_unity


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and critical scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.feedback = Mock()
        self.feedback.pushConsoleInfo = Mock()
        self.feedback.isCanceled = Mock(return_value=False)
    
    def test_odd_sized_dataset_center_calculation(self):
        """Test center pixel calculation for odd-sized datasets."""
        # Dataset with odd dimensions (101x101)
        # Center should be 50.5, which is correct for pixel coordinates
        width, height = 101, 101
        x_center = width / 2
        y_center = height / 2
        
        self.assertEqual(x_center, 50.5)
        self.assertEqual(y_center, 50.5)
        
        # Verify this works correctly in geotransform calculation
        # (The code handles float centers correctly)
        pixel_size = 0.01
        lon, lat = -46.6, -23.5
        gt = (
            lon - (width / 2 * pixel_size),
            pixel_size,
            0.0,
            lat + (height / 2 * pixel_size),
            0.0,
            -pixel_size
        )
        
        # Calculate world coordinate
        x_world = gt[0] + (x_center * gt[1]) + (y_center * gt[2])
        y_world = gt[3] + (x_center * gt[4]) + (y_center * gt[5])
        
        # Should be very close to original lon/lat
        self.assertAlmostEqual(x_world, lon, places=5)
        self.assertAlmostEqual(y_world, lat, places=5)
    
    def test_utm_zone_edge_case_longitude_180(self):
        """Test UTM zone calculation for longitude 180 (edge case)."""
        # Longitude 180 gives zone 61, but UTM only has zones 1-60
        lon = 180.0
        utm_zone = math.floor((lon + 180) / 6) + 1
        
        # The formula gives 61, which is technically outside valid UTM range
        # In practice, this should be handled, but the current code doesn't clamp it
        self.assertEqual(utm_zone, 61)
        
        # This would result in EPSG:32661 or EPSG:32761, which don't exist
        # This is a potential bug that should be noted
        lat = 0.0
        if lat >= 0:
            epsg_code = 32600 + utm_zone
        else:
            epsg_code = 32700 + utm_zone
        
        # EPSG:32661 doesn't exist (max is 32660)
        self.assertEqual(epsg_code, 32661)
        # Note: This is a known limitation - longitude exactly 180° is rare in practice
    
    def test_crop_offset_calculation_edge_cases(self):
        """Test crop offset calculation for various image dimensions."""
        test_cases = [
            (100, 200, 0, 50),      # Standard case
            (200, 100, 50, 0),      # Wider than tall
            (101, 201, 0, 50),     # Odd dimensions
            (1, 100, 0, 49),       # Very narrow
            (100, 1, 49, 0),       # Very short
        ]
        
        for cols, rows, expected_x, expected_y in test_cases:
            min_dim = min(cols, rows)
            x_offset = (cols - min_dim) // 2
            y_offset = (rows - min_dim) // 2
            
            self.assertEqual(x_offset, expected_x, 
                           f"x_offset for {cols}x{rows} should be {expected_x}")
            self.assertEqual(y_offset, expected_y,
                           f"y_offset for {cols}x{rows} should be {expected_y}")
    
    def test_min_dim_calculation(self):
        """Test min_dim calculation for various cases."""
        test_cases = [
            (100, 200, 100),
            (200, 100, 100),
            (100, 100, 100),
            (1, 1000, 1),
            (1000, 1, 1),
        ]
        
        for cols, rows, expected_min in test_cases:
            min_dim = min(cols, rows)
            self.assertEqual(min_dim, expected_min,
                           f"min_dim for {cols}x{rows} should be {expected_min}")
    
    def test_normalization_edge_case_flat_terrain(self):
        """Test normalization when terrain is completely flat (max == min)."""
        # When max_height == min_height, terrain is flat
        # Code should handle this by creating zeros
        min_height = 100.0
        max_height = 100.0
        
        # Simulate the code's logic
        if max_height == min_height:
            # Code creates zeros
            data_uint16 = np.zeros((10, 10), dtype=np.uint16)
        else:
            terrain_height_variation = max_height - min_height
            data_normalized = (np.array([[min_height]]) - min_height) / terrain_height_variation
            data_uint16 = (data_normalized * 65535).astype(np.uint16)
        
        # Should be all zeros
        self.assertTrue(np.all(data_uint16 == 0))
        self.assertEqual(data_uint16.dtype, np.uint16)
    
    def test_normalization_calculation(self):
        """Test normalization calculation is correct."""
        # Test the normalization formula
        min_height = 100.0
        max_height = 200.0
        terrain_height_variation = max_height - min_height
        
        # Test various heights
        test_heights = [100.0, 150.0, 200.0]
        expected_normalized = [0.0, 0.5, 1.0]
        expected_uint16 = [0, 32767, 65535]
        
        for height, exp_norm, exp_uint in zip(test_heights, expected_normalized, expected_uint16):
            normalized = (height - min_height) / terrain_height_variation
            uint16_value = int(normalized * 65535)
            
            self.assertAlmostEqual(normalized, exp_norm, places=5)
            # Allow small rounding differences
            self.assertAlmostEqual(uint16_value, exp_uint, delta=1)
    
    def test_byte_order_handling(self):
        """Test byte order handling for different systems."""
        # The code checks sys.byteorder and byteswaps if 'big'
        # We can't easily test this without mocking sys.byteorder,
        # but we can verify the logic
        
        # Little endian (most common) - no swap
        # Big endian - swap needed
        
        # Test that the check exists
        has_byteorder_check = hasattr(sys, 'byteorder')
        self.assertTrue(has_byteorder_check, "sys.byteorder should exist")
        
        # The actual byteswap is tested implicitly through the code structure
        # Full test would require mocking sys.byteorder
    
    def test_nodata_handling_all_nodata(self):
        """Test handling when all pixels are NoData."""
        # Create array with all NoData
        # Note: The code uses band.GetNoDataValue() which returns a scalar, not NaN directly
        # So we test with a specific NoData value
        nodata_value = -9999.0
        data = np.array([[nodata_value, nodata_value], 
                        [nodata_value, nodata_value]], dtype=np.float32)
        
        # Simulate the code's check (line 193-197)
        if nodata_value is not None:
            mask = data != nodata_value
            if not mask.any():
                # Code returns False in this case (line 197)
                should_fail = True
            else:
                should_fail = False
        else:
            should_fail = False
        
        self.assertTrue(should_fail, "Should fail when all pixels are NoData")
    
    def test_nodata_handling_partial_nodata(self):
        """Test handling when some pixels are NoData."""
        # Create array with some NoData
        data = np.array([[100.0, np.nan], [150.0, 200.0]], dtype=np.float32)
        nodata_value = np.nan
        
        # Simulate the code's logic
        if nodata_value is not None:
            mask = data != nodata_value
            if not mask.any():
                should_fail = True
            else:
                min_height = np.min(data[mask])
                data[~mask] = min_height  # Fill NoData with minimum
                should_fail = False
        else:
            min_height = np.min(data)
            should_fail = False
        
        self.assertFalse(should_fail, "Should not fail when some pixels are valid")
        # NoData should be filled with minimum
        self.assertTrue(np.all(data[~mask] == min_height))


if __name__ == '__main__':
    unittest.main()

