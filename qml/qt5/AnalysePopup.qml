// Copyright (c) 2023 5@xes

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.11
import QtQuick.Dialogs 1.0

import UM 1.1 as UM
import Cura 1.0 as Cura


UM.Dialog
{
    id: popupDialog
    minimumWidth: 650
    minimumHeight: 250

	property variant i18n_catalog: UM.I18nCatalog { name: "profilplus" }
	
    title: i18n_catalog.i18nc("@title", "Profile Plus Current Profile : ") + manager.profileName

	TextArea {
		id: inputfg
		width: parent.width
		anchors
		{
			top: parent.top
			bottom: parent.bottom
			bottomMargin: UM.Theme.getSize("default_margin").height
		}

		// font.family: "Courier New"
		wrapMode: Text.WordWrap 
		textFormat : Text.PlainText
		text: manager.paramSetting
	}

    rightButtons: [ 
        Button {
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
        Button {
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
        Button {
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
        Button {
            text: i18n_catalog.i18nc("@action:button", "Close");
            onClicked: {
                popupDialog.visible = false;
            }
        }
    ]	
}