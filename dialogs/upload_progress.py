"""
CartoVista Authorization dialog
"""

from typing import Optional

from .authorized_dialog import AuthorizedDialog
from qgis.PyQt.QtWidgets import QWidget

UPLOADING_MESSAGE = "Uploading"
UPLOAD_COMPLETE_MESSAGE = "Upload Complete"
UPLOAD_FAILED_MESSAGE = "Upload Failed"
class UploadProgress(AuthorizedDialog):
    """
    Custom dialog for authorizing the client.

    If the dialog is accepted then the authorization process should be started.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.setObjectName('UploadProgressDialog')

        self._max_value = 100
        self._progress = 0
        self.setWindowTitle(self.tr('Add to CartoVista'))

        self.log_out_button.setVisible(False)
        self.progressBar.setVisible(True)
        self.primaryButton.setVisible(False)
        self.secondaryButton.setVisible(False)
    
    def start_upload(self, is_map_upload: bool, item_name: str):
        text = f"Uploading {item_name} to CartoVista..." if is_map_upload else f"Uploading layer {item_name} to CartoVista..."
        self.dialogText.setText(text)
        self.show()

    def start_upload_map(self, map_name):
        text = f"Uploading {map_name} to CartoVista..."
        self.dialogText.setText(text)
        self.set_progress(0)
        self.set_maximum(100)
        self.show()

    def start_upload_layer(self, layer_name):
        text = f"Uploading layer {layer_name} to CartoVista..."
        self.dialogText.setText(text)
        self.set_progress(0)
        self.set_maximum(4)
        self.show()

        
    def set_progress(self, progress: int):
        self._progress = progress
        self.progressBar.setValue(progress)

    def set_maximum(self, maximum: int):
        self._max_value = maximum
        self.progressBar.setMaximum(maximum)

    def get_progress(self):
        return self._progress
    
    def get_maximum(self):
        return self._max_value




        