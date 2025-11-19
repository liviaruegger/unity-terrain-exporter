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
# --- Helper Function: Core Processing Logic ---
#

def process_geotiff_for_unity(input_path, output_raw_path, feedback: QgsProcessingFeedback):
    """
    Runs the full workflow:
    1. Square Crop (Center)
    2. Reproject to UTM (Auto-Detect)
    3. Convert to 16-bit .raw
    """
    
    # Use GDAL's in-memory file system for intermediate files
    temp_cropped_path = f"/vsimem/{os.path.basename(input_path)}_cropped.tif"
    temp_warped_path = f"/vsimem/{os.path.basename(input_path)}_warped.tif"

    dataset = None
    cropped_ds = None
    warped_ds = None

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
        
        # 2. REPROJECT TO UTM (Auto-Detect)
        
        # Detect the correct UTM EPSG code
        target_srs_utm = get_utm_epsg_code(cropped_ds, feedback)
        if not target_srs_utm:
            feedback.pushConsoleInfo("Failed to auto-detect UTM zone.")
            return False
        
        # Check if already in the target UTM projection
        current_srs = osr.SpatialReference(wkt=cropped_ds.GetProjection())
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(int(target_srs_utm.split(':')[1]))
        
        # Compare projections (check if they represent the same coordinate system)
        if current_srs.IsSame(target_srs):
            feedback.pushConsoleInfo(f"Image is already in {target_srs_utm}. Skipping reprojection.")
            warped_ds = cropped_ds
            cropped_ds = None  # Don't close it, warped_ds references it
        else:
            feedback.pushConsoleInfo(f"Reprojecting to {target_srs_utm}...")
            
            # Execute the reprojection (gdal.Warp) to another in-memory file
            # Use 'Bilinear' for height data resampling
            warped_ds = gdal.Warp(temp_warped_path,
                                   cropped_ds,
                                   dstSRS=target_srs_utm,
                                   resampleAlg=gdal.GRA_Bilinear,
                                   format="GTiff")
            
            # Close cropped dataset after Warp is complete
            # (Warp has already read all data, so it's safe to close)
            cropped_ds = None

        # 3. CONVERT TO UNITY .RAW (16-BIT)
        feedback.pushConsoleInfo("Starting conversion to 16-bit .raw...")

        band = warped_ds.GetRasterBand(1)
        final_cols = warped_ds.RasterXSize
        final_rows = warped_ds.RasterYSize
        
        feedback.pushConsoleInfo(f"--- IMPORTANT: Unity Import Settings ---")
        feedback.pushConsoleInfo(f"Final Resolution (Width/Height): {final_cols}x{final_rows}")
        
        data = band.ReadAsArray().astype(np.float32)
        
        # Handle NoData values
        nodata_value = band.GetNoDataValue()
        min_height = 0
        
        if nodata_value is not None:
            mask = data != nodata_value
            if not mask.any():
                 feedback.pushConsoleInfo("Error: File seems to contain only NoData values.")
                 return False
            min_height = np.min(data[mask])
            data[~mask] = min_height # Fill NoData with minimum height
        else:
            min_height = np.min(data)
            
        max_height = np.max(data)

        feedback.pushConsoleInfo(f"Real-world Min Height: {min_height:.2f}m")
        feedback.pushConsoleInfo(f"Real-world Max Height: {max_height:.2f}m")
        
        terrain_height_variation = max_height - min_height
        feedback.pushConsoleInfo(f"Terrain Height (Variation): {terrain_height_variation:.2f}m")
        feedback.pushConsoleInfo(f"----------------------------------------")
        
        # Normalize (0.0 to 1.0) and scale (0 to 65535)
        if max_height == min_height:
            data_uint16 = np.zeros_like(data, dtype=np.uint16)
        else:
            data_normalized = (data - min_height) / terrain_height_variation
            data_uint16 = (data_normalized * 65535).astype(np.uint16)
            
        # Ensure Little Endian (Windows/Unity default)
        if sys.byteorder == 'big':
            data_uint16.byteswap(inplace=True)

        # 4. SAVE THE FINAL .RAW FILE
        with open(output_raw_path, 'wb') as f:
            data_uint16.tofile(f)

        feedback.pushConsoleInfo(f"\nSUCCESS! File saved to: {output_raw_path}")
        return True

    except Exception as e:
        feedback.pushConsoleInfo(f"An error occurred during processing: {e}")
        return False
    
    finally:
        # 5. CLEANUP
        # Close datasets (if they are still open)
        dataset = None
        cropped_ds = None
        warped_ds = None
        
        # Unlink the in-memory virtual files
        try:
            gdal.Unlink(temp_cropped_path)
        except: pass
        try:
            gdal.Unlink(temp_warped_path)
        except: pass
        feedback.pushConsoleInfo("Processing complete and temporary files cleaned.")


#
# --- Main QGIS Algorithm Class ---
#

class ConvertToUnityRaw(QgsProcessingAlgorithm):
    """
    This is the main algorithm class.
    It converts a GeoTIFF to a Unity-compatible .raw file,
    applying a square crop and UTM reprojection.
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
        return self.tr('Convert to Unity RAW (UTM, Square)')

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