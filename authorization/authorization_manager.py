from functools import partial
from typing import Optional
from .oauth import OAuthWorkflow, RefreshTokenWorkflow
from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject,
    pyqtSignal,
    QTimer,
    QDateTime,
    Qt,
    QCoreApplication,
    QUrl
)
from qgis.core import QgsApplication


CARTOVISTA_ACCESS_TOKEN = "cartovista_access_token"
CARTOVISTA_ACCESS_TOKEN_EXPIRY = "cartovista_access_token_expiry"
CARTOVISTA_REFRESH_TOKEN = "cartovista_refresh_token"


class AuthorizationManager(QObject):
    deauthenticated = pyqtSignal()
    authenticated = pyqtSignal()
    tokens_changed = pyqtSignal()
    show_auth_dialog = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.oauth_close_timer: Optional[QTimer] = None
        self._workflow: Optional[OAuthWorkflow] = None
        self._refresh_workflow: Optional[RefreshTokenWorkflow] = None
        self.access_token = None

        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._iniate_token_refresh_from_timer)
    
    def try_authenticate(self):
        """
        Tries to authorize the client, using previously fetched token if
        available. Otherwise shows the login dialog to the user.
        """
        api_token, expiry_time, refresh_token = AuthorizationManager.retrieve_tokens()

        if expiry_time:
            token_expiry_dt = QDateTime.fromString(expiry_time, Qt.ISODate)
            if not token_expiry_dt.isValid() or token_expiry_dt <= QDateTime.currentDateTime():
                self._initiate_token_refresh(refresh_token, True)
                return
        elif refresh_token is not None:
            self._initiate_token_refresh(refresh_token, True)
            return
        else:
            self.show_auth_dialog.emit()
            return

        self._set_token_refresh_timer(token_expiry_dt)
        self.set_access_token(api_token)
        self.authenticated.emit()

    def _set_token_refresh_timer(self, timer_end: QDateTime):
        if self._refresh_timer.isActive():
            self._refresh_timer.stop()
        now = QDateTime.currentDateTime()
        milliseconds_left = now.msecsTo(timer_end)
        self._refresh_timer.start(milliseconds_left)
        

    @staticmethod
    def retrieve_tokens() -> Optional[str]:
        """
        Retrieves a previously stored API token, if available

        Returns None if no stored token is available
        """
        access_token = (
                QgsApplication.authManager().authSetting(
                    CARTOVISTA_ACCESS_TOKEN, defaultValue="", decrypt=True
                ) or None
        )
        token_expiry = (
                QgsApplication.authManager().authSetting(
                    CARTOVISTA_ACCESS_TOKEN_EXPIRY, defaultValue="", decrypt=False
                ) or None
        )
        refresh_token = (
                QgsApplication.authManager().authSetting(
                    CARTOVISTA_REFRESH_TOKEN, defaultValue="", decrypt=True
                ) or None
        )

        return access_token, token_expiry, refresh_token
    
    def deauthenticate(self):
        if self._refresh_timer.isActive():
            self._refresh_timer.stop()
        QgsApplication.authManager().storeAuthSetting(
            CARTOVISTA_ACCESS_TOKEN, "", True
        )
        QgsApplication.authManager().storeAuthSetting(
            CARTOVISTA_ACCESS_TOKEN_EXPIRY,
            "",
            False
        )
        QgsApplication.authManager().storeAuthSetting(
            CARTOVISTA_REFRESH_TOKEN,
            "",
            True
        )
        self.access_token = None
        self.deauthenticated.emit()

    def start_authorization_workflow(self):
        if self._workflow is not None:
            self._terminate_oauth_thread()
        self._workflow = OAuthWorkflow()
        self._workflow.error_occurred.connect(self._on_authorization_failed)
        self._workflow.finished.connect(self._on_authorization_success)
        self._workflow.start()

    def _store_api_token(self, token: str, expiry: int, refresh_token: str):
        buffer_seconds = 60
        expires_at = QDateTime.currentDateTimeUtc().addSecs(expiry - buffer_seconds)
        expires_at_str = expires_at.toString(Qt.ISODate)
        QgsApplication.authManager().storeAuthSetting(
            CARTOVISTA_ACCESS_TOKEN, token, True
        )
        QgsApplication.authManager().storeAuthSetting(
            CARTOVISTA_ACCESS_TOKEN_EXPIRY,
            expires_at_str,
            False
        )
        QgsApplication.authManager().storeAuthSetting(
            CARTOVISTA_REFRESH_TOKEN,
            refresh_token,
            True
        )

        self._set_token_refresh_timer(expires_at)
        self.set_access_token(token)
    

    def _on_authorization_success(self, token: str, expiry: int, refresh_token: str):
        self._store_api_token(token, expiry, refresh_token)
        self._terminate_oauth_thread_delay()
        self.authenticated.emit()

    def _on_authorization_failed(self, error: str):
        self._terminate_oauth_thread_delay()

    def _terminate_oauth_thread_delay(self):
        if self._workflow and not sip.isdeleted(self._workflow):
            self.oauth_close_timer = QTimer(self)
            self.oauth_close_timer.setSingleShot(True)
            self.oauth_close_timer.setInterval(1000)
            self.oauth_close_timer.timeout.connect(self._terminate_oauth_thread)
            self.oauth_close_timer.start()


    def _terminate_oauth_thread(self):
        if self.oauth_close_timer and not sip.isdeleted(
                self.oauth_close_timer):
            self.oauth_close_timer.timeout.disconnect(
                self._terminate_oauth_thread)
            self.oauth_close_timer.deleteLater()
        self.oauth_close_timer = None

        if self._workflow and not sip.isdeleted(self._workflow):

            self._workflow.close_server()
            self._workflow.quit()
            self._workflow.wait()
            self._workflow.deleteLater()

        self._workflow = None

    def _on_refresh_failed(self, error):
        self._terminate_refresh_thread()
        self.deauthenticate()

    def _on_refresh_success(self, token: str, expiry: int, refresh_token: str, isFirstAttemptAuth=False):
        self._store_api_token(token, expiry, refresh_token)
        self._terminate_refresh_thread()
        if isFirstAttemptAuth:
            self.authenticated.emit()

    def _terminate_refresh_thread(self):
        if self.refresh_workflow and not sip.isdeleted(self.refresh_workflow):
            self.refresh_workflow.quit()
            self.refresh_workflow.wait()
            self.refresh_workflow.deleteLater()

        self.refresh_workflow = None

    def _initiate_token_refresh(self, refresh_token, isFirstAttemptAuth: bool):
        self.refresh_workflow = RefreshTokenWorkflow(refresh_token)
        
        self.refresh_workflow.error_occurred.connect(self._on_refresh_failed)
        self.refresh_workflow.finished.connect(partial(self._on_refresh_success, isFirstAttemptAuth=isFirstAttemptAuth))
        self.refresh_workflow.start()

    def _iniate_token_refresh_from_timer(self):
        refresh_token = (
                QgsApplication.authManager().authSetting(
                    CARTOVISTA_REFRESH_TOKEN, defaultValue="", decrypt=True
                ) or None
        )
        self._initiate_token_refresh(refresh_token, False)

    def set_access_token(self, access_token):
        if self.access_token != access_token:
            self.access_token = access_token
            self.tokens_changed.emit()

 # --- Singleton pattern using QCoreApplication ---
def get_authorization_manager():
    app = QCoreApplication.instance()
    if not hasattr(app, "_cv_plugin_auth_manager"):
        app._cv_plugin_auth_manager = AuthorizationManager()
    return app._cv_plugin_auth_manager

AUTHORIZATION_MANAGER = get_authorization_manager()
