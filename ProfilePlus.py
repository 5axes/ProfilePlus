#--------------------------------------------------------------------------------------------
# Initial Copyright(c) FieldofView for the SettingsVisibilityHandler 
# Copyright (c) 2022 5axes
#--------------------------------------------------------------------------------------------
# All modification 5@xes
# First release  01-07-2022  First proof of concept
#------------------------------------------------------------------------------------------------------------------
# 1.0.0 01-07-2022  First release to test the concept
#------------------------------------------------------------------------------------------------------------------
import os
import os.path
import tempfile
import html
import json
import re
import webbrowser
  

USE_QT5 = False
try:
    from PyQt6.QtGui import QDesktopServices
    from PyQt6.QtQml import qmlRegisterType
    from PyQt6.QtCore import QObject, QBuffer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
except ImportError:
    from PyQt5.QtQml import qmlRegisterType
    from PyQt5.QtCore import QObject, QBuffer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
    from PyQt5.QtGui import QDesktopServices
    USE_QT5 = True

from cura.CuraApplication import CuraApplication

from UM.Extension import Extension

from UM.PluginRegistry import PluginRegistry
from UM.Qt.Duration import DurationFormat

from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.CuraVersion import CuraVersion  # type: ignore
# from UM.Version import Version

from cura.CuraApplication import CuraApplication


from UM.Logger import Logger
from UM.Message import Message

from . import ProfilePlusSettingsVisibilityHandler
from . import ProfilePlusSettingDefinitionsModel

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")
i18n_cura_catalog = i18nCatalog('cura')
i18n_catalog = i18nCatalog('fdmprinter.def.json')
i18n_extrud_catalog = i18nCatalog('fdmextruder.def.json')

encode = html.escape


class ProfilePlus(QObject, Extension):
    #Create an api
    from cura.CuraApplication import CuraApplication
    api = CuraApplication.getInstance().getCuraAPI()

    plugin_version = ""
    visibility_string = ""

    userAction = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        Extension.__init__(self)

        self._application = CuraApplication.getInstance()

        ## Load the plugin version
        pluginInfo = json.load(open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "plugin.json")))
        self.plugin_version = pluginInfo['version']
        Logger.log("d", "Plugin version : %s", self.plugin_version )

        ## Menu    
        self.addMenuItem("Remove Settings", self.showSettingsDialog)
        self.addMenuItem("View Active Profile", viewProfile)
        self.addMenuItem("View Active Configuration", viewAll)

        self._application.getPreferences().addPreference("profile_plus/profile_settings",";")

        self._application.engineCreatedSignal.connect(self._onEngineCreated)



    def _onEngineCreated(self):
        qmlRegisterType(
            ProfilePlusSettingsVisibilityHandler.ProfilePlusSettingsVisibilityHandler,
            "Cura", 1, 0, "ProfilePlusSettingsVisibilityHandler"
        )

    def showSettingsDialog(self):
        self.visibility_string=updateVisibility()
        Logger.log("d", "showSettingsDialog Profile Visibility_string : %s", self.visibility_string )  
        self._application.getPreferences().setValue("profile_plus/profile_settings", self.visibility_string)
        
        path = None
        if USE_QT5:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt5", "SettingsDialog.qml")
        else:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt6","SettingsDialog.qml")

        self._settings_dialog = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})
        self._settings_dialog.show()


    @pyqtProperty(str, notify= userAction)
    def upDate(self)-> None:
        modi = ''
        self.visibility_string=self._application.getPreferences().getValue("profile_plus/profile_settings")
        Logger.log("d", "Update Visibility_string : %s", self.visibility_string )
        modi += upDateExtruderStacks(self.visibility_string)
        modi += upDateContainerStack(Application.getInstance().getGlobalContainerStack(),self.visibility_string)
        # 
        # Logger.log("d", "Update Visibility_string : %s", self.visibility_string ) 
        if modi == "" :
            Message(text = "! Error Nothing to do !", title = catalog.i18nc("@info:title", "Profile Plus ") + str(self.plugin_version), message_type = Message.MessageType.ERROR).show()
        else :
            Message(text = "! Modification ok for : %s" % (modi), title = catalog.i18nc("@info:title", "Profile Plus ") + str(self.plugin_version), message_type = Message.MessageType.POSITIVE).show()        
        
