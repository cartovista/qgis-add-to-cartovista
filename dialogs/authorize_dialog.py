"""
CartoVista Authorization dialog
"""

from typing import Optional

from add_to_cartovista.constants import DEPLOYMENT_URL
from ..authorization import AUTHORIZATION_MANAGER
from .cartovista_dialog import CartoVistaDialog
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl, pyqtSignal

SIGN_UP_URL = f"{DEPLOYMENT_URL}/signup?utm_source=qgis&utm_medium=plugin&utm_campaign=signup"

class AuthorizeDialog(CartoVistaDialog):
    """
    Custom dialog for authorizing the client.

    If the dialog is accepted then the authorization process should be started.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setObjectName('AuthorizeDialog')
        self.setWindowTitle(self.tr('Authorize CartoVista'))

        self.secondaryButton.setText("Log in")
        self.secondaryButton.clicked.connect(self.on_click_login)

        self.primaryButton.setText("Sign up")
        self.primaryButton.clicked.connect(self.sign_up)

    def open(self, mac_os_keychain_issue: bool):
        dialog_text = "Unlock the power of interactive maps for seamless sharing, collaboration, and insightful data analysis with CartoVista Cloud." \
        "<br> Sign up or log in now to get started – and it's absolutely free!"
        if mac_os_keychain_issue:
            dialog_text += "<br> <br> <small><b>Tip:</b> To get QGIS to remember your master password:" \
            '<br> Open <i>Keychain Access</i> → search "QGIS" → double-click it → ' \
            'Access Control → select "Allow all applications to access this item" → Save.</small>'
        self.dialogText.setText(dialog_text)
        self.show()



    def on_click_login(self):
        AUTHORIZATION_MANAGER.start_authorization_workflow()
        self.close()

    def sign_up(self):
        QDesktopServices.openUrl(QUrl(SIGN_UP_URL))
        