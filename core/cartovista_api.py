"""
CartoVista API Client
"""

from __future__ import print_function
from add_to_cartovista import swagger_client
from ..authorization import AUTHORIZATION_MANAGER
from .async_manager import ASYNC_MANAGER
from qgis.PyQt.QtCore import QCoreApplication

class ApiClient():

    def __init__(self):
        # Configure API key authorization: apiKey
        configuration = swagger_client.Configuration()

        configuration.api_key_prefix['Authorization'] = 'Bearer '
        configuration.api_key['Authorization'] = AUTHORIZATION_MANAGER.access_token

    
        #configuration.api_key['apiKey'] = API_KEY
        # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
        # configuration.api_key_prefix['apiKey'] = 'Bearer'

        # Create an instance of the API class
        self.api_client = swagger_client.ApiClient(configuration)
        self.map_api = swagger_client.MapApi(self.api_client)
        self.layer_api = swagger_client.LayerApi(self.api_client)
        self.layer_settings_api = swagger_client.LayerSettingsApi(self.api_client)
        self.oauth_api = swagger_client.OAuthApi(self.api_client)
        self.organization_api = swagger_client.OrganizationApi(self.api_client)
        self.user_api = swagger_client.UserApi(self.api_client)
        self.data_column_api = swagger_client.DataColumnApi(self.api_client)
        self.slide_api = swagger_client.SlideApi(self.api_client)

        self.tenant_url_code = None

        AUTHORIZATION_MANAGER.tokens_changed.connect(self._set_bearer_token)
        AUTHORIZATION_MANAGER.deauthenticated.connect(self._unset_internal_tenant_url_code)

    def _unset_internal_tenant_url_code(self):
         self.tenant_url_code = None
    
    def get_current_organization(self, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.organization_api.organization_get_organization)

    def get_current_user(self, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.user_api.user_get_current_user, self.tenant_url_code)

    def upload_layer_api(self, file, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.layer_api.layer_create_layer_from_zip, self.tenant_url_code, file=file)

    def get_data_column(self, layer_identifier, column_identifier, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.data_column_api.data_column_get_layer_data_column, layer_identifier, column_identifier, self.tenant_url_code)

    def get_map_slides(self, map_identifier, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.map_api.map_get_slides, map_identifier, self.tenant_url_code)

    def update_slide_themeset(self, slide_id, theme_set, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.slide_api.slide_update_slide_theme_set, theme_set, slide_id, self.tenant_url_code)

    def create_map_api(self, map_name, map_layer_parameters, on_success, on_error):
        body = {
            "title": "",
            "description": "",
            "language": "en",
            "editable": True,
            "seoTitle": "",
            "seoDescription": "",
            "seoCustomHTML": "",
            "scoringEnabled": False,
            "layers": [
                {
                    "identifier": "",
                    "type": "Interactive"
                }
            ],
            "themesets": "",
            "thematicSchemas": "",
            "defaultSlideName": "Default slide"
        }
        body["title"] = map_name
        body["layers"] = map_layer_parameters

        ASYNC_MANAGER.setup_thread(on_success, on_error, self.map_api.map_create_map, body, self.tenant_url_code)

    def get_layer_default_settings(self, layer_id, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.layer_settings_api.layer_settings_get_default_layer_settings, layer_id, self.tenant_url_code)

    def update_point_geometry_style(self, layer_settings_id, geometry_style, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.layer_settings_api.layer_settings_update_point_geometry_style, geometry_style, layer_settings_id, self.tenant_url_code)

    def update_polyline_geometry_style(self, layer_settings_id, geometry_style, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.layer_settings_api.layer_settings_update_polyline_geometry_style, geometry_style, layer_settings_id, self.tenant_url_code)

    def update_polygon_geometry_style(self, layer_settings_id, geometry_style, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.layer_settings_api.layer_settings_update_polygon_geometry_style, geometry_style, layer_settings_id, self.tenant_url_code)

    def update_common_layer_settings(self, layer_settings_id, common_settings, on_success, on_error):
        ASYNC_MANAGER.setup_thread(on_success, on_error, self.layer_settings_api.layer_settings_update_common_settings, common_settings, layer_settings_id, self.tenant_url_code)

    def _set_bearer_token(self):
        self.api_client.configuration.api_key['Authorization'] = AUTHORIZATION_MANAGER.access_token

 # --- Singleton pattern using QCoreApplication ---
def get_api_client():
    app = QCoreApplication.instance()
    if not hasattr(app, "_cv_plugin_api_client"):
        app._cv_plugin_api_client = ApiClient()
    return app._cv_plugin_api_client

API_CLIENT = get_api_client()
    
