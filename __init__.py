from . import ProfilePlusEdit
from . import ProfilePlusSettingDefinitionsModel

USE_QT5 = False
try:
    from PyQt6.QtQml import qmlRegisterType
except ImportError:
    from PyQt5.QtQml import qmlRegisterType
    USE_QT5 = True


def getMetaData():
    return {}


def register(app):
    qmlRegisterType(ProfilePlusSettingDefinitionsModel.ProfilePlusSettingDefinitionsModel,
                    "ProfilePlusEdit", 1, 0, "ProfilePlusSettingDefinitionsModel")

    return {"extension": ProfilePlusEdit.ProfilePlusEdit()}
