#!/usr/bin/env python3
"""
Interactive 3D visualization of Unity .raw terrain file.

This script opens only the 3D interactive view for exploring the terrain.
"""

import os
import sys

# Import from visualize_raw module
sys.path.insert(0, os.path.dirname(__file__))
from visualize_raw import read_raw_file, visualize_raw


def main():
    if len(sys.argv) < 6:
        print(f"\n❌ Error: Missing required arguments")
        print(f"\n💡 Usage:")
        print(f"   python3 {os.path.basename(__file__)} <raw_file> <width> <height> <min_elevation> <max_elevation> <variation>")
        print(f"\n📝 Example:")
        print(f"   python3 {os.path.basename(__file__)} output.raw 2049 2049 881.0 2090.0 1209.0")
        return 1
    
    raw_path = sys.argv[1]
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    min_elevation = float(sys.argv[4])
    max_elevation = float(sys.argv[5])
    variation = float(sys.argv[6])
    
    if not os.path.exists(raw_path):
        print(f"❌ Error: File not found: {raw_path}")
        return 1
    
    try:
        # Show only 3D interactive view
        visualize_raw(raw_path, width, height, min_elevation, max_elevation, variation,
                      save_images=False, show_interactive=True, show_3d_only=True)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

