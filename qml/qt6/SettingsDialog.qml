// Copyright (c) 2023 5@xes
// The ProfilePlus Plugin is released under the terms of the AGPLv3 or higher.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import UM 1.6 as UM
import Cura 1.7 as Cura
import ProfilePlus as ProfilePlus

UM.Dialog {
    id: settingsDialog

    title: catalog.i18nc("@title:window", "Select settings to delete from : ") + manager.profileName
    // width: screenScaleFactor * 360

    onVisibilityChanged:
    {
        if(visible)
        {
            updateFilter()
        }
    }

    function updateFilter()
    {
        var new_filter = {};

        if(filterInput.text != "")
        {
            new_filter["i18n_label"] = "*" + filterInput.text;
        }

        listview.model.filter = new_filter;
    }

    ColumnLayout
    {
        anchors.fill: parent

        UM.Label
        {
            id: settingLabel
            font.bold: true
            text: catalog.i18nc("@label", "Settings")
        }

        Row {
            id: settingSearchRow
            Layout.fillWidth: true

            Cura.TextField {

                id: filterInput
                width: settingSearchRow.width - searchSpacer.width - toggleShowAll.width
                placeholderText: catalog.i18nc("@label:textbox", "Filter...");

                onTextChanged: settingsDialog.updateFilter()
            }

            Item
            {
                id: searchSpacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").width
            }

            UM.CheckBox
            {
                id: toggleShowAll            
                text: catalog.i18nc("@label:checkbox", "Show all")
                checked: listview.model.showAll
                onClicked:
                {
                    listview.model.showAll = checked;
                }
            }
        }

        ScrollView
        {
            id: scrollView
            Layout.fillHeight: true
            Layout.fillWidth: true

            ListView
            {
                id:listview
                model: ProfilePlus.ProfilePlusSettingDefinitionsModel
                {
                    id: definitionsModel
                    containerId: Cura.MachineManager.activeMachine.definition.id
                    visibilityHandler: Cura.ProfilePlusSettingsVisibilityHandler {}
                    showAll: false
                    showAncestors: true
                    expanded: [ "*" ]
                    exclude: [ "machine_settings", "command_line_settings" ]
                }
                delegate:Loader
                {
                    id: loader

                    // width: UM.Theme.getSize("setting_control").width
					width: parent.width
                    height: model.type != undefined ? UM.Theme.getSize("section").height : 0;

                    property var definition: model
                    property var settingDefinitionsModel: definitionsModel

                    asynchronous: true
                    source:
                    {
                        switch(model.type)
                        {
                            case "category":
                                return "SettingCategory.qml"
                            default:
                                return "SettingItem.qml"
                        }
                    }
                }
                Component.onCompleted: settingsDialog.updateFilter()
            }
        }
    }
    
    rightButtons: [
        Cura.PrimaryButton {
            anchors {
                rightMargin: UM.Theme.getSize("default_margin").width
            }
            
            text: catalog.i18nc("@action:button", "Update current Profile Parameters")
            onClicked: {
                // UM.Preferences.resetProfileSettings("profile_plus/profile_settings")
                manager.upDate
                // settingsDialog.visible = false;
            }
        },
        Item
        {
            //: Spacer
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        },
        Cura.PrimaryButton {
            text: catalog.i18nc("@action:button", "Close");
            onClicked: {
                settingsDialog.visible = false;
            }
        }
    ]

    Item
    {
        UM.I18nCatalog { id: catalog; name: "profilplus"; }
    }
}
