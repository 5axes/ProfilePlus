// Copyright (c) 2023 5@xes
// proterties values
//   "SParam"         : Text for test parameter

import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Dialogs 6.2
import QtQuick.Layouts 6.0

import UM 1.6 as UM
import Cura 1.7 as Cura


UM.Dialog
{
    id: popupDialog
    minimumWidth: 650
    minimumHeight: 250

    property variant i18n_catalog: UM.I18nCatalog { name: "profileplus" }
	
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
            text: i18n_catalog.i18nc("@action:button", "Close");
            onClicked: {
                popupDialog.visible = false;
            }
        }
    ]	
}