def upDateExtruderStacks(visibility_string):
    modi = ''
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in Application.getInstance().getExtruderManager().getActiveExtruderStacks():
        modi += upDateContainerStack(extruder_stack, visibility_string)
        position += 1
    return modi

def upDateContainerStack(Cstack, visibility_string):
    modi = ''
    Logger.log("d", "upDateContainerStack : %s", visibility_string )
    profile_plus_settings = visibility_string.split(";")
    for container in Cstack.getContainers():
        # Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == "quality_changes" :
            keys = list(container.getAllKeys())
            for key in keys:
                # visi += formatSettingsKeyTableRow(key, formatSettingValue(container, key, key_properties))
                # Logger.log("d", "key :|%s|", key )
                # Naive Method :)
                delRef = True
                for iList in profile_plus_settings:
                    if (iList == key) :
                        delRef = False
                        # Logger.log("d", "iList :|%s|", iList )
                        
                if delRef == True :
                    # The point of no return, will remove the parameter
                    # https://community.ultimaker.com/topic/40968-container-removeinstance-goal-of-the-option-postpone_emit/
                    container.removeInstance(key, postpone_emit=True)
                    modi += key
                    modi += "\n"
    return modi

    
def viewAll():
    HtmlFile = str(CuraVersion).replace('.','-') + '_cura_settings.html'
    openHtmlPage(HtmlFile, htmlPage())

def viewProfile():
    HtmlFile = str(CuraVersion).replace('.','-') + '_cura_profile.html'
    openHtmlPage(HtmlFile, htmlBasePage())   

def updateVisibility():
    visi = ""
    visi += formatExtruderVisibilityStacks()
    visi += formatContainerVisibilityStack(Application.getInstance().getGlobalContainerStack())

    return visi

def formatExtruderVisibilityStacks():
    visi = ''
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in Application.getInstance().getExtruderManager().getActiveExtruderStacks():
        visi += formatContainerVisibilityStack(extruder_stack)
        position += 1
    return visi

def formatContainerVisibilityStack(Cstack, show_stack_keys=True):
    visi = ''
    for container in Cstack.getContainers():
        Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == "quality_changes" :
            keys = list(container.getAllKeys())
            for key in keys:
                # visi += formatSettingsKeyTableRow(key, formatSettingValue(container, key, key_properties))
                visi += key
                visi += ";"
    return visi

    
def htmlPage():
    html = getHtmlHeader()

    # Menu creation
    html += '<div class="menu">\n'
    html += '<ul>'
 

    html += '<li><a href="#extruder_stacks">Extruder Stacks</a>\n'
    html += formatExtruderStacksMenu()
    html += '</li>\n'

    html += '<li><a href="#global_stack">Global Stack</a>'
    html += formatContainerStackMenu(Application.getInstance().getGlobalContainerStack())
    html += '</li>\n'

    html += '</ul>\n'
    
    # Java script filter function
    html += keyFilterWidget()
    html += '</div>'

    # Contents creation
    html += '<div class="contents">'
    html += formatExtruderStacks()
     
    html += '<h2 id="global_stack">Global Stack</h2>'
    html += formatContainerStack(Application.getInstance().getGlobalContainerStack())
    
    html += '</div>'

    html += htmlFooter
    return html

def htmlBasePage():
    html = getHtmlHeader()

    # Menu creation
    html += '<div class="menu">\n'
    html += '<ul>'
 

    html += '<li><a href="#extruder_stacks">Extruder Stacks</a>\n'
    html += formatExtruderBaseStacksMenu()
    html += '</li>\n'

    html += '<li><a href="#global_stack">Global Stack</a>'
    html += formatContainerBaseStackMenu(Application.getInstance().getGlobalContainerStack())
    html += '</li>\n'

    html += '</ul>\n'
    
    html += '</div>'

    # Contents creation
    html += '<div class="contents">'
    html += formatExtruderBaseStacks()
     
    html += '<h2 id="global_stack">Global Stack</h2>'
    html += formatContainerBaseStack(Application.getInstance().getGlobalContainerStack())
    
    html += '</div>'

    html += htmlFooter
    return html
    
