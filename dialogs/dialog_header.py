from .custom_svg import CustomSvgWidget
from qgis.PyQt.QtWidgets import QWidget, QLabel, QHBoxLayout, QStackedLayout, QSizePolicy
#from qgis.PyQt.QtSvg import QSvgWidget
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtCore import Qt
import os
from pathlib import Path

class DialogHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        plugin_dir = Path(__file__).resolve().parent.parent
        background_path = str(plugin_dir / "assets" / "cartovista_header_background.png")
        logo_path = str(plugin_dir / "assets" / "cartovista_header_logo.svg")
        # Stack layout to layer background and logo
        stack = QStackedLayout(self)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # Background label (stretches with widget size)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pixmap = QPixmap(str(background_path)).scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
        self.bg_label.setPixmap(pixmap)
        stack.addWidget(self.bg_label)

        # Container for centered logo
        logo_container = QWidget(self)
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo = CustomSvgWidget(logo_path, logo_container)
        logo_layout.addWidget(self.logo)

        stack.addWidget(logo_container)
        stack.setCurrentWidget(logo_container)

        # Ensure both layers resize with parent
        