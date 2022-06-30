// Copyright (c) 2022 5@xes
// The ProfilePlus Plugin is released under the terms of the AGPLv3 or higher.

import QtQuick 
import QtQuick.Controls
import QtQuick.Window 
import QtQuick.Layouts 

import UM  as UM
import Cura  as Cura
import ProfilePlusUploader  as ProfilePlusUploader

UM.Dialog {
    id: settingsDialog

    title: catalog.i18nc("@title:window", "Select Settings to Reset")
    width: screenScaleFactor * 360

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



        Item
        {
            //: Spacer
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        }

        Label
        {
            id: settingLabel
            font.bold: true
            text: "Settings"
        }

        Row {
            id: settingSearchRow
            Layout.fillWidth: true

            TextField {

                id: filterInput
                width: settingSearchRow.width - searchSpacer.width - toggleShowAll.width
                placeholderText: catalog.i18nc("@label:textbox", "Filter...");

                onTextChanged: settingsDialog.updateFilter()
            }

            Item
            {
                id: searchSpacer
                //: Spacer
                height: UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("default_margin").width
            }

            CheckBox
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
                model: ProfilePlusUploader.ProfilePlusSettingDefinitionsModel
                {
                    id: definitionsModel;
                    containerId: Cura.MachineManager.activeMachine.definition.id
                    visibilityHandler: Cura.ProfilePlusSettingsVisibilityHandler {}
                    showAll: true
                    showAncestors: true
                    expanded: [ "*" ]
                    exclude: [ "machine_settings", "command_line_settings" ]
                }
                delegate:Loader
                {
                    id: loader

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
        Button {
            anchors {
                rightMargin: UM.Theme.getSize("default_margin").width
            }
            
            text: catalog.i18nc("@action:button", "Reset To Defaults");
            onClicked: {
                UM.Preferences.resetPreference("profile_plus/logged_settings")
                

                settingsDialog.visible = false;
            }
        },
        Item
        {
            //: Spacer
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        },
        Button {
            text: catalog.i18nc("@action:button", "Close");
            onClicked: {
                settingsDialog.visible = false;
            }
        }
    ]

    Item
    {
        UM.I18nCatalog { id: catalog; name: "cura"; }
    }
}
