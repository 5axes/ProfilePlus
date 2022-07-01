# Source origine FiledOfView
from UM.Settings.Models.SettingVisibilityHandler import SettingVisibilityHandler
from UM.Application import Application

from UM.FlameProfiler import pyqtSlot

from UM.Logger import Logger
from UM.Message import Message

from UM.i18n import i18nCatalog
i18n_cura_catalog = i18nCatalog('cura')



class ProfilePlusSettingsVisibilityHandler(SettingVisibilityHandler):
    '''Create a custom visibility handler so we can hide/show settings in the dialogs.'''

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)

        self._preferences = Application.getInstance().getPreferences()
        self._preferences.preferenceChanged.connect(self._onPreferencesChanged)

        self._onPreferencesChanged("profile_plus/profile_settings")
        self.visibilityChanged.connect(self._updatePreference)

    def _onPreferencesChanged(self, name: str) -> None:
        if name != "profile_plus/profile_settings":
            return
        
        visibility_string = self._preferences.getValue("profile_plus/profile_settings")
            
        # Logger.log('d', "New Visibility_string : {}".format(visibility_string))
        
        if not visibility_string:
            # self._preferences.resetProfileSettings("profile_plus/profile_settings")
            Message(text = "Standard settings or Profile without settings", title = i18n_cura_catalog.i18nc("@info:title", "Warning ! Profile Plus"), message_type = Message.MessageType.WARNING).show()
            return

        profile_plus_settings = set(visibility_string.split(";"))
        if profile_plus_settings != self.getVisible():
            self.setVisible(profile_plus_settings)

    def _updatePreference(self) -> None:
        visibility_string = ";".join(self.getVisible())
        self._preferences.setValue("profile_plus/profile_settings", visibility_string)
        # Logger.log('d', "UpdatePreference : {}".format(visibility_string))

    # Set a single SettingDefinition's visible state
    @pyqtSlot(str, bool)
    def setSettingVisibility(self, key: str, visible: bool) -> None:
        visible_settings = self.getVisible()
        if visible:
            visible_settings.add(key)
        else:
            try:
                visible_settings.remove(key)
            except KeyError:
                pass

        self.setVisible(visible_settings)
