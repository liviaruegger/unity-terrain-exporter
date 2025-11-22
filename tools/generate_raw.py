#!/usr/bin/env python3
"""
Generate Unity .raw file from GeoTIFF.

This script generates a .raw file from a GeoTIFF using the plugin's processing logic.
The generated .raw file can then be visualized using visualize_raw.py.
"""

import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unity_terrain_exporter.convert_unity_raw import process_geotiff_for_unity
from qgis.core import QgsProcessingFeedback


class MockFeedback(QgsProcessingFeedback):
    """Mock feedback that captures log messages."""
    def __init__(self):
        self.messages = []
        self.min_height = None
        self.max_height = None
        self.variation = None
        self.width = None
        self.height = None
        self.terrain_size_x = None
        self.terrain_size_z = None
    
    def pushConsoleInfo(self, msg):
        self.messages.append(msg)
        print(msg)
        
        # Parse Unity Import Settings from log
        if "Resolution (Width/Height):" in msg:
            parts = msg.split(":")[1].strip().split("x")
            self.width = int(parts[0])
            self.height = int(parts[1])
        elif "  X:" in msg:
            # Parse "  X: 98710.00m" or "  X: 98710.00 (units may not be meters...)"
            x_str = msg.split(":")[1].strip().split()[0].replace("m", "")
            self.terrain_size_x = float(x_str)
        elif "  Y:" in msg:
            # Parse "  Y: 1209.00m"
            y_str = msg.split(":")[1].strip().split()[0].replace("m", "")
            self.variation = float(y_str)
        elif "  Z:" in msg:
            # Parse "  Z: 84500.00m" or "  Z: 84500.00 (units may not be meters...)"
            z_str = msg.split(":")[1].strip().split()[0].replace("m", "")
            self.terrain_size_z = float(z_str)
        elif "  Min Height:" in msg:
            self.min_height = float(msg.split(":")[1].strip().replace("m", ""))
        elif "  Max Height:" in msg:
            self.max_height = float(msg.split(":")[1].strip().replace("m", ""))
    
    def isCanceled(self):
        return False


def main():
    if len(sys.argv) < 3:
        print(f"\n❌ Error: Missing required arguments")
        print(f"\n💡 Usage:")
        print(f"   python3 {os.path.basename(__file__)} <input.tif> <output.raw>")
        print(f"\n📝 Example:")
        print(f"   python3 {os.path.basename(__file__)} terrain.tif terrain.raw")
        return 1
    
    input_tif = sys.argv[1]
    output_raw = sys.argv[2]
    
    if not os.path.exists(input_tif):
        print(f"❌ Error: Input file not found: {input_tif}")
        return 1
    
    print(f"\n{'='*70}")
    print(f"🔄 Generating .raw file from GeoTIFF...")
    print(f"{'='*70}")
    
    feedback = MockFeedback()
    success = process_geotiff_for_unity(input_tif, output_raw, feedback)
    
    if not success:
        print(f"\n❌ Error: Failed to generate .raw file")
        return 1
    
    # Check if we got all the values from the log
    if not all([feedback.width, feedback.height, feedback.min_height, feedback.max_height, feedback.variation]):
        print(f"\n⚠️  Warning: Could not parse all values from log")
        print(f"   Width: {feedback.width}, Height: {feedback.height}")
        print(f"   X: {feedback.terrain_size_x}, Z: {feedback.terrain_size_z}")
        print(f"   Min: {feedback.min_height}, Max: {feedback.max_height}, Variation: {feedback.variation}")
        print(f"   Using fallback values...")
        # Fallback: try to get from file
        from osgeo import gdal
        ds = gdal.Open(input_tif, gdal.GA_ReadOnly)
        if ds:
            feedback.width = ds.RasterXSize
            feedback.height = ds.RasterYSize
            ds = None
    
    if not all([feedback.width, feedback.height, feedback.min_height, feedback.max_height, feedback.variation]):
        print(f"\n⚠️  Warning: Some values missing, but .raw file was generated")
        print(f"   You may need to provide these manually for visualization:")
        print(f"   Width: {feedback.width}, Height: {feedback.height}")
        print(f"   X: {feedback.terrain_size_x}, Z: {feedback.terrain_size_z}")
        print(f"   Min: {feedback.min_height}, Max: {feedback.max_height}, Variation: {feedback.variation}")
    else:
        print(f"\n✓ .raw file generated successfully")
        print(f"   File: {output_raw}")
        print(f"   Resolution: {feedback.width}x{feedback.height}")
        print(f"   Terrain Size: X={feedback.terrain_size_x:.2f}m, Y={feedback.variation:.2f}m, Z={feedback.terrain_size_z:.2f}m")
        print(f"   Elevation: {feedback.min_height:.2f}m - {feedback.max_height:.2f}m")
        print(f"\n💡 To visualize, run:")
        print(f"   python3 visualize_raw.py {output_raw} {feedback.width} {feedback.height} {feedback.min_height:.2f} {feedback.max_height:.2f} {feedback.variation:.2f}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

