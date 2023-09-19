// Copyright (c) 2023 5@xes
// The ProfilePlus Plugin is released under the terms of the AGPLv3 or higher.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import UM 1.6 as UM
import Cura 1.7 as Cura

UM.Dialog
{
    id: popupDialog
    minimumWidth: 650
    minimumHeight: 250

    property variant i18n_catalog: UM.I18nCatalog { name: "profilplus" }
	
	function getValue()
	{
		// Convert the path to a usable url
		var url = ""
		url = manager.testMachineProfile
		return url
	}
	
    title: i18n_catalog.i18nc("@title", "Profile Plus Current Profile : ") + manager.profileName

	Cura.ScrollableTextArea {
		id: inputfg
		width: parent.width
		anchors
		{
			top: parent.top
			bottom: parent.bottom
			bottomMargin: UM.Theme.getSize("default_margin").height
		}

		// font.family: "Courier New"
		textArea.wrapMode: Text.WordWrap 
		textArea.textFormat : Text.PlainText
		textArea.text: manager.paramSetting
	}

    rightButtons: [ 
        Cura.PrimaryButton {
            anchors {
                rightMargin: UM.Theme.getSize("default_margin").width
            }
			
            tooltip: i18n_catalog.i18nc("@tooltip:button", "Delete every parameters set in your current profile which are also present in the active Material settings")
            text: i18n_catalog.i18nc("@action:button", "Remove Parameters")
            onClicked: {
                manager.cleanProfile
            }
        },
        Item
        {
            //: Spacer
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        },
        Cura.PrimaryButton {
            anchors {
                rightMargin: UM.Theme.getSize("default_margin").width
            }
			
            tooltip: i18n_catalog.i18nc("@tooltip:button", "Delete every parameters set in your current profile which are also present in every material definitions associated with this machine")
            text: i18n_catalog.i18nc("@action:button", "Remove Materials Parameters")
            onClicked: {
                manager.cleanMachineProfile
            }
        },
        Item
        {
            //: Spacer
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        },
        Cura.PrimaryButton {
            anchors {
                rightMargin: UM.Theme.getSize("default_margin").width
            }
            tooltip: i18n_catalog.i18nc("@tooltip:button", "Link the settings present in the Material definition with your current settings.")
            text: i18n_catalog.i18nc("@action:button", "Link Parameters")
            onClicked: {
                manager.linkProfile
            }
        },		
        Item
        {
            //: Spacer
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        },		
        Cura.PrimaryButton {
			tooltip: i18n_catalog.i18nc("@tooltip:button", "Close this windows")
            text: i18n_catalog.i18nc("@action:button", "Close");
            onClicked: {
                popupDialog.visible = false;
            }
        }
    ]	
}