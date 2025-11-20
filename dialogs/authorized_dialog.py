from typing import Optional
from ..authorization.authorization_manager import AUTHORIZATION_MANAGER
from .cartovista_dialog import CartoVistaDialog
from qgis.PyQt.QtWidgets import QWidget

class AuthorizedDialog(CartoVistaDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._user_email = None
        self._user_organization_name = None

        self.user_info_label.setVisible(True)
        self.log_out_button.setVisible(True)
        self.log_out_button.setText("Log out")
        self.log_out_button.clicked.connect(self.logout)

    def set_email_and_organization(self, email: Optional[str], organization_name: Optional[str]):
        self._user_email = email
        self._user_organization_name = organization_name
        if email and organization_name:
            self.user_info_label.setText(f"{self._user_email} | {self._user_organization_name}")

    def logout(self):
        AUTHORIZATION_MANAGER.deauthenticate()