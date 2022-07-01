# Profile Plus

The plugin allows to delete parameters defined in a profile. 

**! Be careful, the deletion is direct without the possibility to cancel the action !**

## Purpose of the plugin

There are often requests for the possibility of defining, for example, a flow rate in the material definition. The problem is that the custom profile settings overwrite this data. The only solution I know is to edit the profile manualy via a text editor and delete the unnecessary parameter.

This Plugin allows you to delete in the active profile some parameters already defined. 



## Installation
First, make sure your Cura version is  4.4 or newer.

Manual Install Download & extract the repository as ZIP or clone it. Copy the files/plugins/ProfilePlus directory to:

on Windows: [Cura installation folder]/plugins/ProfilePlus

on Linux: ~/.local/share/cura/[YOUR CURA VERSION]/plugins/ProfilePlus (e.g. ~/.local/share/cura/4.6/plugins/ProfilePlus)

on Mac: ~/Library/Application Support/cura/[YOUR CURA VERSION]/plugins/ProfilePlus


## How to use

![Menu](./images/menu.png)

First of all you must activate the profile you want to edit.
Then use the function **Configure Settings** to activate the windows where you will have every parameters set in your current profile.

![Reset](./images/reset.png)

Just untick the parameters you want to delete from the Profile and press the Button **Update current Profile parameters**

The list of the suppressed parameters will be displayed in a Cura message :

![Message](./images/message.png)
