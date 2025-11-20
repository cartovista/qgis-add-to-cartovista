from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QStackedLayout, QSizePolicy
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
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
        stack.setStackingMode(QStackedLayout.StackAll)

        # Background label (stretches with widget size)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pixmap = QPixmap(str(background_path)).scaledToHeight(120, Qt.SmoothTransformation)
        self.bg_label.setPixmap(pixmap)
        stack.addWidget(self.bg_label)

        # Container for centered logo
        logo_container = QWidget(self)
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_size = (171, 37)
        self.logo = QSvgWidget(logo_container)
        self.logo.load(logo_path)
        self.logo.setFixedSize(*logo_size)  # Keep constant size
        logo_layout.addWidget(self.logo)

        stack.addWidget(logo_container)
        stack.setCurrentWidget(logo_container)

        # Ensure both layers resize with parent
        