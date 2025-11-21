# This file contains the main algorithm logic.
# This is where the actual DEM processing will happen.

# Python standard library imports
import sys
import os
import numpy as np
import math

# QGIS imports
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsProcessingFeedback,
)

# PyQt imports (use qgis.PyQt for QGIS compatibility)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

# GDAL/OSR imports (QGIS includes these)
from osgeo import gdal, osr

#
# --- Helper Function: UTM Zone Detection ---
#

def get_utm_epsg_code(dataset, feedback: QgsProcessingFeedback):
    """
    Calculates the correct UTM EPSG code for the center of the dataset.
    """
    try:
        # 1. Get the geotransform and source projection
        gt = dataset.GetGeoTransform()
        srs_origin = osr.SpatialReference(wkt=dataset.GetProjection())
        
        # 2. Calculate center pixel coordinate
        x_center_pixel = dataset.RasterXSize / 2
        y_center_pixel = dataset.RasterYSize / 2
        
        # 3. Convert center pixel to world coordinate (in original projection)
        x_center_world = gt[0] + (x_center_pixel * gt[1]) + (y_center_pixel * gt[2])
        y_center_world = gt[3] + (x_center_pixel * gt[4]) + (y_center_pixel * gt[5])

        # 4. Create transformation to WGS84 (EPSG:4326) to get lon/lat
        srs_wgs84 = osr.SpatialReference()
        srs_wgs84.ImportFromEPSG(4326)
        
        # 5. Ensure correct axis mapping (handles QGIS 3+ / GDAL 3+ changes)
        if int(gdal.__version__[0]) >= 3:
            srs_origin.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            srs_wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        transform = osr.CoordinateTransformation(srs_origin, srs_wgs84)
        
        # 6. Transform the point
        point = transform.TransformPoint(x_center_world, y_center_world)
        lon = point[0]
        lat = point[1]

        # 7. Calculate UTM zone
        # UTM zones are 1-60
        utm_zone = math.floor((lon + 180) / 6) + 1
        
        # 8. Determine hemisphere and base EPSG code
        # 32600 for Northern Hemisphere, 32700 for Southern
        if lat >= 0:
            epsg_code = 32600 + utm_zone
        else:
            epsg_code = 32700 + utm_zone
            
        feedback.pushConsoleInfo(f"Detected center Lon/Lat: ({lon:.2f}, {lat:.2f})")
        feedback.pushConsoleInfo(f"Auto-detected UTM EPSG code: {epsg_code} (Zone {utm_zone})")
        
        return f"EPSG:{epsg_code}"

    except Exception as e:
        feedback.pushConsoleInfo(f"Error in get_utm_epsg_code: {e}")
        return None

#
# --- Helper Function: Padding Detection ---
#

