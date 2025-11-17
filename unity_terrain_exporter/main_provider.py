# This file defines the Processing Provider.
# It groups all our algorithms under one "provider" in the toolbox.

from qgis.core import QgsProcessingProvider

# Import our algorithm class from the other file
from .convert_unity_raw import ConvertToUnityRaw

class UnityToolsProvider(QgsProcessingProvider):
    """
    This is the provider class that manages and exposes
    our processing algorithms to QGIS.
    """

    def loadAlgorithms(self, *args, **kwargs):
        """ Loads all available algorithms. """
        # Add our single algorithm to the provider
        self.addAlgorithm(ConvertToUnityRaw())
        # You could add more algorithms here in the future

    def id(self, *args, **kwargs):
        """ Returns the unique provider ID. """
        # This ID should be unique and machine-readable
        return 'unity_tools_provider'

    def name(self, *args, **kwargs):
        """ Returns the provider's display name. """
        # This is the name for the group in the toolbox
        return 'Unity Conversion Tools'

    def icon(self, *args, **kwargs):
        """ Returns the icon for the tool group. """
        # We can set a proper icon later
        return QgsProcessingProvider.icon(self)

    def longName(self, *args, **kwargs):
        """ Returns a longer description for the provider. """
        return self.name()