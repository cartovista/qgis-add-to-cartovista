import math
from typing import List
from .cartovista_styles import get_fill_style, get_label_settings, get_line_style, get_marker_style
from .helper_functions import HelperFunctions
from .layer_upload_info import LayerUploadInfo, LayerUploadStatus
from qgis.PyQt.QtCore import pyqtSignal, QObject
from qgis.core import (Qgis, QgsFeatureRenderer, QgsWkbTypes, QgsSymbol,
                       QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsCoordinateTransformContext,
                       QgsSimpleMarkerSymbolLayer, QgsSvgMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsSimpleFillSymbolLayer, 
                       QgsGradientFillSymbolLayer, QgsMapLayer)
import zipfile
import os.path
from functools import partial
from .cartovista_api import API_CLIENT
from add_to_cartovista.swagger_client.models.data_column import DataColumn
from add_to_cartovista.swagger_client.models.layer import Layer

class LayerUploadHelper(QObject):
    layer_uploaded = pyqtSignal(LayerUploadInfo)
    layer_upload_failed = pyqtSignal(Exception)
    def __init__(self):
        super().__init__()
        self.layers_upload_info: List[LayerUploadInfo] = []
        self.invalid_layer_names: List[str] = []
        # Context object to store info about coordinate operations
        self.transform_context = QgsCoordinateTransformContext()

    def create_layers_info_for_map_upload(self, layers: List[QgsMapLayer]):
        self.layers_upload_info = []
        self.invalid_layer_names = []
        for layer in layers:
            if HelperFunctions.is_supported_layer(layer):
                self.layers_upload_info.append(LayerUploadInfo(layer))
            else:
                self.invalid_layer_names.append(layer.name())

    def create_geopackage(self, layer_upload_info: LayerUploadInfo, temp_dir: str):
        layer_path_no_extension = os.path.join(temp_dir, layer_upload_info.layer_name)

        writer_options = QgsVectorFileWriter.SaveVectorOptions()
        writer_options.driverName = 'GPKG'
        writer_options.ct = QgsCoordinateTransform(
            layer_upload_info.layer.crs(),
            QgsCoordinateReferenceSystem('EPSG:4326'),
            self.transform_context,
        )
        writer_options.forceMulti = True
        writer_options.overrideGeometryType = QgsWkbTypes.dropM(
            QgsWkbTypes.dropZ(layer_upload_info.layer.wkbType())
        )
        writer_options.includeZ = False
        
        output = QgsVectorFileWriter.writeAsVectorFormatV3(layer_upload_info.layer, layer_path_no_extension, self.transform_context, writer_options)
        if output[0]:
            layer_upload_info.status = LayerUploadStatus.FAILED
            self.iface.messageBar().pushMessage("Error writing Layer contents", "Failed to write: " + layer_upload_info.layer_name + " Status: " + str(output), level=Qgis.MessageLevel.Critical)
            raise Exception("Writing layer to geopackage failed")
        true_file_path = output[2]
        layer_upload_info.file_path = true_file_path
        layer_upload_info.size = math.floor(os.path.getsize(true_file_path) / 1024)
        
    def zip_geopackage(self, temp_dir: str, layer_upload_info: LayerUploadInfo):
        # Zip the layer
        try:
            zipped_layer = str(os.path.join(temp_dir, layer_upload_info.layer_name)) +'.zip'
            with zipfile.ZipFile(zipped_layer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(layer_upload_info.file_path, f"{layer_upload_info.layer_name}.gpkg")
                layer_upload_info.zip_path = zipf.filename
        except:
            layer_upload_info.status = LayerUploadStatus.FAILED
            raise
        return layer_upload_info

    def upload_layer(self, layer_upload_info: LayerUploadInfo):
        API_CLIENT.upload_layer_api(layer_upload_info.zip_path, partial(self._upload_layer_2, layer_upload_info), partial(self._on_upload_layer_error, layer_upload_info))
            
    def _upload_layer_2(self, layer_upload_info: LayerUploadInfo, upload_response: Layer):
        # Get layer styles
        cv_layer_id = upload_response.system_identifier
        layer_upload_info.cv_id = cv_layer_id
        layer_upload_info.cv_identifier = upload_response.unique_identifier

        if layer_upload_info.done_with_geometry_style and layer_upload_info.common_settings_non_default():
            layer_upload_info.status = LayerUploadStatus.COMPLETE
            self.layer_uploaded.emit(layer_upload_info)
            return
        
        API_CLIENT.get_layer_default_settings(cv_layer_id, partial(self._upload_layer_3, layer_upload_info), partial(self._on_get_layer_default_settings_failed, layer_upload_info))
    
    def _upload_layer_3(self, layer_upload_info: LayerUploadInfo, upload_layer_default_settings):
        layer_upload_info.cv_default_layer_settings_id = upload_layer_default_settings.id
        if not layer_upload_info.done_with_geometry_style:
            self._upload_layer_set_symbology(layer_upload_info)
        if layer_upload_info.add_cv_labels:
            self._get_column_id_for_labeling_style(layer_upload_info)
        elif layer_upload_info.common_settings_non_default():
            self._on_cv_common_styles_ready(layer_upload_info)

    def _get_column_id_for_labeling_style(self, layer_upload_info: LayerUploadInfo):
        label_settings = layer_upload_info.layer.labeling().settings()
        on_success = partial(self._get_column_id_for_labeling_success, layer_upload_info)
        on_failure = partial(self._get_column_id_for_labeling_style_failure, layer_upload_info)
        API_CLIENT.get_data_column(layer_upload_info.cv_id, label_settings.fieldName, on_success, on_failure)

    def _get_column_id_for_labeling_style_failure(self, layer_upload_info: LayerUploadInfo, _):
        layer_upload_info.add_cv_labels = False
        layer_upload_info.cv_label_settings = None
        self._on_cv_common_styles_ready(layer_upload_info)

    def _get_column_id_for_labeling_success(self, layer_upload_info: LayerUploadInfo, dataColumn: DataColumn):
        label_settings = layer_upload_info.layer.labeling().settings()
        layer_upload_info.cv_label_settings = get_label_settings(label_settings, dataColumn.system_identifier)
        self._on_cv_common_styles_ready(layer_upload_info)

    def _on_cv_common_styles_ready(self, layer_upload_info: LayerUploadInfo):
        common_layer_settings_update_param = {
            'alias': None,
            'labels': layer_upload_info.cv_label_settings,
            'general': None,
            'interactivity': None,
            'legend': None,
            'rendering': layer_upload_info.cv_rendering_settings,
            'visibilityRanges': layer_upload_info.cv_visibility_settings,
            'effects': None
        }
        on_complete = partial(self._on_upload_layer_style_success_or_error, False, layer_upload_info)
        API_CLIENT.update_common_layer_settings(layer_upload_info.cv_default_layer_settings_id, common_layer_settings_update_param, on_complete, on_complete)

    def _upload_layer_set_symbology(self, layer_upload_info: LayerUploadInfo):
        symbol: QgsSymbol = layer_upload_info.layer.renderer().symbol()
        symbol_layer = symbol.symbolLayer(0)
        properties = symbol_layer.properties()
        on_complete = partial(self._on_upload_layer_style_success_or_error, True, layer_upload_info)
        if isinstance(symbol_layer, (QgsSimpleMarkerSymbolLayer, QgsSvgMarkerSymbolLayer)):
            style = get_marker_style(properties)
            API_CLIENT.update_point_geometry_style(layer_upload_info.cv_default_layer_settings_id, style, on_complete, on_complete)
        elif isinstance(symbol_layer, QgsSimpleLineSymbolLayer):
            style = get_line_style(properties)
            API_CLIENT.update_polyline_geometry_style(layer_upload_info.cv_default_layer_settings_id, style, on_complete, on_complete)
        elif isinstance(symbol_layer, (QgsSimpleFillSymbolLayer, QgsGradientFillSymbolLayer)):
            style = get_fill_style(properties)
            API_CLIENT.update_polygon_geometry_style(layer_upload_info.cv_default_layer_settings_id, style, on_complete, on_complete)
        else:
            self._on_upload_layer_style_success_or_error(True, layer_upload_info, None)

    
    def _on_upload_layer_style_success_or_error(self, for_geom_style: bool, layer_upload_info: LayerUploadInfo, _):
        if for_geom_style:
            layer_upload_info.done_with_geometry_style = True
        else:
            layer_upload_info.done_with_other_layer_settings = True
        
        if layer_upload_info.done_with_geometry_style and layer_upload_info.done_with_other_layer_settings:
            layer_upload_info.status = LayerUploadStatus.COMPLETE
            self.layer_uploaded.emit(layer_upload_info)
    
    def _on_get_layer_default_settings_failed(self, layer_upload_info, e):
        layer_upload_info.status = LayerUploadStatus.COMPLETE
        self.layer_uploaded.emit(layer_upload_info)

    def _on_upload_layer_error(self, layer_upload_info: LayerUploadInfo, e):
        layer_upload_info.status = LayerUploadStatus.FAILED
        self.layer_upload_failed.emit(e)

