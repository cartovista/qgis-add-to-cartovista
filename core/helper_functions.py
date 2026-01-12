from qgis.core import QgsVectorLayer, QgsWkbTypes
class HelperFunctions:
    def is_supported_layer(layer) -> bool:
        """Return True if layer is a vector layer of point/line/polygon geometry."""
        if layer is None:
            return False
        if not isinstance(layer, QgsVectorLayer):
            return False
        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        return geom_type in (
            QgsWkbTypes.GeometryType.PointGeometry,
            QgsWkbTypes.GeometryType.LineGeometry,
            QgsWkbTypes.GeometryType.PolygonGeometry,
        )