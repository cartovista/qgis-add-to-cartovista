"""
CartoVista Authorization dialog
"""

from typing import Optional

from .authorized_dialog import AuthorizedDialog
from qgis.PyQt.QtWidgets import QWidget


class PreUploadDialog(AuthorizedDialog):
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setObjectName('PreUploadDialog')

    def open(self, isMap: bool, mac_os_keychain_issue: bool):
        window_title = 'Upload map to CartoVista' if isMap else 'Upload layer to CartoVista'
        self.setWindowTitle(self.tr(window_title))
        self.primaryButton.clicked.connect(self.accept)
        self.secondaryButton.clicked.connect(self.close)

        primary_text = "Upload map" if isMap else "Upload layer"
        self.primaryButton.setText(primary_text)
        self.secondaryButton.setText("Cancel")

        dialog_text = "Upload map to your CartoVista workspace? Unchecked layers will not be included." if isMap else "Upload layer to your CartoVista workspace?"

        if mac_os_keychain_issue:
            dialog_text += "<br> <br> <small><b>Tip:</b> To get QGIS to remember your master password:" \
            '<br> Open <i>Keychain Access</i> → search "QGIS" → double-click it → ' \
            'Access Control → select "Allow all applications to access this item" → Save.</small>'
        self.dialogText.setText(dialog_text)

        return self.exec()

        