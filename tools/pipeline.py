#!/usr/bin/env python3
"""
Complete pipeline: Convert GeoTIFF to .raw and visualize it.

This script:
1. Converts a GeoTIFF to Unity .raw format
2. Automatically extracts parameters from the conversion log
3. Visualizes the result (interactive 3D + saved images)
"""

import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unity_terrain_exporter.convert_unity_raw import process_geotiff_for_unity
from qgis.core import QgsProcessingFeedback
from generate_raw import MockFeedback
import re
from visualize_raw import visualize_raw


def get_default_example():
    """Get path to default example.tif file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    example_path = os.path.join(script_dir, '..', 'samples', 'example.tif')
    return example_path if os.path.exists(example_path) else None


def main():
    # Parse options first (before determining input file)
    if '--3d-only' in sys.argv:
        save_images = False
        show_3d = True
    elif '--images-only' in sys.argv:
        save_images = True
        show_3d = False
    else:
        # Default: both
        save_images = True
        show_3d = True
    
    # Filter out options to find file arguments
    file_args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    # Default to example.tif if no file provided
    if len(file_args) == 0:
        example_path = get_default_example()
        if example_path:
            print(f"\n💡 No file specified, using default: samples/example.tif")
            input_tif = example_path
        else:
            print(f"\n❌ Error: Missing required argument and example.tif not found")
            print(f"\n💡 Usage:")
            print(f"   python3 {os.path.basename(__file__)} [input.tif] [output.raw] [options]")
            print(f"\n📝 Examples:")
            print(f"   python3 {os.path.basename(__file__)}                    # Uses samples/example.tif")
            print(f"   python3 {os.path.basename(__file__)} terrain.tif")
            print(f"   python3 {os.path.basename(__file__)} --3d-only          # Uses example.tif, 3D only")
            print(f"   python3 {os.path.basename(__file__)} --images-only     # Uses example.tif, images only")
            return 1
    else:
        input_tif = file_args[0]
    
    # Determine output path
    output_raw = file_args[1] if len(file_args) > 1 else None
    
    if output_raw is None:
        # Auto-generate output name
        base_name = os.path.splitext(os.path.basename(input_tif))[0]
        output_raw = f"{base_name}.raw"
    
    if not os.path.exists(input_tif):
        print(f"❌ Error: Input file not found: {input_tif}")
        return 1
    
    print(f"\n{'='*70}")
    print(f"🚀 Pipeline: Convert + Visualize")
    print(f"{'='*70}")
    print(f"Input:  {input_tif}")
    print(f"Output: {output_raw}")
    print(f"{'='*70}\n")
    
    # Step 1: Generate .raw file
    print(f"📦 Step 1/2: Converting GeoTIFF to .raw...")
    print(f"{'-'*70}")
    
    feedback = MockFeedback()
    success = process_geotiff_for_unity(input_tif, output_raw, feedback)
    
    if not success:
        print(f"\n❌ Error: Failed to generate .raw file")
        return 1
    
    # Check if we got all the values from the log
    # If variation is missing, calculate it from min/max
    if feedback.variation is None and feedback.min_height is not None and feedback.max_height is not None:
        feedback.variation = feedback.max_height - feedback.min_height
        print(f"\n💡 Calculated variation from min/max: {feedback.variation:.2f}m")
    
    # Debug: show what we parsed
    print(f"\n📋 Parsed values:")
    print(f"   Width: {feedback.width}, Height: {feedback.height}")
    print(f"   X: {feedback.terrain_size_x}, Z: {feedback.terrain_size_z}")
    print(f"   Min: {feedback.min_height}, Max: {feedback.max_height}, Variation: {feedback.variation}")
    
    # Check if all required values are present (check for None, not falsy values)
    required_values = {
        'width': feedback.width,
        'height': feedback.height,
        'min_height': feedback.min_height,
        'max_height': feedback.max_height,
        'variation': feedback.variation
    }
    
    missing = [k for k, v in required_values.items() if v is None]
    if missing:
        print(f"\n❌ Error: Could not parse all required values from conversion log")
        print(f"   Missing: {', '.join(missing)}")
        print(f"\n   The .raw file was generated, but visualization requires these values.")
        print(f"   Please check the log above and run visualize_raw.py manually.")
        return 1
    
    print(f"\n✓ Conversion complete!")
    print(f"   Resolution: {feedback.width}x{feedback.height}")
    print(f"   Terrain Size: X={feedback.terrain_size_x:.2f}m, Y={feedback.variation:.2f}m, Z={feedback.terrain_size_z:.2f}m")
    print(f"   Elevation: {feedback.min_height:.2f}m - {feedback.max_height:.2f}m")
    
    # Step 2: Visualize
    print(f"\n{'='*70}")
    print(f"🎨 Step 2/2: Visualizing .raw file...")
    print(f"{'-'*70}")
    
    try:
        visualize_raw(
            output_raw,
            feedback.width,
            feedback.height,
            feedback.min_height,
            feedback.max_height,
            feedback.variation,
            save_images=save_images,
            show_3d=show_3d
        )
        print(f"\n✓ Visualization complete!")
        print(f"   File: {output_raw}")
        if save_images:
            print(f"   ✓ 4 high-res images saved (300 DPI)")
        if show_3d:
            print(f"   ✓ 3D interactive view displayed")
    except Exception as e:
        print(f"\n❌ Error during visualization: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

