import ast
import base64
import hashlib
import os
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import urllib.parse
import time
import socket

from ..constants import DEPLOYMENT_URL, OAUTH_CLIENT_ID
from .oauth_pages import SUCCESS_HTML, ERROR_HTML
from qgis.PyQt.QtGui import QDesktopServices

from qgis.PyQt.QtCore import (
    QThread,
    pyqtSignal,
    QUrl
)
from add_to_cartovista.swagger_client.api.o_auth_api import OAuthApi


# === CONFIGURATION ===
AUTH_URL = f"{DEPLOYMENT_URL}/authorize"
TOKEN_URL = f"{DEPLOYMENT_URL}/api/v2/oauth2/token"
SCOPE = "FULL_ACCESS"

def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    _, port = s.getsockname()
    s.close()
    return port


class RefreshTokenWorkflow(QThread):
    finished = pyqtSignal(str, int, str)
    error_occurred = pyqtSignal(str)
    def __init__(self, refresh_token):
        super().__init__()
        self.refresh_token = refresh_token
    def run(self):
        api_instance = OAuthApi()
        body = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": OAUTH_CLIENT_ID
        }

        try:
            response = api_instance.o_auth_token(**body)
        except Exception:
            self.error_occurred.emit("Refresh Token call failed")
            return
        token_response = ast.literal_eval(response)

        refresh_token = token_response.get("refresh_token")
        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in")
        self.finished.emit(access_token, expires_in, refresh_token)


class OAuthWorkflow(QThread):
    finished = pyqtSignal(str, int, str)
    error_occurred = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        
        port = get_free_port()
        self.redirect_uri = f"http://127.0.0.1:{port}/callback"
        self.port = port
        self.server = None
        self.code_verifier, self.code_challenge = OAuthWorkflow.generate_pkce_pair()
        self.state = OAuthWorkflow.generate_oauth_state()
        params = {
            "response_type": "code",
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uri": self.redirect_uri,
            "scope": SCOPE,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
            "state": self.state
        }
        self.oauth_url_params = urllib.parse.urlencode(params)

        self.terminate_workflow = False

    def run(self):
        self.server = HTTPServer(('127.0.0.1', self.port), OAuthCallbackHandler)
        self.server.code_verifier = self.code_verifier
        self.server.state = self.state
        self.server.access_token = None
        self.server.expires_in = None
        self.server.refresh_token = None
        self.server.error = None
        self.server.redirect_uri = self.redirect_uri

        QDesktopServices.openUrl(QUrl(f"{AUTH_URL}?{self.oauth_url_params}"))

        self.server.timeout = 1.0  # 1 second to give the socket time to stabilize
        start_time = time.time()
        while True:
            if self.terminate_workflow:
                self._close_server()
                return
            self.server.handle_request()
            if self.server.access_token or self.server.error:
                break
            if time.time() - start_time > 300:
                self.server.error = "Timeout waiting for response"
                break

        if self.server.error:
            self.error_occurred.emit(self.server.error)
        else:
            self.finished.emit(self.server.access_token, self.server.expires_in,self. server.refresh_token)

    def close_server(self):
        """
        Closes and cleans up the local server
        """
        self.terminate_workflow = True
        if self.server.access_token or self.server.error:
            self._close_server()
            

    def _close_server(self):
        self.server.server_close()
        del self.server
        self.server = None

    @staticmethod
    def generate_pkce_pair():
        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip("=")
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip("=")
        return code_verifier, code_challenge

    @staticmethod
    def generate_oauth_state():
        return secrets.token_urlsafe(32)


class OAuthCallbackHandler(BaseHTTPRequestHandler):

    def log_request(self, _format, *args):  # pylint: disable=arguments-differ
        pass

    def do_GET(self):
        self.get_auth_token()
        if not self.server.error:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(SUCCESS_HTML.encode("utf8"))
            self.wfile.flush()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(ERROR_HTML.encode("utf8"))
    
    def get_auth_token(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if not "code" in params:
            self.server.error = "Auth code not found"
            return
        auth_code = params["code"][0]
        retreived_state = params["state"][0]
        if (retreived_state is None or retreived_state != self.server.state):
            self.server.error = "Invalid state parameter"
            return
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.server.redirect_uri,
            "client_id": OAUTH_CLIENT_ID,
            "code_verifier": self.server.code_verifier
        }

        response = requests.post(TOKEN_URL, data=data)
        token_response = response.json()

        refresh_token = token_response.get("refresh_token")
        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in")
        
        if not access_token or not expires_in or not refresh_token:
            self.server.error = "Access token, exiry time or refresh token not found"
            return
        
        self.server.refresh_token = refresh_token
        self.server.access_token = access_token
        self.server.expires_in = expires_in