# Change the 'quality_type' to 'standard' if 'not_supported'
def changeToStandardQuality():
    #stack = Application.getInstance().getGlobalContainerStack()

    machine_manager = Application.getInstance().getMachineManager()
    g_stack = machine_manager.activeMachine
    machine_id=str(g_stack.quality.getMetaDataEntry('definition'))
    
    if machine_id == '' or machine_id == 'None':
        machine_quality_changes = machine_manager.activeMachine.qualityChanges
        machine_id=str(machine_quality_changes.getMetaDataEntry('definition'))
    
    # Logger.log("d", "First Machine_id : %s", machine_id )    
    containers = ContainerRegistry.getInstance().findInstanceContainers(definition = machine_id, type='quality')
    
    liste_quality = []
    for container in containers:
        #
        MetaData_quality_type = container.getMetaDataEntry('quality_type')
        if MetaData_quality_type is not None :
            if MetaData_quality_type != 'not_supported' :
                # Logger.log("d", "New MetaData_quality_type : %s for %s", str(MetaData_quality_type), container.getId() )
                liste_quality.append(MetaData_quality_type)
    
    liste_quality = list(dict.fromkeys(liste_quality))
    new_quality='not_supported'
    
    try:
        new_quality=liste_quality[0]

    except:
        pass

    for ql in liste_quality:
        if ql == 'standard':
            new_quality='standard'
            break
        if ql == 'normal':
            new_quality='normal'
            break

    # Logger.log("d", "New_quality : %s", str(new_quality) )
    global_stack = Application.getInstance().getGlobalContainerStack()
    for container in global_stack.getContainers():
        #
        MetaData_quality_type = container.getMetaDataEntry('quality_type')
        if MetaData_quality_type is not None :
            if MetaData_quality_type == 'not_supported' :
                container.setMetaDataEntry('quality_type', new_quality)
                container.setDirty(True)
                MetaData_quality_type = container.getMetaDataEntry('quality_type')
                Logger.log("d", "New MetaData_quality_type : %s for %s", str(MetaData_quality_type), container.getId() )

    
def formatContainer(container, name='Container', short_value_properties=False, show_keys=True):
    html = ''
    html += '<a id="' + str(id(container)) + '" ></a>'
    #
    if safeCall(container.getName) == "empty" :
        html += tableHeader(name + ': ' + safeCall(container.getId))
    else :
        html += tableHeader(name + ': ' + safeCall(container.getName))
        
        
    html += formatContainerMetaDataRows(container)

    if show_keys:
        key_properties = ['value', 'resolve'] if short_value_properties else setting_prop_names
        key_properties.sort()

        # hasattr() method returns true if an object has the given named attribute and false if it does not
        if hasattr(container, 'getAllKeys'):
            keys = list(container.getAllKeys())
            for key in keys:
                html += formatSettingsKeyTableRow(key, formatSettingValue(container, key, key_properties))

    html += tableFooter()
    return html    

def formatContainerMetaDataRows(def_container):
    html = ''
    try:
        # Logger.log("d", "quality_type : " + safeCall(def_container.getMetaDataEntry('quality_type')))
        html += formatKeyValueTableRow('type', def_container.getMetaDataEntry('type'), extra_class='metadata') 
        # html += formatKeyValueTableRow('<type>', type(def_container), extra_class='metadata')
        # html += formatKeyValueTableRow('<id>', def_container, extra_class='metadata')
        html += formatKeyValueTableRow('id', safeCall(def_container.getId), extra_class='metadata')
        html += formatKeyValueTableRow('name', safeCall(def_container.getName), extra_class='metadata')
 
        MetaData_definition = def_container.getMetaDataEntry('definition')
        if MetaData_definition is not None:
            html += formatKeyValueTableRow('definition', MetaData_definition, extra_class='metadata')
        MetaData_quality_type = def_container.getMetaDataEntry('quality_type')
        if MetaData_quality_type is not None:
            html += formatKeyValueTableRow('quality_type', MetaData_quality_type, extra_class='metadata')  
            
        # hasattr() method returns true if an object has the given named attribute and false if it does not
        html += formatKeyValueTableRow('read only', safeCall(def_container.isReadOnly), extra_class='metadata')
        if hasattr(def_container, 'getPath'):
            html += formatKeyValueTableRowFile('path', safeCall(def_container.getPath), extra_class='metadata')
        if hasattr(def_container, 'getType'):
            html += formatStringTableRow('type', safeCall(def_container.getType), extra_class='metadata')

    except:
        pass

    return html
    
