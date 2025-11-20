"""
CartoVista Authorization dialog
"""

from typing import Optional

from add_to_cartovista.constants import DEPLOYMENT_URL
from .dialog_header import DialogHeader
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QDialog, QVBoxLayout
from qgis.gui import QgsGui
from .utils import GuiUtils

WIDGET, _ = uic.loadUiType(GuiUtils.get_ui_file_path('dialog_template.ui'))
SIGN_UP_URL = f"{DEPLOYMENT_URL}/signup"

class CartoVistaDialog(QDialog, WIDGET):
    """
    Custom dialog for authorizing the client.

    If the dialog is accepted then the authorization process should be started.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setupUi(self)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(DialogHeader())
        self.header.setLayout(header_layout)

        QgsGui.enableAutoGeometryRestore(self)
        