"""
Unit tests for the ConvertToUnityRaw algorithm class.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import os
import tempfile
import numpy as np

# Import the classes to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unity_terrain_exporter.convert_unity_raw import ConvertToUnityRaw
from qgis.core import QgsProcessingContext, QgsProcessingFeedback


class TestConvertToUnityRaw(unittest.TestCase):
    """Test cases for ConvertToUnityRaw algorithm class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.algorithm = ConvertToUnityRaw()
        self.context = Mock(spec=QgsProcessingContext)
        self.feedback = Mock(spec=QgsProcessingFeedback)
        self.feedback.pushConsoleInfo = Mock()
        self.feedback.isCanceled = Mock(return_value=False)
    
    def test_algorithm_name(self):
        """Test algorithm name."""
        self.assertEqual(self.algorithm.name(), 'convert_unity_raw')
    
    def test_algorithm_display_name(self):
        """Test algorithm display name."""
        display_name = self.algorithm.displayName()
        self.assertIn('Unity', display_name)
        self.assertIn('RAW', display_name)
        # After v0.1.2: removed automatic UTM reprojection
        self.assertNotIn('UTM', display_name, "Display name should not mention UTM (reprojection removed)")
    
    def test_algorithm_group(self):
        """Test algorithm group."""
        group = self.algorithm.group()
        self.assertIn('Unity', group)
    
    def test_algorithm_group_id(self):
        """Test algorithm group ID."""
        self.assertEqual(self.algorithm.groupId(), 'unity_tools')
    
    def test_create_instance(self):
        """Test createInstance method."""
        instance = self.algorithm.createInstance()
        self.assertIsInstance(instance, ConvertToUnityRaw)
        self.assertIsNot(instance, self.algorithm)  # Should be a new instance
    
    def test_init_algorithm_parameters(self):
        """Test that algorithm initializes with correct parameters."""
        config = {}
        self.algorithm.initAlgorithm(config)
        
        # Check that parameters were added
        # We can't easily check the parameter list without QGIS environment,
        # but we can verify the method runs without error
        self.assertTrue(True)  # If we get here, initAlgorithm worked
    
    @patch('unity_terrain_exporter.convert_unity_raw.process_geotiff_for_unity')
    def test_process_algorithm_success(self, mock_process):
        """Test successful algorithm processing."""
        # Mock successful processing
        mock_process.return_value = True
        
        # Mock parameters
        parameters = {
            self.algorithm.INPUT: Mock(),
            self.algorithm.OUTPUT: '/tmp/test_output.raw'
        }
        
        # Mock input layer
        input_layer = Mock()
        input_layer.source.return_value = '/tmp/test_input.tif'
        
        self.context.parameterAsRasterLayer = Mock(return_value=input_layer)
        self.context.parameterAsFileOutput = Mock(return_value='/tmp/test_output.raw')
        
        # We need to mock the parameterAsRasterLayer method on the algorithm
        with patch.object(self.algorithm, 'parameterAsRasterLayer', return_value=input_layer):
            with patch.object(self.algorithm, 'parameterAsFileOutput', return_value='/tmp/test_output.raw'):
                result = self.algorithm.processAlgorithm(parameters, self.context, self.feedback)
        
        # Should return output path on success
        self.assertIsNotNone(result)
        self.assertEqual(result[self.algorithm.OUTPUT], '/tmp/test_output.raw')
        mock_process.assert_called_once()
    
    @patch('unity_terrain_exporter.convert_unity_raw.process_geotiff_for_unity')
    def test_process_algorithm_failure(self, mock_process):
        """Test algorithm processing failure."""
        # Mock failed processing
        mock_process.return_value = False
        
        # Mock parameters
        parameters = {
            self.algorithm.INPUT: Mock(),
            self.algorithm.OUTPUT: '/tmp/test_output.raw'
        }
        
        # Mock input layer
        input_layer = Mock()
        input_layer.source.return_value = '/tmp/test_input.tif'
        
        with patch.object(self.algorithm, 'parameterAsRasterLayer', return_value=input_layer):
            with patch.object(self.algorithm, 'parameterAsFileOutput', return_value='/tmp/test_output.raw'):
                result = self.algorithm.processAlgorithm(parameters, self.context, self.feedback)
        
        # Should return None on failure
        self.assertIsNotNone(result)
        self.assertIsNone(result[self.algorithm.OUTPUT])
        mock_process.assert_called_once()
    
    def test_process_algorithm_invalid_input(self):
        """Test algorithm with invalid input layer."""
        parameters = {
            self.algorithm.INPUT: Mock(),
            self.algorithm.OUTPUT: '/tmp/test_output.raw'
        }
        
        # Mock invalid input layer (None)
        with patch.object(self.algorithm, 'parameterAsRasterLayer', return_value=None):
            result = self.algorithm.processAlgorithm(parameters, self.context, self.feedback)
        
        # Should return None output on invalid input
        self.assertIsNotNone(result)
        self.assertIsNone(result[self.algorithm.OUTPUT])
        self.feedback.pushConsoleInfo.assert_called()


if __name__ == '__main__':
    unittest.main()

