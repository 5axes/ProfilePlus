import json
import os
import time
import collections
from typing import Optional, TYPE_CHECKING

USE_QT5 = False
try:
    from PyQt6.QtQml import qmlRegisterType
    from PyQt6.QtCore import QObject, QBuffer
    from PyQt6.QtNetwork import QNetworkRequest
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtGui import QPixmap
    if TYPE_CHECKING:
        from PyQt6.QtNetwork import QNetworkReply
except ImportError:
    from PyQt5.QtQml import qmlRegisterType
    from PyQt5.QtCore import QObject, QBuffer
    from PyQt5.QtNetwork import QNetworkRequest
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtGui import QPixmap
    if TYPE_CHECKING:
        from PyQt5.QtNetwork import QNetworkReply
    USE_QT5 = True

from cura.CuraApplication import CuraApplication

from UM.Extension import Extension
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from UM.Qt.Duration import DurationFormat

from cura import ApplicationMetadata

from . import ProfilePlusSettingsVisibilityHandler
from . import ProfilePlusSettingDefinitionsModel

if TYPE_CHECKING:
    from PyQt6.QtNetwork import QNetworkReply


catalog = i18nCatalog("cura")


class ProfilePlusUploader(QObject, Extension):
    '''This extension lets a user to create a new print on https://www.3dProfilePlus.com when saving a print in Cura.
    3D Print Logs's new print form is pre-populated by Cura's print settings and estimated print time/filament.
    Requires the user to have an account and be logged into 3D Print Log before they can save any information.
    '''

    plugin_version = ""


    default_logged_settings = {
        "layer_height",
        "line_width",
        "wall_line_count",
        "top_thickness",
        "bottom_thickness",
        "infill_sparse_density",
        "infill_pattern",
        "material_print_temperature",
        "material_bed_temperature",
        "speed_print",
        "cool_fan_enabled",
        "cool_fan_speed",
        "support_enable",
        "support_structure",
        "support_type",
        "adhesion_type",
    }

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        Extension.__init__(self)

        self._application = CuraApplication.getInstance()


        ## Load the plugin version
        pluginInfo = json.load(open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "plugin.json")))
        self.plugin_version = pluginInfo['version']

        self.addMenuItem("Configure Settings", self.showSettingsDialog)

        self._application.getPreferences().addPreference(
            "profile_plus/logged_settings",
            ";".join(self.default_logged_settings)
        )


        # Transfer deprecated bypass_prompt to the new combobox value:
        bypass_prompt = self._application.getPreferences().getValue(
                "profile_plus/bypass_prompt")
        if (bypass_prompt is not None):
            if (bypass_prompt):
                self._application.getPreferences().setValue(
                    "profile_plus/prompt_settings",
                    "send_after_save"
                )
            # Remove the deprecated value
            self._application.getPreferences().removePreference(
                "profile_plus/bypass_prompt")


        self._application.engineCreatedSignal.connect(self._onEngineCreated)



    def _onEngineCreated(self):
        qmlRegisterType(
            ProfilePlusSettingsVisibilityHandler.ProfilePlusSettingsVisibilityHandler,
            "Cura", 1, 0, "ProfilePlusSettingsVisibilityHandler"
        )

    def showSettingsDialog(self):
        path = None
        if USE_QT5:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt5", "SettingsDialog.qml")
        else:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt6","SettingsDialog.qml")

        self._settings_dialog = CuraApplication.getInstance(
        ).createQmlComponent(path, {"manager": self})
        self._settings_dialog.show()


