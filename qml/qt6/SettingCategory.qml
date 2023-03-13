// Copyright (c) 2022 5@xes
// The ProfilePlus Plugin is released under the terms of the AGPLv3 or higher.

import QtQuick
import QtQuick.Controls

import Cura 1.5 as Cura
import UM 1.5 as UM

Cura.CategoryButton
{
    id: base;
	
    categoryIcon: definition ? UM.Theme.getIcon(definition.icon) : ""
    labelText: definition ? definition.label : ""
    expanded: definition ? definition.expanded : false

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()

    onClicked: expanded ? settingDefinitionsModel.collapseRecursive(definition.key) : settingDefinitionsModel.expandRecursive(definition.key)
}
