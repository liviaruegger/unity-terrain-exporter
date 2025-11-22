#!/usr/bin/env python3
"""
Visualize Unity .raw terrain file without Unity.

This script reads a .raw file and displays it as a heightmap,
similar to how Unity would render it.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def read_raw_file(filepath, width, height):
    """Read a Unity .raw file (16-bit unsigned integer, Little Endian)."""
    with open(filepath, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=np.uint16)
    
    if len(data) != width * height:
        raise ValueError(f"File size mismatch: expected {width * height} pixels, got {len(data)}")
    
    return data.reshape((height, width))


def visualize_raw(raw_path, width, height, min_elevation, max_elevation, variation,
                  save_images=True, show_3d=False):
    """
    Visualize the .raw file as a heightmap.
    
    Args:
        raw_path: Path to .raw file
        width, height: Image dimensions
        min_elevation, max_elevation, variation: Elevation parameters
        save_images: If True, save 4 separate high-res images
        show_3d: If True, show interactive 3D visualization
    """
    print(f"\n{'='*70}")
    print(f"🎨 Visualizing .raw file: {os.path.basename(raw_path)}")
    print(f"{'='*70}")
    
    # Read .raw file
    raw_data = read_raw_file(raw_path, width, height)
    
    # Convert to normalized (0.0 to 1.0)
    normalized = raw_data.astype(np.float32) / 65535.0
    
    # Convert to real-world elevation (meters)
    elevation = min_elevation + (normalized * variation)
    
    print(f"\n📊 Statistics:")
    print(f"   Raw values: {np.min(raw_data):,} - {np.max(raw_data):,}")
    print(f"   Elevation: {np.min(elevation):.2f}m - {np.max(elevation):.2f}m")
    print(f"   Mean elevation: {np.mean(elevation):.2f}m")
    
    base_name = raw_path.replace('.raw', '')
    
    # Pre-calculate variables needed for visualizations
    center_row = height // 2
    center_col = width // 2
    horizontal_profile = elevation[center_row, :]
    vertical_profile = elevation[:, center_col]
    
    # Downsample for 3D visualization (max 200x200 for performance)
    downsample = max(1, max(width, height) // 200)
    elevation_downsampled = elevation[::downsample, ::downsample]
    y_size, x_size = elevation_downsampled.shape
    x_coords = np.arange(0, width, downsample)[:x_size]
    y_coords = np.arange(0, height, downsample)[:y_size]
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Save individual high-res images
    if save_images:
        print(f"\n📸 Generating high-resolution images...")
        
        # 1. Heightmap (grayscale)
        print(f"   1/4: Heightmap (Grayscale)...")
        fig1, ax1 = plt.subplots(figsize=(12, 12))
        im1 = ax1.imshow(elevation, cmap='gray', aspect='equal', origin='upper')
        ax1.set_title(f'Heightmap (Grayscale)\nElevation: {min_elevation:.0f}m - {max_elevation:.0f}m (Range: {variation:.0f}m)', 
                      fontsize=14, fontweight='bold', pad=20)
        ax1.set_xlabel('Width (pixels)', fontsize=12)
        ax1.set_ylabel('Height (pixels)', fontsize=12)
        cbar1 = plt.colorbar(im1, ax=ax1, label='Elevation (m)', fraction=0.046, pad=0.04)
        cbar1.ax.tick_params(labelsize=10)
        plt.tight_layout()
        output1 = f"{base_name}_01_heightmap_grayscale.png"
        plt.savefig(output1, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig1)
        print(f"      ✓ Saved: {output1}")
        
        # 2. Heightmap (terrain colormap)
        print(f"   2/4: Heightmap (Terrain Colormap)...")
        fig2, ax2 = plt.subplots(figsize=(12, 12))
        im2 = ax2.imshow(elevation, cmap='terrain', aspect='equal', origin='upper')
        ax2.set_title(f'Heightmap (Terrain Colormap)\nElevation: {min_elevation:.0f}m - {max_elevation:.0f}m (Range: {variation:.0f}m)', 
                      fontsize=14, fontweight='bold', pad=20)
        ax2.set_xlabel('Width (pixels)', fontsize=12)
        ax2.set_ylabel('Height (pixels)', fontsize=12)
        cbar2 = plt.colorbar(im2, ax=ax2, label='Elevation (m)', fraction=0.046, pad=0.04)
        cbar2.ax.tick_params(labelsize=10)
        plt.tight_layout()
        output2 = f"{base_name}_02_heightmap_terrain.png"
        plt.savefig(output2, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig2)
        print(f"      ✓ Saved: {output2}")
        
        # 3. 3D Surface
        print(f"   3/4: 3D Surface View...")
        fig3 = plt.figure(figsize=(14, 10))
        ax3 = fig3.add_subplot(111, projection='3d')
        surf = ax3.plot_surface(X, Y, elevation_downsampled, cmap='terrain', 
                               linewidth=0, antialiased=True, alpha=0.9)
        ax3.set_title(f'3D Surface View\nElevation: {min_elevation:.0f}m - {max_elevation:.0f}m (Range: {variation:.0f}m)', 
                      fontsize=14, fontweight='bold', pad=20)
        ax3.set_xlabel('Width (pixels)', fontsize=11)
        ax3.set_ylabel('Height (pixels)', fontsize=11)
        ax3.set_zlabel('Elevation (m)', fontsize=11)
        cbar3 = plt.colorbar(surf, ax=ax3, label='Elevation (m)', shrink=0.6, pad=0.1)
        cbar3.ax.tick_params(labelsize=10)
        plt.tight_layout()
        output3 = f"{base_name}_03_3d_surface.png"
        plt.savefig(output3, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig3)
        print(f"      ✓ Saved: {output3}")
        
        # 4. Elevation profile
        print(f"   4/4: Elevation Profiles...")
        fig4, ax4 = plt.subplots(figsize=(12, 8))
        ax4.plot(horizontal_profile, label=f'Horizontal (row {center_row})', linewidth=2.5, alpha=0.8)
        ax4.plot(vertical_profile, label=f'Vertical (col {center_col})', linewidth=2.5, alpha=0.8)
        ax4.set_title(f'Elevation Profiles (Cross-sections through center)\nElevation Range: {min_elevation:.0f}m - {max_elevation:.0f}m', 
                      fontsize=14, fontweight='bold', pad=20)
        ax4.set_xlabel('Position (pixels)', fontsize=12)
        ax4.set_ylabel('Elevation (m)', fontsize=12)
        ax4.legend(fontsize=11, loc='best')
        ax4.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        output4 = f"{base_name}_04_elevation_profiles.png"
        plt.savefig(output4, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig4)
        print(f"      ✓ Saved: {output4}")
        
        print(f"\n💾 All images saved (300 DPI):")
        print(f"   1. {os.path.basename(output1)}")
        print(f"   2. {os.path.basename(output2)}")
        print(f"   3. {os.path.basename(output3)}")
        print(f"   4. {os.path.basename(output4)}")
        print(f"   Location: {os.path.dirname(os.path.abspath(output1))}")
    
    # Show interactive 3D visualization
    if show_3d:
        print(f"\n📺 Opening interactive 3D visualization...")
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X, Y, elevation_downsampled, cmap='terrain', 
                              linewidth=0, antialiased=True, alpha=0.9)
        ax.set_title(f'Interactive 3D Terrain Surface\nElevation: {min_elevation:.0f}m - {max_elevation:.0f}m (Range: {variation:.0f}m)', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Width (pixels)', fontsize=12)
        ax.set_ylabel('Height (pixels)', fontsize=12)
        ax.set_zlabel('Elevation (m)', fontsize=12)
        plt.colorbar(surf, ax=ax, label='Elevation (m)', shrink=0.6, pad=0.1)
        plt.tight_layout()
        print(f"   (You can rotate and zoom the 3D model. Close the window to continue)")
        plt.show()
    
    return elevation


def get_default_example():
    """Get path to default example.tif file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    example_path = os.path.join(script_dir, '..', 'samples', 'example.tif')
    return example_path if os.path.exists(example_path) else None


