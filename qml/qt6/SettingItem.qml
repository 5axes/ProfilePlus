// Copyright (c) 2022 5@xes
// The ProfilePlus Plugin is released under the terms of the AGPLv3 or higher.

import QtQuick
import QtQuick.Controls

import UM 1.6 as UM

UM.TooltipArea
{
    x: model.depth * UM.Theme.getSize("narrow_margin").width
    text: model.description

    width: childrenRect.width
    height: childrenRect.height

    UM.CheckBox
    {
        id: check
        text: definition.label
        checked: definition.visible;

        onClicked:
        {
            definitionsModel.visibilityHandler.setSettingVisibility(model.key, checked);
        }
    }
}