def formatExtruderStacks():
    html = ''
    html += '<h2 id="extruder_stacks">Extruder Stacks</h2>'
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in Application.getInstance().getExtruderManager().getActiveExtruderStacks():
        html += '<h3 id="extruder_index_' + str(position) + '">Index ' + str(position) + '</h3>'
        html += formatContainerStack(extruder_stack)
        position += 1
    return html

def formatExtruderBaseStacks():
    html = ''
    html += '<h2 id="extruder_stacks">Extruder Stacks</h2>'
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in Application.getInstance().getExtruderManager().getActiveExtruderStacks():
        html += '<h3 id="extruder_index_' + str(position) + '">Index ' + str(position) + '</h3>'
        html += formatContainerBaseStack(extruder_stack)
        position += 1
    return html
    
def formatExtruderStacksMenu():
    html = ''
    html += '<ul>'
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in Application.getInstance().getExtruderManager().getActiveExtruderStacks():
        html += '<li>'
        html += '<a href="#extruder_index_' + str(position) + '">Index ' + str(position) + '</a>\n'
        html += formatContainerStackMenu(extruder_stack)
        html += '</li>'
        position += 1
    html += '</ul>'
    return html

def formatExtruderBaseStacksMenu():
    html = ''
    html += '<ul>'
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in Application.getInstance().getExtruderManager().getActiveExtruderStacks():
        html += '<li>'
        html += '<a href="#extruder_index_' + str(position) + '">Index ' + str(position) + '</a>\n'
        html += formatContainerBaseStackMenu(extruder_stack)
        html += '</li>'
        position += 1
    html += '</ul>'
    return html
    
def formatContainerStack(Cstack, show_stack_keys=True):
    html = '<div class="container_stack">\n'
    html += formatContainer(Cstack, name='Container Stack', short_value_properties=True)
    html += '<div class="container_stack_containers">\n'
    html += '<h3>Containers</h3>\n'
    for container in Cstack.getContainers():
        html += formatContainer(container, show_keys=show_stack_keys)
    html += '</div>\n'
    html += '</div>\n'
    return html

def formatContainerBaseStack(Cstack, show_stack_keys=True):
    html = '<div class="container_stack_containers">\n'
    html += '<h3>Containers</h3>\n'
    for container in Cstack.getContainers():
        Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == "quality_changes" :
            html += formatContainer(container, show_keys=show_stack_keys)
    html += '</div>\n'
    return html
    
def formatContainerStackMenu(stack):
    html = ''
    html += '<a href="#' + str(id(stack)) + '"></a><br />\n'
    html += '<ul>\n'
    for container in stack.getContainers():
        #
        if container.getName() == "empty" :
            html += '<li><a href="#' + str(id(container)) + '">' + encode(container.getId()) + '</a></li>'
        else:
            html += '<li><a href="#' + str(id(container)) + '">' + encode(container.getName()) + '</a></li>'
            
    html += '</ul>\n'
    return html

def formatContainerBaseStackMenu(stack):
    html = ''
    html += '<a href="#' + str(id(stack)) + '"></a><br />\n'
    html += '<ul>\n'
    for container in stack.getContainers():
        if str(container.getMetaDataEntry("type")) == "quality_changes" :
            #
            if container.getName() == "empty" :
                html += '<li><a href="#' + str(id(container)) + '">' + encode(container.getId()) + '</a></li>'
            else:
                html += '<li><a href="#' + str(id(container)) + '">' + encode(container.getName()) + '</a></li>'
            
    html += '</ul>\n'
    return html
    
setting_prop_names = SettingDefinition.getPropertyNames()
def formatSettingValue(container, key, properties=None):
    if properties is None:
        properties = setting_prop_names

    #value = '<ul class=\'property_list\'>\n'
    value = ''
    comma = ''
    properties.sort()
    for prop_name in properties:
        prop_value = container.getProperty(key, prop_name)
        if prop_value is not None:
            if prop_name=='value' :
                # repr() function returns a printable representation of the given object
                print_value = repr(prop_value)
                if print_value.find('UM.Settings.SettingFunction') > 0 :
                    # Logger.log("d", "print_value : " + print_value)
                    strtok_value = print_value.split('=',1)
                    # Logger.log("d", "print_value : " + str(strtok_value[1]))
                    final_value = '=' + strtok_value[1].replace(' >','')
                else :
                    final_value = print_value
                    
                #value += '  <li>\n'
                # value += '    <span class="prop_name">' + encode(prop_name) + ':</span> ' + encode(final_value)
                value += encode(final_value)
                # value += '  </li>\n'
    #value += '</ul>\n'
    value += '\n'

    return RawHtml(value)
    
