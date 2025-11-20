from .async_result_thread import AsyncResultThread
from qgis.PyQt.QtCore import QCoreApplication

class AsyncManager:

    def __init__(self):
        self._threads = []

    def setup_thread(self, on_success, on_error, method, *args, **kwargs):
        thread = AsyncResultThread(method, *args, **kwargs)

        self._threads.append(thread)

        thread.finished.connect(on_success)
        thread.error.connect(on_error)

        def _cleanup():
            if thread in self._threads:
                self._threads.remove(thread)
            thread.deleteLater()

        thread.finished.connect(_cleanup)
        thread.error.connect(_cleanup)
        thread.start()


 # --- Singleton pattern using QCoreApplication ---
def get_async_manager():
    app = QCoreApplication.instance()
    if not hasattr(app, "_cv_plugin_async_manager"):
        app._cv_plugin_async_manager = AsyncManager()
    return app._cv_plugin_async_manager

ASYNC_MANAGER = get_async_manager()