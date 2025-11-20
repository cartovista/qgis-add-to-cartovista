from enum import Enum
from .cartovista_styles import get_rendering_settings, get_visibility_ranges_settings
from qgis.core import QgsVectorLayer, QgsFeatureRenderer

class LayerUploadInfo:
  def __init__(self, layer: QgsVectorLayer):
    self.qgis_id = layer.id()
    self.layer = layer
    self.layer_name = layer.name()
    self.size = None
    self.file_path = None
    self.zip_path = None
    self.cv_id = None
    self.cv_identifier = None
    self.cv_default_layer_settings_id = None
    self.status = LayerUploadStatus.PROGRESS
    
    renderer: QgsFeatureRenderer = layer.renderer()
    style_type = renderer.type()

    self.add_cv_labels = layer.labelsEnabled() and layer.labeling().type() == "simple"

    self.opacity = round(layer.opacity() * 100) / 100
    self.cv_rendering_settings = get_rendering_settings(layer)
    self.cv_visibility_settings = get_visibility_ranges_settings(layer)
    self.cv_label_settings = None #need to get labeling column id before creating labeling settings

    self.done_with_geometry_style = style_type != 'singleSymbol'
    self.done_with_other_layer_settings = not self.common_settings_non_default()

  def common_settings_non_default(self):
     return self.cv_rendering_settings != None or self.cv_visibility_settings != None or self.add_cv_labels

    
    
    
       




class LayerUploadStatus(Enum):
    PROGRESS = 1
    FAILED = 2
    COMPLETE = 3