def safeCall(callable):
    try:
        result = callable()
        return result
    except Exception as ex:
        return ex

def tableHeader(title):
    return '''<table class='key_value_table'>
    <thead><tr><th colspan='2'>''' + encode(title) + '''</th></tr></thead>
    <tbody>
'''

def tableFooter():
    return '</tbody></table>\n'

def formatStringTableRow(key, value, extra_class=''):
    clazz = ''
    formatted_value = encode(str(value))
    formatted_key = encode(str(key))

    return '<tr class="' + extra_class + ' ' + clazz + '"><td class="key">' + formatted_key + '</td><td class="value">' + formatted_value + '</td></tr>\n'
    
def formatKeyValueTableRow(key, value, extra_class=''):
    clazz = ''
    if isinstance(value, Exception):
        clazz = 'exception'

    if isinstance(value, RawHtml):
        formatted_value = value.value
    elif isinstance(value, dict):
        formatted_value = encode(json.dumps(value, sort_keys=True, indent=4))
        clazz += ' preformat'
    elif isinstance(value, DefinitionContainer):
        formatted_value = encode(value.getId() + ' ' + str(value))
    else:
        formatted_value = encode(str(value))

    if isinstance(key, RawHtml):
        formatted_key = key.value
    else:
        formatted_key = encode(str(key))

    return '<tr class="' + extra_class + ' ' + clazz + '"><td class="key">' + formatted_key + '</td><td class="value">' + formatted_value + '</td></tr>\n'
    
def formatKeyValueTableRowFile(key, value, extra_class=''):
    clazz = ''
    if isinstance(value, Exception):
        clazz = 'exception'

    if isinstance(value, RawHtml):
        formatted_value = value.value
    elif isinstance(value, dict):
        formatted_value = encode(json.dumps(value, sort_keys=True, indent=4))
        clazz += ' preformat'
    elif isinstance(value, DefinitionContainer):
        formatted_value = encode(value.getId() + ' ' + str(value))
    else:
        formatted_value = encode(str(value))

    if isinstance(key, RawHtml):
        formatted_key = key.value
    else:
        formatted_key = encode(str(key))

    return '<tr class="' + extra_class + ' ' + clazz + '"><td class="CellWithComment">' + formatted_key + '</td><td class="value"><a href="' + formatted_value + '">' + formatted_value + '</a></td></tr>\n'

def formatSettingsKeyTableRow(key, value):

    Cstack = CuraApplication.getInstance().getGlobalContainerStack()
    
    clazz = ''
    # Test if type Exception
    if isinstance(value, Exception):
        clazz = 'exception'

    # Test if type RawHtml
    if isinstance(value, RawHtml):
        formatted_value = value.value
        Display_Key = '&#x1f511; '
    else:
        formatted_value = encode(str(value))
        Display_Key = '&#x1F527; '

    formatted_key = encode(str(key))
    
    Ckey=str(key)
    
    untranslated_label=str(Cstack.getProperty(Ckey, 'label'))
    definition_key=Ckey + ' label'
    translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)
    untranslated_description=str(Cstack.getProperty(Ckey, 'description'))
    description_key=Ckey + ' description'
    translated_description=i18n_catalog.i18nc(description_key, untranslated_description)
    
    # &#x1f511;  => Key symbole
    return '<tr class="' + clazz + '" --data-key="' + translated_label + '"><td class="CellWithComment">' + Display_Key + translated_label +  '<span class="CellComment">' + translated_description + '</span></td><td class="value">' + formatted_value + '</td></tr>\n'

 
def keyFilterJS():
    return '''
    function initKeyFilter() {
      var filter = document.getElementById("key_filter");
      filter.addEventListener("change", function() {
        var filterValue = filter.value;

        if (filterValue === '') {
          document.body.classList.add("show_metadata");
          document.body.classList.remove("hide_metadata");
        } else {
          document.body.classList.remove("show_metadata");
          document.body.classList.add("hide_metadata");
        }

        var filterRegexp = new RegExp(filterValue, "i");

        var allKeys = document.querySelectorAll("[--data-key]");
        var i;
        for (i=0; i<allKeys.length; i++) {
          var keyTr = allKeys[i];
          var key = keyTr.getAttribute("--data-key");
          if (filterRegexp.test(key)) {
            keyTr.classList.remove("key_hide");
          } else {
            keyTr.classList.add("key_hide");
          }
        }
      });
    }
    '''

