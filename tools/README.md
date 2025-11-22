# Development Tools

Tools for generating and visualizing Unity terrain `.raw` files without Unity.

## Quick Start

**🚀 Complete Pipeline (Recommended):**
```bash
# Uses samples/example.tif by default
make pipeline

# Or specify a file
make pipeline FILE=../samples/terrain.tif

# Options:
make pipeline OPTIONS=--3d-only        # Only interactive 3D
make pipeline OPTIONS=--images-only    # Only export 4 images
```

## How to Use

### 1. Visualize Interactive 3D

**Option A: Using pipeline (recommended - auto-converts)**
```bash
# Uses example.tif, converts to .raw, shows 3D
make pipeline OPTIONS=--3d-only

# Or with Python:
python3 pipeline.py --3d-only
```

**Option B: Direct visualization (if .raw already exists)**
```bash
python3 visualize_raw.py example.raw 1025 1025 946.0 1344.0 398.0 --3d-only
```

### 2. Export 4 Separate Images

**Option A: Using pipeline (recommended - auto-converts)**
```bash
# Uses example.tif, converts to .raw, exports 4 images
make pipeline OPTIONS=--images-only

# Or with Python:
python3 pipeline.py --images-only
```

**Option B: Direct visualization (if .raw already exists)**
```bash
python3 visualize_raw.py example.raw 1025 1025 946.0 1344.0 398.0 --images-only
```

## Scripts

### `pipeline.py` ⭐ **Recommended**
Complete pipeline: converts GeoTIFF to `.raw` and visualizes it automatically.

**Default behavior:** Uses `samples/example.tif` if no file specified.

```bash
# Uses example.tif by default
python3 pipeline.py

# Specify a file
python3 pipeline.py ../samples/terrain.tif

# Options:
python3 pipeline.py --3d-only        # Only interactive 3D
python3 pipeline.py --images-only   # Only export 4 images
python3 pipeline.py                 # Both (default)
```

### `visualize_raw.py`
Visualizes an existing `.raw` file.

**Default behavior:** If no arguments, uses `pipeline.py` with `example.tif`.

```bash
# Uses example.tif (converts first)
python3 visualize_raw.py

# Direct visualization
python3 visualize_raw.py <raw_file> <width> <height> <min_elevation> <max_elevation> <variation> [options]

# Options:
python3 visualize_raw.py file.raw 1025 1025 946.0 1344.0 398.0 --3d-only
python3 visualize_raw.py file.raw 1025 1025 946.0 1344.0 398.0 --images-only
```

### `visualize_3d.py`
Opens only the 3D interactive visualization (no images saved).

```bash
python3 visualize_3d.py <raw_file> <width> <height> <min_elevation> <max_elevation> <variation>
```

### `generate_raw.py`
Generates a `.raw` file from a GeoTIFF (without visualization).

```bash
python3 generate_raw.py <input.tif> <output.raw>
```

## Using Makefile

### Complete Pipeline
```bash
# Uses example.tif by default
make pipeline

# With options
make pipeline OPTIONS=--3d-only
make pipeline OPTIONS=--images-only

# With custom file
make pipeline FILE=../samples/terrain.tif
```

### Interactive 3D Only
```bash
# Uses example.tif (converts first)
make visualize-3d

# Or with existing .raw file
make visualize-3d FILE=example.raw WIDTH=1025 HEIGHT=1025 MIN=946.0 MAX=1344.0 VAR=398.0
```

### Export Images Only
```bash
# Uses example.tif (converts first)
make visualize-images

# Or with existing .raw file
make visualize-images FILE=example.raw WIDTH=1025 HEIGHT=1025 MIN=946.0 MAX=1344.0 VAR=398.0
```

## Output

When exporting images, the following files are generated (300 DPI, high resolution):

- `*_01_heightmap_grayscale.png` - Grayscale heightmap (how Unity sees it)
- `*_02_heightmap_terrain.png` - Terrain colormap (more intuitive)
- `*_03_3d_surface.png` - 3D surface view
- `*_04_elevation_profiles.png` - Elevation cross-sections

## Requirements

- Python 3.x
- numpy
- matplotlib
- GDAL (for generate_raw.py and pipeline.py)
- QGIS Python bindings (for generate_raw.py and pipeline.py)
