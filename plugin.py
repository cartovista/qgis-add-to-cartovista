"""
CartoVista QGIS plugin
"""

import math
import platform
import re
from add_to_cartovista.constants import DEPLOYMENT_URL

from .core import (
    ASYNC_MANAGER,
    HelperFunctions,
    LayerUploadHelper,
    LayerUploadInfo,
    LayerUploadStatus,
    generate_theme_set_group,
    API_CLIENT
)

from .authorization import AUTHORIZATION_MANAGER

from .dialogs import (
    UploadCompleteDialog,
    UploadProgress,
    PreUploadDialog,
    GuiUtils,
    AuthorizeDialog,
    MasterPasswordDialog
)

from qgis.PyQt.QtCore import QObject, QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QDialog
from qgis.PyQt import sip
from qgis.core import Qgis, QgsVectorLayer, QgsLayerTreeLayer, QgsProject, QgsApplication
from qgis.gui import QgisInterface

import shutil
import tempfile
import os.path
from typing import List, Optional
from functools import partial

from add_to_cartovista.swagger_client.models.map import Map
from add_to_cartovista.swagger_client.models.organization import Organization
from add_to_cartovista.swagger_client.models.user import User
from add_to_cartovista.swagger_client.models.slide import Slide


class CartoVistaPlugin(QObject):
    """ 
    CartoVista QGIS plugin
    """

    def __init__(self, iface: QgisInterface):
        
        # Save reference to the QGIS interface
        super().__init__()
        self.iface: QgisInterface = iface
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CartoVistaPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.menu = self.tr(u'&CartoVista')
        
        self.pre_upload_dialog = PreUploadDialog()
        self.upload_progress_dialog = UploadProgress()
        self.upload_complete_dialog = UploadCompleteDialog()
        self.authorize_dialog = AuthorizeDialog()
        self.layer_upload_helper = LayerUploadHelper()
        self.master_password_dialog = MasterPasswordDialog()
        self.layer_to_upload = None
        self.temp_dir = None
        self.map_name = None
        self.organization : Optional[Organization] = None
        self.user : Optional[User] = None

        AUTHORIZATION_MANAGER.deauthenticated.connect(self._on_deauthenticated)
        AUTHORIZATION_MANAGER.authenticated.connect(self._on_authenticated)
        AUTHORIZATION_MANAGER.show_auth_dialog.connect(self.on_show_authorize_dialog)
        self.upload_complete_dialog.create_map_from_layer.connect(self.create_map_from_uploaded_layer)
        self.master_password_dialog.accepted.connect(self.verify_master_password)

        self.mac_os_keychain_permission_issue = False
        QgsApplication.authManager().passwordHelperFailure.connect(self.on_password_helper_failure)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CartoVistaPlugin', message)


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.share_map_action = QAction(self.tr('Add to CartoVista…'))
        self.share_map_action.setIcon(QIcon(GuiUtils.get_icon('icon.png')))
        self.share_map_action.triggered.connect(partial(self.upload_map_pre_dialog))
        self.iface.addWebToolBarIcon(self.share_map_action)


         # little hack to ensure the web menu is visible before we try
        # to add a submenu to it -- the public API expects plugins to only
        # add individual actions to this menu, not submenus.
        temp_action = QAction()
        self.iface.addPluginToWebMenu('CartoVista', temp_action)

        web_menu = self.iface.webMenu()
        self.cartovista_web_menu = QMenu(self.tr('CartoVista'))
        self.cartovista_web_menu.setIcon(
            GuiUtils.get_icon('icon.png')
        )

        web_menu.addMenu(self.cartovista_web_menu)

        self.iface.removePluginWebMenu('CartoVista', temp_action)
        self.cartovista_web_menu.addAction(self.share_map_action)

        

        self.set_share_map_state()

        # Re-check whenever project layers change
        QgsProject.instance().layerTreeRoot().addedChildren.connect(self.set_share_map_state)
        QgsProject.instance().layerTreeRoot().removedChildren.connect(self.set_share_map_state)
        QgsProject.instance().layersAdded.connect(self.set_share_map_state) #needed since layerTreeRoot().addedChildren does not fire when opening a project
        QgsProject.instance().layerTreeRoot().visibilityChanged.connect(self.set_share_map_state)
        self.share_layer_action = None
        
        try:
            self.iface.layerTreeView().contextMenuAboutToShow.connect(self.layer_tree_view_menu)
        except AttributeError:
            pass

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.disconnect_signal(QgsProject.instance().layersAdded, self.set_share_map_state)
        self.disconnect_signal(QgsProject.instance().layerTreeRoot().visibilityChanged, self.set_share_map_state)
        self.disconnect_signal(QgsProject.instance().layerTreeRoot().addedChildren, self.set_share_map_state)
        self.disconnect_signal(QgsProject.instance().layerTreeRoot().removedChildren, self.set_share_map_state)

        if self.cartovista_web_menu and not sip.isdeleted(self.cartovista_web_menu):
            self.cartovista_web_menu.deleteLater()
            self.cartovista_web_menu = None

        if self.share_map_action and not sip.isdeleted(self.share_map_action):
            self.share_map_action.deleteLater()
        self.share_map_action = None

        if self.share_layer_action and not sip.isdeleted(self.share_layer_action):
            self.share_layer_action.deleteLater()
        self.share_layer_action = None

    def open_upload_map_dialog(self):
        self.close_all_dialogs()
        result = self.pre_upload_dialog.open(True, self.mac_os_keychain_permission_issue)
        if result == QDialog.DialogCode.Accepted:
            self.upload_map()
    
    def upload_map_pre_dialog(self):
        self.layer_to_upload = None
        self.verify_master_password()

    def upload_layer_pre_dialog(self, layer_id):
        self.layer_to_upload = layer_id
        self.verify_master_password()

    def open_upload_layer_dialog(self):
        self.close_all_dialogs()
        result = self.pre_upload_dialog.open(False, self.mac_os_keychain_permission_issue)
        if result == QDialog.DialogCode.Accepted:
            self.upload_single_layer(self.layer_to_upload)
        

    def upload_single_layer(self, layer: Optional[QgsVectorLayer] = None):
        # Create temp directory
        # Create a directory inside C:\Users\USENAME\AppData\Local\Temp for windows
        self.temp_dir = tempfile.mkdtemp(None, 'cartovista_qgisplugin_', None)
        layer_info = LayerUploadInfo(layer)
        self.upload_progress_dialog.start_upload_layer(layer_info.layer_name)
        self.layer_upload_helper.layers_upload_info = [layer_info]
        ASYNC_MANAGER.setup_thread(self._upload_single_layer_2, self._on_upload_single_layer_error, self.layer_upload_helper.create_geopackage, self.layer_upload_helper.layers_upload_info[0], self.temp_dir)
    
    def _upload_single_layer_2(self):
        self.upload_progress_dialog.set_progress(1)
        ASYNC_MANAGER.setup_thread(self._upload_single_layer_3, self._on_upload_single_layer_error, self.layer_upload_helper.zip_geopackage, self.temp_dir, self.layer_upload_helper.layers_upload_info[0])

    def _upload_single_layer_3(self):
        self.upload_progress_dialog.set_progress(2)
        self.layer_upload_helper.layer_uploaded.connect(self._on_upload_single_layer_success)
        self.layer_upload_helper.layer_upload_failed.connect(self._on_upload_single_layer_error)
        self.layer_upload_helper.upload_layer(self.layer_upload_helper.layers_upload_info[0])
    
    def _on_upload_single_layer_success(self, layer_upload_info: LayerUploadInfo):
        self.upload_progress_dialog.set_progress(4)
        self.delete_temp_folder()
        self.disconnect_signal(self.layer_upload_helper.layer_uploaded, self._on_upload_single_layer_success)
        self.disconnect_signal(self.layer_upload_helper.layer_upload_failed, self._on_upload_single_layer_error)
        self.upload_progress_dialog.close()
        self.upload_complete_dialog.layer_success(layer_upload_info.layer_name)

    def _on_upload_single_layer_error(self, _):
        layer_upload_info = self.layer_upload_helper.layers_upload_info[0]
        self.disconnect_signal(self.layer_upload_helper.layer_uploaded, self._on_upload_single_layer_success)
        self.disconnect_signal(self.layer_upload_helper.layer_upload_failed, self._on_upload_single_layer_error)
        self.upload_progress_dialog.close()
        self.upload_complete_dialog.layer_failed(layer_upload_info.layer_name)

    def get_map_name(self, layer_names: Optional[list] = None):
        # Get the current project instance
        project = QgsProject.instance()
        # Get the project file path
        project_path = project.fileName()  # Returns full path if saved, empty string if new

        # Check if the project is new / not yet saved
        if not project.title() and not project_path and layer_names is not None and len(layer_names) > 0:
            title_from_layers = ", ".join(layer_names)
            self.map_name = title_from_layers
            return

        # If the project is saved, or the map has no layers, use the window title
        window_title = self.iface.mainWindow().windowTitle()
        title_cleaned = re.sub(r'\s*[-—]\s*QGIS\b.*$', '', window_title).lstrip('*')
        self.map_name = title_cleaned

    def upload_map(self):

        def is_layer_visible(layer):
            layer_tree_root = QgsProject.instance().layerTreeRoot()
            checked_ids = {l.id() for l in layer_tree_root.checkedLayers()}
            if checked_ids:
                return layer.id() in checked_ids
            return False        
        layers = list(filter(is_layer_visible, self.iface.mapCanvas().layers())) 
        
        if not layers:
            self.iface.messageBar().pushMessage("No layer selected for uplaod", level=Qgis.MessageLevel.Warning)
            return
        self.get_map_name()
        self.upload_progress_dialog.start_upload_map(self.map_name)
        self.temp_dir = tempfile.mkdtemp(None, 'cartovista_qgisplugin_', None)

        self.layer_upload_helper.create_layers_info_for_map_upload(layers)
        ASYNC_MANAGER.setup_thread(self._upload_map_2, self._on_map_creation_failed, self._upload_map_create_geopackages)
        
    def _upload_map_create_geopackages(self):
        maxProgress = 0
        currentProgress = 0
        for layer_upload_info in self.layer_upload_helper.layers_upload_info:
            self.layer_upload_helper.create_geopackage(layer_upload_info, self.temp_dir)
            maxProgress += math.floor(layer_upload_info.size * 1.2 * 1.1)
            currentProgress += math.floor(layer_upload_info.size * 0.1)
        return (maxProgress, currentProgress)

    def _upload_map_2(self, progress_bar_info):
        maxProgress = progress_bar_info[0]
        currentProgress = progress_bar_info[1]

        self.upload_progress_dialog.set_maximum(maxProgress)
        self.upload_progress_dialog.set_progress(currentProgress)

        self.layer_upload_helper.layer_uploaded.connect(self._on_layer_uploaded_for_upload_map)
        self.layer_upload_helper.layer_upload_failed.connect(self._on_layer_failed_for_upload_map)
        for layer_upload_info in self.layer_upload_helper.layers_upload_info:
            ASYNC_MANAGER.setup_thread(self._on_layer_zipped_for_upload_map, self._on_map_creation_failed, self.layer_upload_helper.zip_geopackage, self.temp_dir, layer_upload_info)

    def _on_layer_zipped_for_upload_map(self, layer_upload_info):
        currentProgress = self.upload_progress_dialog.get_progress()
        currentProgress += math.floor(layer_upload_info.size * 0.1)
        self.upload_progress_dialog.set_progress(currentProgress)
        self.layer_upload_helper.upload_layer(layer_upload_info)

    def _on_layer_uploaded_for_upload_map(self, layer_upload_info: Optional[LayerUploadInfo]):
        if layer_upload_info is not None:
            self.upload_progress_dialog.set_progress(self.upload_progress_dialog.get_progress() + layer_upload_info.size)
        info_complete_layers = [lui for lui in self.layer_upload_helper.layers_upload_info if lui.status == LayerUploadStatus.COMPLETE]
        info_failed_layers = [lui for lui in self.layer_upload_helper.layers_upload_info if lui.status == LayerUploadStatus.FAILED]
        if len(info_failed_layers) == len(self.layer_upload_helper.layers_upload_info):
            self.disconnect_signal(self.layer_upload_helper.layer_uploaded, self._on_layer_uploaded_for_upload_map)
            self.disconnect_signal(self.layer_upload_helper.layer_upload_failed, self._on_layer_failed_for_upload_map)
            self._on_map_creation_failed(None)

        if len(info_failed_layers) + len(info_complete_layers) == len(self.layer_upload_helper.layers_upload_info):
            self.disconnect_signal(self.layer_upload_helper.layer_uploaded, self._on_layer_uploaded_for_upload_map)
            self.disconnect_signal(self.layer_upload_helper.layer_upload_failed, self._on_layer_failed_for_upload_map)

            self.delete_temp_folder()
            map_layer_parameters = []
            for info_complete_layer in info_complete_layers:
                map_layer_parameters.append(({
                    "identifier": info_complete_layer.cv_id,
                    "type": "Interactive"
                }))
            layer_names = [info_complete_layer.layer_name for info_complete_layer in info_complete_layers]
            self.get_map_name(layer_names)
            API_CLIENT.create_map_api(self.map_name, map_layer_parameters, self._update_slide, self._on_map_creation_failed)

    def _on_layer_failed_for_upload_map(self, e):
        self._on_layer_uploaded_for_upload_map(None)

    def create_map_from_uploaded_layer(self):
        self.upload_complete_dialog.close()
        map_layer_parameters = [{
                    "identifier": self.layer_upload_helper.layers_upload_info[0].cv_id,
                    "type": "Interactive"
                }]
        self.map_name = self.layer_upload_helper.layers_upload_info[0].layer_name
        API_CLIENT.create_map_api(self.map_name, map_layer_parameters, self._update_slide, self._on_map_creation_failed)

    def _on_map_creation_success(self, cv_map: Map):
        self.map_name = cv_map.title
        self.upload_progress_dialog.set_progress(self.upload_progress_dialog.get_maximum())
        self.upload_progress_dialog.close()
        upload_failed_layer_names = [layer_info.layer_name for layer_info in self.layer_upload_helper.layers_upload_info if layer_info.status == LayerUploadStatus.FAILED]
        self.upload_complete_dialog.map_success(self.map_name, self.construct_map_url(API_CLIENT.tenant_url_code, cv_map.vanity_url), self.layer_upload_helper.invalid_layer_names, upload_failed_layer_names)
        self.iface.messageBar().pushMessage("Map created", level=Qgis.MessageLevel.Info)
    
    def _update_slide(self, cv_map: Map):
        layers_need_slide_update = [lui for lui in self.layer_upload_helper.layers_upload_info if lui.status == LayerUploadStatus.COMPLETE and (lui.add_cv_labels or lui.opacity != 1)]
        if len(layers_need_slide_update) == 0:
            self._on_map_creation_success(cv_map)
            return
        API_CLIENT.get_map_slides(cv_map.unique_identifier, partial(self._update_slide_2, cv_map), partial(self._on_update_slide_failed, cv_map))
    
    def _update_slide_2(self, cv_map: Map, slides: List[Slide]):
        if len(slides) < 1: 
            self._on_map_creation_success(cv_map)
            return
        theme_set_group = generate_theme_set_group(self.layer_upload_helper.layers_upload_info)
        API_CLIENT.update_slide_themeset(slides[0].id, theme_set_group, partial(self._on_update_slide_success, cv_map), partial(self._on_update_slide_failed, cv_map))
    
    def _on_update_slide_failed(self, cv_map: Map, e):
        self._on_map_creation_success(cv_map)

    def _on_update_slide_success(self, cv_map: Map, _):
        self._on_map_creation_success(cv_map)

    def _on_map_creation_failed(self, e: Optional[Exception] = None):
        self.delete_temp_folder()
        self.upload_progress_dialog.close()
        self.upload_complete_dialog.map_failed(self.map_name)

    def layer_tree_view_menu(self, menu: QMenu):
        """
        Triggered when the layer tree menu is about to show
        """
        if not menu:
            return

        current_node = self.iface.layerTreeView().currentNode()
        if not isinstance(current_node, QgsLayerTreeLayer):
            return

        layer = current_node.layer()
        if layer is None:
            return
       
        menus = [action for action in menu.children() if
                    isinstance(action, QMenu) and
                    action.objectName() == 'exportMenu']
        if not menus:
            return

        export_menu = menus[0]

        is_supported = HelperFunctions.is_supported_layer(layer)
        text = "Share Layer to CartoVista" if is_supported else "Share Layer to CartoVista (unsupported layer type)"
        self.share_layer_action = QAction(self.tr(text), menu)
        self.share_layer_action.setIcon(QIcon(GuiUtils.get_icon('icon.png')))
       
        self.share_layer_action.setEnabled(is_supported)
        export_menu.addAction(self.share_layer_action)        
        self.share_layer_action.triggered.connect(partial(self.upload_layer_pre_dialog, layer))

    def set_share_map_state(self, _ = None):
        supported = False
        layers = QgsProject.instance().mapLayers().values()
        layer_tree_root = QgsProject.instance().layerTreeRoot()
        if len(layers) > 0:
            for layer in QgsProject.instance().mapLayers().values():
                layer_tree_layer = layer_tree_root.findLayer(layer.id())
                if layer_tree_layer is None:
                    continue
                is_visible = layer_tree_layer.isVisible()
                if HelperFunctions.is_supported_layer(layer) and is_visible:
                    supported = True
                    break
        self.share_map_action.setEnabled(supported)
        tooltip = "" if supported else "No supported layers present in map. Point, line and polygon layers are supported"
        self.share_map_action.setToolTip(tooltip)

    def _on_authenticated(self):
        API_CLIENT.get_current_organization(self._on_fetch_organization, self._on_authentication_error)

    def _on_fetch_organization(self, org: Organization):
        API_CLIENT.tenant_url_code = org.url_code
        self.organization = org
        API_CLIENT.get_current_user(self._on_fetch_user, self._on_authentication_error)

    def _on_fetch_user(self, user: User):
        self.user = user
        self.set_user_and_organization_in_dialogs(self.user.email_address, self.organization.name)
        self.open_upload_dialog()

    def open_upload_dialog(self):
            if self.layer_to_upload is not None:
                self.open_upload_layer_dialog()
            else:
                self.open_upload_map_dialog()

    def _on_authentication_error(self, _):
        AUTHORIZATION_MANAGER.deauthenticate()

    def close_all_dialogs(self):
        self.pre_upload_dialog.close()
        self.upload_progress_dialog.close()
        self.upload_complete_dialog.close()
        self.authorize_dialog.close()
        self.master_password_dialog.close()

    def _on_deauthenticated(self):
        self.close_all_dialogs()
        self.set_user_and_organization_in_dialogs(None, None)
        if (self.layer_to_upload is not None):
            self.upload_layer_pre_dialog(self.layer_to_upload)
        else:
            self.upload_map_pre_dialog()

    def set_user_and_organization_in_dialogs(self, email: Optional[str], org_name: Optional[str]):
        self.pre_upload_dialog.set_email_and_organization(email, org_name)
        self.upload_progress_dialog.set_email_and_organization(email, org_name)
        self.upload_complete_dialog.set_email_and_organization(email, org_name)

    def disconnect_signal(self, signal, method):
        try:
            signal.disconnect(method)
        except TypeError:
            pass


    def construct_map_url(self, tenant_code, map_vanity_url):
        return f"{DEPLOYMENT_URL}/{tenant_code}/maps/{map_vanity_url}"


    def on_password_helper_failure(self):
        if platform.system() == "Darwin":
            self.mac_os_keychain_permission_issue = True

    def delete_temp_folder(self):
        # Delete temp folder and content
        if self.temp_dir is None: return
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except OSError as e:
            self.iface.messageBar().pushMessage("Error deleting temp folder",  "Error: " + str(self.temp_dir) +" : "+str(e.strerror), level=Qgis.MessageLevel.Critical)
        finally:
            self.temp_dir = None


    def verify_master_password(self):
        isSet = QgsApplication.authManager().setMasterPassword()
        if not isSet:
            self.master_password_dialog.show()
        else:
            AUTHORIZATION_MANAGER.try_authenticate()

    def on_show_authorize_dialog(self):
        self.authorize_dialog.open(self.mac_os_keychain_permission_issue)
