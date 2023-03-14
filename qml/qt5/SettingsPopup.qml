// Copyright (c) 2023 5@xes

import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.2 as UM

UM.Dialog
{
    minimumWidth: 400
    minimumHeight: 60
	
	property variant i18n_catalog: UM.I18nCatalog { name: "profilplus" }
	
    function boolCheck(value) //Hack to ensure a good match between python and qml.
    {
        if(value == "True")
        {
            return true
        }else if(value == "False" || value == undefined)
        {
            return false
        }
        else
        {
            return value
        }
    }
	
    title: i18n_catalog.i18nc("@title", "Profile Plus plugin settings")

    CheckBox
    {
        checked: boolCheck(UM.Preferences.getValue("profile_plus/advanced_login"))
        onClicked: UM.Preferences.setValue("profile_plus/advanced_login", checked)

        text: i18n_catalog.i18nc("@label", "Advanced Login (restart Cura to apply change)")
    }
}