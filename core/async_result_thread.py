from qgis.PyQt.QtCore import QThread, pyqtSignal

class AsyncResultThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, api_method, *args, **kwargs):
        super().__init__()
        self.api_method = api_method
        self.args = args
        self.kwargs = kwargs


    def run(self):
        try:
            result = self.api_method(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)