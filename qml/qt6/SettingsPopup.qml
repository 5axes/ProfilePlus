// Copyright (c) 2023 5@xes

import QtQuick
import QtQuick.Controls

import UM 1.6 as UM

UM.Dialog
{
    minimumWidth: 400
    minimumHeight: 60
	
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

    property variant i18n_catalog: UM.I18nCatalog { name: "profileplus" }
	
    title: i18n_catalog.i18nc("@title", "Profile Plus plugin settings")

    UM.CheckBox
    {
        checked: boolCheck(UM.Preferences.getValue("profile_plus/advanced_login"))
        onClicked: UM.Preferences.setValue("profile_plus/advanced_login", checked)

        text: i18n_catalog.i18nc("@label", "Advanced Login (restart Cura to apply change)")
    }
	
}