def detect_and_exclude_padding(data, mask, rows, cols):
    """
    Detects zero-value padding in image borders and excludes it from the mask.
    
    Padding typically appears in corners/edges after rotation or cropping.
    This function compares zero density in border regions vs center region.
    
    Args:
        data: numpy array of height values (float32)
        mask: boolean mask of valid pixels (already excludes NoData)
        rows: number of rows in the image
        cols: number of columns in the image
    
    Returns:
        tuple: (updated_mask, padding_detected)
            - updated_mask: boolean mask with padding zeros excluded
            - padding_detected: True if padding was detected and excluded
    """
    zero_mask = data == 0
    zero_count = zero_mask.sum()
    non_zero_count = (~zero_mask).sum()
    
    # If there are no zeros, or all pixels are zero, no padding to detect
    if zero_count == 0 or non_zero_count == 0:
        return mask, False
    
    # Define border region (outer 5% of each dimension)
    border_size = max(5, min(cols, rows) // 20)
    
    # Create border mask (all pixels within border_size from edges)
    border_mask = np.zeros_like(data, dtype=bool)
    border_mask[:border_size, :] = True  # top
    border_mask[-border_size:, :] = True  # bottom
    border_mask[:, :border_size] = True  # left
    border_mask[:, -border_size:] = True  # right
    
    # Define center region (inner 50% of each dimension)
    center_start = rows // 4
    center_end = 3 * rows // 4
    center_mask = np.zeros_like(data, dtype=bool)
    center_mask[center_start:center_end, center_start:center_end] = True
    
    # Calculate zero ratios
    border_zeros = np.sum(zero_mask & border_mask)
    border_total = np.sum(border_mask)
    border_zero_ratio = border_zeros / border_total if border_total > 0 else 0
    
    center_zeros = np.sum(zero_mask & center_mask)
    center_total = np.sum(center_mask)
    center_zero_ratio = center_zeros / center_total if center_total > 0 else 0
    
    # If border has significantly more zeros than center, likely padding
    # Threshold: border has >3x more zeros than center, AND border has >30% zeros
    if border_zero_ratio > 0.3 and (center_zero_ratio == 0 or border_zero_ratio > 3 * center_zero_ratio):
        # Exclude zeros from valid mask
        updated_mask = mask & ~zero_mask
        return updated_mask, True
    
    # No padding detected - zeros appear to be valid terrain (e.g., sea level)
    return mask, False


#
# --- Helper Function: Core Processing Logic ---
#

def process_geotiff_for_unity(input_path, output_raw_path, feedback: QgsProcessingFeedback):
    """
    Runs the full workflow:
    1. Square Crop (Center) - only if necessary
    2. Detect and exclude zero-value padding from borders (if present)
    3. Convert to 16-bit .raw with proper normalization
    
    Note: Input should be pre-reprojected to UTM projection for best results.
    The plugin assumes the input is already in the desired projection.
    """
    
    # Use GDAL's in-memory file system for intermediate files
    temp_cropped_path = f"/vsimem/{os.path.basename(input_path)}_cropped.tif"

    dataset = None
    cropped_ds = None

    try:
        # Enable GDAL exceptions for better debugging
        gdal.UseExceptions()
        
        # 0. Open the input file
        dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
        if not dataset:
            feedback.pushConsoleInfo(f"Error: Could not open input file {input_path}")
            return False

        feedback.pushConsoleInfo(f"--- Processing: {os.path.basename(input_path)} ---")

        # 1. CALCULATE SQUARE CROP (from center)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        min_dim = min(cols, rows)
        is_square = (cols == rows)
        
        if is_square:
            feedback.pushConsoleInfo(f"Image is already square ({cols}x{rows}). Skipping crop.")
            # Use the original dataset directly
            cropped_ds = dataset
            dataset = None  # Don't close it yet, cropped_ds references it
        else:
            # Calculate offset to crop from the center
            x_offset = (cols - min_dim) // 2
            y_offset = (rows - min_dim) // 2
            
            feedback.pushConsoleInfo(f"Original dimensions: {cols}x{rows}. Cropping to {min_dim}x{min_dim} from center.")

            # Execute the crop (gdal.Translate) to the in-memory file
            gdal.Translate(temp_cropped_path, 
                             dataset, 
                             srcWin=[x_offset, y_offset, min_dim, min_dim],
                             format="GTiff")
            
            # Close original dataset
            dataset = None 
            
            # Open the newly cropped dataset (from memory)
            cropped_ds = gdal.Open(temp_cropped_path, gdal.GA_ReadOnly)
        
        # 2. VALIDATE PROJECTION (Optional Warning)
        # Check if input is in UTM projection (informational only, non-blocking)
        current_srs = osr.SpatialReference(wkt=cropped_ds.GetProjection())
        srs_name = current_srs.GetName() if current_srs.GetName() else "Unknown"
        
        # Check if it's a UTM projection (EPSG codes 32601-32660 for North, 32701-32760 for South)
        is_utm = False
        if current_srs.GetAuthorityName(None) == "EPSG":
            epsg_code = current_srs.GetAuthorityCode(None)
            if epsg_code:
                epsg_num = int(epsg_code)
                # UTM Northern Hemisphere: 32601-32660, Southern Hemisphere: 32701-32760
                if (32601 <= epsg_num <= 32660) or (32701 <= epsg_num <= 32760):
                    is_utm = True
                    feedback.pushConsoleInfo(f"Input projection: {srs_name} (EPSG:{epsg_code}) - UTM detected ✓")
        
        if not is_utm:
            feedback.pushConsoleInfo(f"Warning: Input projection appears to be {srs_name} (not UTM).")
            feedback.pushConsoleInfo("For best results, reproject to UTM before using this plugin.")
            feedback.pushConsoleInfo("Processing will continue, but Unity import may require manual scaling.")

        # 3. CONVERT TO UNITY .RAW (16-BIT)
        band = cropped_ds.GetRasterBand(1)
        final_cols = cropped_ds.RasterXSize
        final_rows = cropped_ds.RasterYSize
        
        data = band.ReadAsArray().astype(np.float32)
        
        # Handle NoData values and calculate height range
        # Note: min_height may not be 0 if terrain starts above sea level
        nodata_value = band.GetNoDataValue()
        
        # Create initial mask for valid terrain pixels (exclude NoData)
        if nodata_value is not None:
            mask = data != nodata_value
        else:
            mask = np.ones_like(data, dtype=bool)
        
        # Detect and exclude zero-value padding from borders
        mask, padding_detected = detect_and_exclude_padding(data, mask, final_rows, final_cols)
        
        # Check if we have any valid pixels
        if not mask.any():
            feedback.pushConsoleInfo("Error: No valid terrain pixels found after filtering.")
            return False
        
        # Calculate min/max from valid terrain pixels only
        min_height = np.min(data[mask])
        max_height = np.max(data[mask])
        
        # Fill excluded pixels with minimum height to avoid gaps in output
        data[~mask] = min_height
        
        terrain_height_variation = max_height - min_height
        
        # Display padding info (if detected)
        if padding_detected:
            excluded_count = (~mask).sum()
            feedback.pushConsoleInfo(f"⚠ Padding detected in borders and excluded from height calculation ({excluded_count:,} pixels)")
        
        # Display Unity import settings
        feedback.pushConsoleInfo(f"\n--- Unity Import Settings ---")
        feedback.pushConsoleInfo(f"Resolution (Width/Height): {final_cols}x{final_rows}")
        feedback.pushConsoleInfo(f"Real-world Min Height: {min_height:.2f}m")
        feedback.pushConsoleInfo(f"Real-world Max Height: {max_height:.2f}m")
        feedback.pushConsoleInfo(f"Terrain Height (Variation): {terrain_height_variation:.2f}m")
        
        # Normalize (0.0 to 1.0) and scale (0 to 65535)
        # Unity expects: 0 = minimum height, 65535 = maximum height
        if max_height == min_height:
            data_uint16 = np.zeros_like(data, dtype=np.uint16)
        else:
            data_normalized = (data - min_height) / terrain_height_variation
            data_uint16 = (data_normalized * 65535).astype(np.uint16)
        
        # Ensure array is contiguous in memory (C-order, row-major)
        # This matches the .bil format: Band Interleaved by Line
        if not data_uint16.flags['C_CONTIGUOUS']:
            data_uint16 = np.ascontiguousarray(data_uint16, dtype=np.uint16)
            
        # Ensure Little Endian byte order (Windows/Unity default)
        # Unity import settings: Byte Order = "Windows" (Little Endian)
        if sys.byteorder == 'big':
            data_uint16.byteswap(inplace=True)

        # 4. SAVE THE FINAL .RAW FILE
        # Format: 16-bit unsigned integer, Little Endian, row-major (top-to-bottom)
        # No header - raw binary data only (same as .bil format)
        # Unity import: Depth = 16 bit, Byte Order = Windows, Resolution = width x height
        with open(output_raw_path, 'wb') as f:
            data_uint16.tofile(f)

        feedback.pushConsoleInfo(f"\n✓ SUCCESS! File saved to: {output_raw_path}")
        return True

    except Exception as e:
        feedback.pushConsoleInfo(f"Error: An error occurred during processing: {e}")
        return False
    
    finally:
        # 5. CLEANUP
        # Close datasets (if they are still open)
        dataset = None
        cropped_ds = None
        
        # Unlink the in-memory virtual files
        try:
            gdal.Unlink(temp_cropped_path)
        except: pass


#
# --- Main QGIS Algorithm Class ---
#

class ConvertToUnityRaw(QgsProcessingAlgorithm):
    """
    This is the main algorithm class.
    It converts a GeoTIFF to a Unity-compatible .raw file,
    applying a square crop (if necessary).
    
    Note: Input should be pre-reprojected to UTM projection for best results.
    """
    
    # --- Parameter Definitions ---
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        """
        Defines the algorithm's user interface (the parameters).
        """
        
        # 1. Input Raster Layer
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                # self.tr() marks this string for translation
                self.tr('Input Heightmap Layer (GeoTIFF)')
            )
        )
        
        # 2. Output .raw File Destination
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output .raw File'),
                self.tr('Unity RAW Files (*.raw)') # File filter
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        This is called when the user clicks "Run".
        """
        
        # 1. Get input/output file paths from parameters
        input_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if not input_layer:
            feedback.pushConsoleInfo(self.tr("Invalid input layer."))
            return {self.OUTPUT: None} # Return failure
            
        input_path = input_layer.source()
        output_path = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        # 2. Call our main processing function
        success = process_geotiff_for_unity(input_path, output_path, feedback)

        if success:
            # 3. Return the path to the output file on success
            return {self.OUTPUT: output_path}
        else:
            # 4. Return failure
            return {self.OUTPUT: None}

    # --- Boilerplate Metadata Methods ---
    
    def name(self):
        """
        Returns the unique algorithm ID (must not contain spaces).
        """
        return 'convert_unity_raw'

    def displayName(self):
        """
        Returns the human-readable name shown in the toolbox.
        """
        return self.tr('Convert to Unity RAW (Square)')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Unity Tools')

    def groupId(self):
        """
        Returns the unique ID of the group.
        """
        return 'unity_tools'

    def createInstance(self):
        """
        Required method to create a new instance of the class.
        """
        return ConvertToUnityRaw()
    
    def icon(self):
        """
        Returns the icon for the algorithm.
        """
        # Get the plugin directory (same directory as this file)
        plugin_dir = os.path.dirname(__file__)
        icon_path = os.path.join(plugin_dir, 'icon.png')
        
        # Return the icon if it exists, otherwise use default
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            return QgsProcessingAlgorithm.icon(self)

    def tr(self, string):
        """
        Returns a translated string for the algorithm.
        """
        return QCoreApplication.translate(self.__class__.__name__, string)