# This file is the main entry point for the QGIS plugin.

from qgis.core import QgsApplication

def classFactory(iface):
    """
    Called by QGIS to get the plugin class.
    :param iface: An instance of QgisInterface.
    """
    
    # Import the provider class from our other file
    from .main_provider import UnityToolsProvider
    
    # Create an instance of the provider
    provider = UnityToolsProvider()
    
    # Add the provider to the QGIS processing registry
    QgsApplication.processingRegistry().addProvider(provider)
    
    # This simple class wrapper manages the plugin's lifetime
    class UnityPlugin:
        def __init__(self):
            self.provider = provider

        def initGui(self):
            # Called when the plugin is loaded in the GUI
            pass

        def unload(self):
            # Called when the plugin is unloaded
            # Remove the provider from the processing registry
            QgsApplication.processingRegistry().removeProvider(self.provider)

    return UnityPlugin()