def keyFilterWidget():
    html = '''
    <div class="key_filter">
    &#x1F50E; filter key: <input type="text" id="key_filter" />
    </div>
    '''
    return html
   

def has_browser():
    try:
        webbrowser.get()
        return True
    except webbrowser.Error:
        return False
        
def openHtmlPage(page_name, html_contents):
    target = os.path.join(tempfile.gettempdir(), page_name)
    with open(target, 'w', encoding='utf-8') as fhandle:
        fhandle.write(html_contents)
        
    if not has_browser() :
        Logger.log("d", "openHtmlPage default browser not defined") 
        Message(text = "Default browser not defined open \n %s" % (target), title = i18n_cura_catalog.i18nc("@info:title", "Warning ! ProfilAnalyser"), message_type = Message.MessageType.WARNING).show()
        
    QDesktopServices.openUrl(QUrl.fromLocalFile(target))

def getHtmlHeader(page_name='Cura Settings'):
    return '''<!DOCTYPE html><html>
<head>
<meta charset='UTF-8'>
<title>''' + encode(page_name) + '''</title>
<script>
''' + keyFilterJS() + '''
</script>
<style>
html {
  font-family: sans-serif;
  font-size: 11pt;
}

a, a:visited {
  color: #0000ff;
  text-decoration: none;
}

ul {
  padding-left: 1em;
}

div.menu {
  position: fixed;
  padding: 4px;
  left: 0px;
  width: 22em;
  top: 0px;
  height: 100%;
  box-sizing: border-box;
  overflow: auto;
  background-color: #ffffff;
  z-index: 100;
}

div.contents {
  padding-left: 22em;
}

table.key_value_table {
  border-collapse: separate;
  border: 1px solid #e0e0e0;
  margin-top: 16px;
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  border-spacing: 0px;
}

table.key_value_table_extruder > thead th {
  text-align: left;
  background-color: #428000;
  color: #ffffff;
}

table.key_value_table th, table.key_value_table td {
  padding: 4px;
}

table.key_value_table > thead th {
  text-align: left;
  background-color: #428bca;
  color: #ffffff;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

table.key_value_table > tbody > tr:nth-child(even) {
  background-color: #e0e0e0;
}

table.key_value_table_extruder > tbody > tr:nth-child(even) {
  background-color: #e0f0f0;
}

table.key_value_table > tbody > tr.exception {
  background-color: #e08080;
}

table.key_value_table td.key {
  font-weight: bold;
}

table.key_value_table tr.preformat td.value {
  white-space: pre;
}

table.key_value_table tr.preformat td.value_extruder {
  white-space: pre;
  background-color: #e0f0f0;
}

div.container_stack {
  padding: 8px;
  border: 2px solid black;
  border-radius: 8px;
}

div.container_stack > table.key_value_table > thead th {
  background-color: #18294D;
}

div.container_stack_containers {
  margin: 4px;
  padding: 4px;
  border: 1px dotted black;
  border-radius: 4px;
}

td.CellWithComment{
  white-space: pre;
  font-weight: bold;
  position:relative;
}

td.CellWithError{
  white-space: pre;
  font-weight: bold;
  position:relative;
  background-color: #c92b12;
}

.CellComment{
  display:none;
  position:absolute; 
  z-index:100;
  border:1px;
  background-color:white;
  border-style:solid;
  border-width:1px;
  border-color:blue;
  padding:3px;
  color:blue; 
  top:30px; 
  left:20px;
  font-weight: lighter;
}

td.CellWithComment:hover span.CellComment{
  display:block;
}

td.CellWithError:hover span.CellComment{
  display:block;
}

tr.key_hide {
  display: none;
}

body.hide_metadata tr.metadata {
  display: none;
}

ul.property_list {
  list-style: none;
  padding-left: 0;
  margin-left: 0;
}

span.prop_name {
  font-weight: bold;
}
tr.hidden, td.hidden, th.hidden {
  display: none;
}
</style>
</head>
<body onload="initKeyFilter();">
'''

htmlFooter = '''</body>
</html>
'''
class RawHtml:
    def __init__(self, value):
        self.value = value
    