def main():
    # Check if we should use default example (no arguments)
    if len(sys.argv) < 2:
        example_path = get_default_example()
        if not example_path:
            print("❌ Error: Missing required arguments and example.tif not found")
            print("\n💡 Usage:")
            print("   python3 visualize_raw.py [raw_file] [width] [height] [min_elevation] [max_elevation] [variation] [options]")
            print("\n   Or use pipeline.py to convert and visualize automatically:")
            print("   python3 pipeline.py [input.tif]")
            return 1
        
        # Use pipeline to convert example.tif first
        print("💡 No arguments provided, using default: samples/example.tif")
        print("   Converting to .raw first...\n")
        
        import subprocess
        result = subprocess.run(
            [sys.executable, 'pipeline.py', example_path],
            cwd=os.path.dirname(__file__)
        )
        return result.returncode
    
    if len(sys.argv) < 6:
        print("❌ Error: Missing required arguments")
        print("\n💡 Usage:")
        print("   python3 visualize_raw.py <raw_file> <width> <height> <min_elevation> <max_elevation> <variation> [options]")
        print("\n📝 Example:")
        print("   python3 visualize_raw.py output.raw 2049 2049 881.0 2090.0 1209.0")
        print("\n💡 Options:")
        print("   --3d-only        Show only interactive 3D visualization (no images)")
        print("   --images-only    Save 4 high-res images only (no interactive window)")
        print("   (default)        Save images AND show interactive 3D")
        print("\n   Or use pipeline.py to convert and visualize automatically:")
        print("   python3 pipeline.py [input.tif]")
        return 1
    
    raw_path = sys.argv[1]
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    min_elevation = float(sys.argv[4])
    max_elevation = float(sys.argv[5])
    variation = float(sys.argv[6])
    
    # Parse options
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
    
    if not os.path.exists(raw_path):
        print(f"❌ Error: File not found: {raw_path}")
        return 1
    
    try:
        elevation = visualize_raw(raw_path, width, height, min_elevation, max_elevation, variation,
                                  save_images=save_images, show_3d=show_3d)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

