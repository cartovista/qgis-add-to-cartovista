"""
GUI Utilities
"""

import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import (
    QIcon,
)


class GuiUtils:
    """
    Utilities for GUI plugin components
    """

    @staticmethod
    def get_icon(icon: str) -> QIcon:
        """
        Returns a plugin icon
        :param icon: icon name (png file name)
        :return: QIcon
        """
        path = GuiUtils.get_icon_png(icon)
        if not path:
            return QIcon()

        return QIcon(path)

    @staticmethod
    def get_icon_png(icon: str) -> str:
        """
        Returns a plugin icon's PNG file path
        :param icon: icon name (png file name)
        :return: icon png path
        """
        path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'assets',
            icon)
        if not os.path.exists(path):
            return ''

        return path

    @staticmethod
    def get_ui_file_path(file: str) -> str:
        """
        Returns a UI file's path
        :param file: file name (uifile name)
        :return: ui file path
        """
        path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'dialogs',
            file)
        if not os.path.exists(path):
            return ''

        return path
