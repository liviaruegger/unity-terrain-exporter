# This file contains the main algorithm logic.
# This is where the actual DEM processing will happen.

# QGIS imports
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsProcessingFeedback
)

# GDAL/OSR imports (QGIS includes these)
from osgeo import gdal, osr

class ConvertToUnityRaw(QgsProcessingAlgorithm):
    """
    This is the main algorithm class.
    It converts a GeoTIFF to a Unity-compatible .raw file,
    applying a square crop and UTM reprojection.
    """
    
    # --- Parameter Definitions ---
    # These constants are the "keys" for our inputs and outputs
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
        This is where the core logic will go.
        """
        
        # Get input/output file paths from parameters
        input_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        if not input_layer:
            feedback.pushConsoleInfo("Invalid input layer.")
            return {self.OUTPUT: None}
            
        input_path = input_layer.source()
        output_path = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        # ---
        # START of core logic (to be added in the next step)
        # ---
        
        # For now, just log that we started
        feedback.pushConsoleInfo("Algorithm started...")
        feedback.pushConsoleInfo(f"Input file: {input_path}")
        feedback.pushConsoleInfo(f"Output file: {output_path}")

        # ---
        # END of core logic
        # ---

        feedback.pushConsoleInfo("Algorithm finished.")
        
        # Return the output(s)
        return {self.OUTPUT: output_path}

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
        # self.tr() enables translation
        return self.tr('Convert to Unity RAW (UTM, Square)')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        # This will be overridden by the provider's name,
        # but it's good practice to have it.
        return self.tr('Unity Tools')

    def groupId(self):
        """
        Returns the unique ID of the group.
        """
        return 'unity_tools'

    def tr(self, string):
        """
        Translation function wrapper.
        """
        # This connects to the QGIS translation system
        return QgsProcessingAlgorithm.tr(self, string)

    def createInstance(self):
        """
        Required method to create a new instance of the class.
        """
        return ConvertToUnityRaw()