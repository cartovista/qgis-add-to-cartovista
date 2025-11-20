"""
CartoVista Authorization dialog
"""

from typing import List, Optional

from .authorized_dialog import AuthorizedDialog
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl, pyqtSignal

class UploadCompleteDialog(AuthorizedDialog):
    """
    Custom dialog for authorizing the client.

    If the dialog is accepted then the authorization process should be started.
    """

    create_map_from_layer = pyqtSignal()
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.map_url = None
        
        self.setObjectName('UploadCompleteDialog')

        self.setWindowTitle(self.tr('Add to CartoVista'))

        self.secondaryButton.clicked.connect(self.close)
        self.secondaryButton.setText("Close")

    def _set_primary_button(self, isMap: bool):
        self.clear_primary_button_listeners()
        if isMap:
            self.primaryButton.setText("Open map")
            self.primaryButton.clicked.connect(self.on_click_open_map_button)
        else:
            self.primaryButton.setText("Create map from layer")
            self.primaryButton.clicked.connect(self.create_map_from_layer.emit)
        self.primaryButton.setVisible(True)

    def clear_primary_button_listeners(self):
        try:
            self.primaryButton.clicked.disconnect(self.create_map_from_layer.emit)
        except TypeError:
            pass

        try:
             self.primaryButton.clicked.disconnect(self.on_click_open_map_button)
        except TypeError:
            pass

    def map_success(self, map_title: str, map_url, invalid_layer_names: List[str], failed_layer_names: List[str]):
        self._set_primary_button(True)
        self.map_url = map_url
        text = f"{map_title} has been successfully added to your CartoVista workspace."
        if (invalid_layer_names and len(invalid_layer_names) > 0):
            text += f"<br>The following layers were omitted as their types are not supported: {', '.join(invalid_layer_names)}"
        if (failed_layer_names and len(failed_layer_names) > 0):
            text += f"<br>The following layers failed to upload: {', '.join(failed_layer_names)}"
        self.dialogText.setText(text)
        self.show()

    def layer_success(self, layer_name: str):
        self._set_primary_button(False)
        text = f"Layer {layer_name} has been successfully added to your CartoVista workspace."
        self.dialogText.setText(text)
        self.show()

    def layer_failed(self, layer_name: str):
        self.primaryButton.setVisible(False)
        text = f"Upload of layer {layer_name} failed. An unexpected error occured."
        self.dialogText.setText(text)
        self.show()

    def map_failed(self, map_name: str):
        self.primaryButton.setVisible(False)
        text = f"Upload of map {map_name} failed. An unexpected error occured."
        self.dialogText.setText(text)
        self.show()
        
    def on_click_open_map_button(self):
        QDesktopServices.openUrl(QUrl(self.map_url))
    

        