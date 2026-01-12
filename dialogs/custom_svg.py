from qgis.PyQt.QtWidgets import QLabel, QSizePolicy
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtCore import QSize, QRectF
from qgis.PyQt.QtGui import QPainter

class CustomSvgWidget(QLabel):
    def __init__(self, svg_path=None, parent=None):
        super().__init__(parent)
        # Ensure the renderer exists
        self.renderer = QSvgRenderer()
        if svg_path:
            self.loadSvg(svg_path)

        # Ensure the widget resizes with the SVG content
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    def loadSvg(self, svg_path):
        # Load the SVG file using the QSvgRenderer
        self.renderer.load(svg_path)
        # Force a repaint to display the new SVG
        self.update()

    def sizeHint(self):
        # Return the SVG's natural size as the widget's preferred size
        return self.renderer.defaultSize() if self.renderer.isValid() else QSize(100, 100)

    def paintEvent(self, event):
        # Draw the SVG onto the widget's surface
        if self.renderer.isValid():
            painter = QPainter(self)
            
            # Render the SVG scaled to fill the entire widget rectangle
            self.renderer.render(painter, QRectF(self.rect()))
            
            painter.end()