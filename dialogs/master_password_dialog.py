"""
CartoVista Authorization dialog
"""
import platform
from typing import Optional

from add_to_cartovista.constants import DEPLOYMENT_URL
from ..authorization import AUTHORIZATION_MANAGER
from .cartovista_dialog import CartoVistaDialog
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl, pyqtSignal

SIGN_UP_URL = f"{DEPLOYMENT_URL}/signup?utm_source=qgis&utm_medium=plugin&utm_campaign=signup"

class MasterPasswordDialog(CartoVistaDialog):
    """
    Custom dialog for authorizing the client.

    If the dialog is accepted then the authorization process should be started.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setObjectName('MasterPasswordDialog')
        self.setWindowTitle(self.tr('Master password required'))

        dialog_text = "CartoVista requires access to the QGIS vault to store our Access Tokens securily. Accessing the QGIS vault requires you to set up or enter your master password. <br> <br>" \
                        "If you have previously set up a master password and have forgotten it, you can reset it by going to Settings > Options... > Authentication > Utilities > Erase Authentication Database..."

        self.dialogText.setText(dialog_text)

        self.secondaryButton.setText("Cancel")
        self.secondaryButton.clicked.connect(self.close)

        self.primaryButton.setText("Configure master password")
        self.primaryButton.clicked.connect(self.accept)
    
        