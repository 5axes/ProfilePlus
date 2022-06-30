from UM.Settings.Models.SettingVisibilityHandler import SettingVisibilityHandler
from UM.Application import Application

from UM.FlameProfiler import pyqtSlot


class ProfilePlusSettingsVisibilityHandler(SettingVisibilityHandler):
    '''Create a custom visibility handler so we can hide/show settings in the dialogs.'''

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)

        self._preferences = Application.getInstance().getPreferences()
        self._preferences.preferenceChanged.connect(self._onPreferencesChanged)

        self._onPreferencesChanged("profile_plus/logged_settings")
        self.visibilityChanged.connect(self._updatePreference)

    def _onPreferencesChanged(self, name: str) -> None:
        if name != "profile_plus/logged_settings":
            return

        visibility_string = self._preferences.getValue(
            "profile_plus/logged_settings")
        if not visibility_string:
            self._preferences.resetPreference(
                "profile_plus/logged_settings")
            return

        profile_plus_settings = set(visibility_string.split(";"))
        if profile_plus_settings != self.getVisible():
            self.setVisible(profile_plus_settings)

    def _updatePreference(self) -> None:
        visibility_string = ";".join(self.getVisible())
        self._preferences.setValue(
            "profile_plus/logged_settings", visibility_string)

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
