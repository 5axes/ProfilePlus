#--------------------------------------------------------------------------------------------
# Initial Copyright(c) FieldofView for the SettingsVisibilityHandler 
# Copyright (c) 2022 5axes
#--------------------------------------------------------------------------------------------
# All modification 5@xes
# First release  01-07-2022  First proof of concept
#------------------------------------------------------------------------------------------------------------------
# 1.0.0 01-07-2022  First release to test the concept
# 1.0.1 20-08-2022  Test Release of Cura
# 1.0.2 07-09-2022  Add Function to remove settings already existing in the material profile
# 1.0.3 08-09-2022  Test and reduce Code Size
# 1.0.5 08-09-2022  Add function to link with material Profile
# 1.0.6 00-03-2023  Add French translation
# 1.0.7 04-03-2023  Add Function "Test Settings to remove"
#------------------------------------------------------------------------------------------------------------------
#
# Contanier Type in Cura Stacked Profile System
#  type : user
#  type : quality_changes
#  type : intent
#  type : quality
#  type : material
#  type : variant
#  type : definition_changes
#  type : machine
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

from UM.Extension import Extension

from UM.PluginRegistry import PluginRegistry
from UM.Qt.Duration import DurationFormat

from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Version import Version


from cura.CuraVersion import CuraVersion  # type: ignore
from cura.CuraApplication import CuraApplication

from cura.Settings.ExtruderManager import ExtruderManager

from UM.Logger import Logger
from UM.Message import Message

from . import ProfilePlusSettingsVisibilityHandler
from . import ProfilePlusSettingDefinitionsModel

from UM.i18n import i18nCatalog
from UM.Resources import Resources

i18n_cura_catalog = i18nCatalog('cura')
i18n_catalog = i18nCatalog('fdmprinter.def.json')
i18n_extrud_catalog = i18nCatalog('fdmextruder.def.json')

encode = html.escape

Resources.addSearchPath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)))
)  # Plugin translation file import

catalog = i18nCatalog("profilplus")

if catalog.hasTranslationLoaded():
    Logger.log("i", "Profil Plus Plugin translation loaded!")
    
class ProfilePlus(QObject, Extension):
    #Create an api
    api = CuraApplication.getInstance().getCuraAPI()

    plugin_version = ""
    definition_string = ""

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

        self.Major=1
        self.Minor=0

        # Logger.log('d', "Info Version CuraVersion --> " + str(Version(CuraVersion)))
        Logger.log('d', "Info CuraVersion --> " + str(CuraVersion))
        
        # Test version for Cura Master
        # https://github.com/smartavionics/Cura
        if "master" in CuraVersion :
            self.Major=4
            self.Minor=20
        else :
            try:
                self.Major = int(CuraVersion.split(".")[0])
                self.Minor = int(CuraVersion.split(".")[1])
            except:
                pass
                
        ## Menu
        self.addMenuItem(catalog.i18nc("@menu", "Material Settings"), self.showTestMachineProfile)
        self.addMenuItem("", lambda: None)
        ## self.addMenuItem(catalog.i18nc("@menu", "Remove Settings present in the material profile"), self.cleanProfile)
        ## self.addMenuItem(catalog.i18nc("@menu", "Remove Settings present in the Machine Materials profiles"), self.cleanMachineProfile)         
        self.addMenuItem(catalog.i18nc("@menu", "Remove Settings"), self.showSettingsDialog)
        ## self.addMenuItem(" ", lambda: None)
        ## self.addMenuItem(catalog.i18nc("@menu", "Link Settings present in the material profile"), self.linkProfile)
        self.addMenuItem(" ", lambda: None)
        self.addMenuItem(catalog.i18nc("@menu", "View Custom Parameters"), viewProfile)
        self.addMenuItem(catalog.i18nc("@menu", "View Active Material"), viewMaterial)
        self.addMenuItem(catalog.i18nc("@menu", "View Machine Materials"), viewDefaultMaterial)
        self.addMenuItem(catalog.i18nc("@menu", "View Active Profile"), viewAll)
        self.addMenuItem("  ", lambda: None)
        self.addMenuItem(catalog.i18nc("@menu", "Help"), gotoHelp)

        self._application.getPreferences().addPreference("profile_plus/profile_settings",";")

        self._application.engineCreatedSignal.connect(self._onEngineCreated)



    def _onEngineCreated(self):
        qmlRegisterType(
            ProfilePlusSettingsVisibilityHandler.ProfilePlusSettingsVisibilityHandler,
            "Cura", 1, 0, "ProfilePlusSettingsVisibilityHandler"
        )

    def showSettingsDialog(self):
        self.definition_string=updateDefinition()
        Logger.log("d", "showSettingsDialog Profile definition_string : %s", self.definition_string )  
        self._application.getPreferences().setValue("profile_plus/profile_settings", self.definition_string)
        
        path = None
        if USE_QT5:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt5", "SettingsDialog.qml")
        else:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt6","SettingsDialog.qml")

        self._settings_dialog = self._application.createQmlComponent(path, {"manager": self})
        self._settings_dialog.show()

    _paramSettingChanged = pyqtSignal()
    
    def setParamSetting(self, value)->None:
        self._paramSettingChanged.emit()

    @pyqtProperty(str, notify=_paramSettingChanged, fset=setParamSetting)
    def paramSetting(self)->str:
        # Check for param to change
        value = self.testMachineProfile()

        return value
        
    @pyqtProperty(str, notify= userAction)
    def upDate(self)-> None:
        modi = ''
        self.definition_string=self._application.getPreferences().getValue("profile_plus/profile_settings")
        Logger.log("d", "Update definition_string : %s", self.definition_string )
        modi += upDateExtruderStacks(self.definition_string)
        modi += upDateContainerStack(self._application.getGlobalContainerStack(),self.definition_string)
        # 
        # Logger.log("d", "Update definition_string : %s", self.definition_string ) 
        if self.Major == 4 and self.Minor < 11 : 
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to do !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Modification ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()        
        else :
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to do !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.ERROR).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Modification ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.POSITIVE).show()        
    
    # Remove Settings present in the material profile : Remove from the active profile parameters already existing in the Material definition
    @pyqtProperty(str, notify= userAction)
    def cleanProfile(self)-> None:
        modi = ''
        mat_string=updateDefinition("material")
        Logger.log("d", "Material Parameters : %s", mat_string )
        profile_string=updateDefinition("quality_changes")
        Logger.log("d", "Profile Parameters : %s", profile_string )
        material_plus_settings = mat_string.split(";")
        profile_plus_settings = profile_string.split(";")
        
        for remove_key in material_plus_settings:
            # Logger.log("d", "Remove_key : %s", remove_key )
            if remove_key in profile_plus_settings:
                Logger.log("d", "Remove_key in list : %s", remove_key )
                profile_plus_settings.remove(remove_key)
            if "default_" in remove_key:
                remove_key=remove_key[8:]
                Logger.log("d", "Remove_key without default_ in list : %s", remove_key )
                if remove_key in profile_plus_settings:
                    profile_plus_settings.remove(remove_key)           
            
        update_string = ''
        for add_key in profile_plus_settings:
            update_string += add_key
            update_string += ";"      
        Logger.log("d", "Profile Parameters : %s", update_string )

        modi += upDateExtruderStacks(update_string)
        modi += upDateContainerStack(self._application.getGlobalContainerStack(),update_string)
        # 
        # Logger.log("d", "Update definition_string : %s", self.definition_string ) 
        if self.Major == 4 and self.Minor < 11 : 
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to do !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Modification ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()        
        else :
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to do !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.ERROR).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Modification ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.POSITIVE).show()        
        self._paramSettingChanged.emit()

    # Remove Settings present in the Machine Materials profiles : Remove from the active profile parameters already existing in every material associated with this machine
    @pyqtProperty(str, notify= userAction)
    def cleanMachineProfile(self)-> None:
        modi = ''
        mat_string=updateDefaultDefinition("material")
        Logger.log("d", "Material Parameters : %s", mat_string )
        profile_string=updateDefinition("quality_changes")
        Logger.log("d", "Profile Parameters : %s", profile_string )
        material_plus_settings = mat_string.split(";")
        profile_plus_settings = profile_string.split(";")
        
        for remove_key in material_plus_settings:
            # Logger.log("d", "Remove_key : %s", remove_key )
            if remove_key in profile_plus_settings:
                Logger.log("d", "Remove_key in list : %s", remove_key )
                profile_plus_settings.remove(remove_key)
            if "default_" in remove_key:
                remove_key=remove_key[8:]
                Logger.log("d", "Remove_key without default_ in list : %s", remove_key )
                if remove_key in profile_plus_settings:
                    profile_plus_settings.remove(remove_key)           
            
        update_string = ''
        for add_key in profile_plus_settings:
            update_string += add_key
            update_string += ";"      
        
        Logger.log("d", "Profile Parameters : %s", update_string )

        modi += upDateExtruderStacks(update_string)
        modi += upDateContainerStack(self._application.getGlobalContainerStack(),update_string)
        # 
        # Logger.log("d", "Update definition_string : %s", self.definition_string ) 
        if self.Major == 4 and self.Minor < 11 : 
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to do !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Modification ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()        
        else :
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to do !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.ERROR).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Modification ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.POSITIVE).show()        
        
        self._paramSettingChanged.emit() 
        
    # Link Settings present in the material profile : Replace the Settings present in the profile and the material definition by a extruderValueFromContainer instruction
    @pyqtProperty(str, notify= userAction)
    def linkProfile(self)-> None:
        modi = ''
        mat_string=updateDefinition("material")
        Logger.log("d", "Material Parameters link : %s", mat_string )
        profile_string=updateDefinition("quality_changes",True)
        Logger.log("d", "Profile Parameters link : %s", profile_string )
        material_plus_settings = mat_string.split(";")
        profile_plus_settings = profile_string.split(";")
        
        for remove_key in material_plus_settings:
            # Logger.log("d", "Remove_key : %s", remove_key )
            if remove_key in profile_plus_settings and len(remove_key) > 1 :
                Logger.log("d", "Remove_key in list : %s", remove_key )
                profile_plus_settings.remove(remove_key)
            if "default_" in remove_key:
                remove_key=remove_key[8:]
                Logger.log("d", "Remove_key without default_ in list : %s", remove_key )                
                if remove_key in profile_plus_settings:
                    profile_plus_settings.remove(remove_key)           
          
        update_string = ''
        for add_key in profile_plus_settings:
            update_string += add_key
            update_string += ";"      
        # Logger.log("d", "Update string : %s", update_string )
        modi += linkExtruderStacks(update_string)
        modi += linkContainerStack(self._application.getGlobalContainerStack(),update_string)
        # Logger.log("d", "Update for : %s", modi ) 
        
        if self.Major == 4 and self.Minor < 11 : 
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to link !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Link ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version)).show()        
        else :
            if modi == "" :
                Message(text = catalog.i18nc("@info:text", "! Error Nothing to link !"), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.ERROR).show()
            else :
                Message(text = catalog.i18nc("@info:text", "! Link ok for : %s") % (modi), title = catalog.i18nc("@info:title", "Profile Plus :") + str(self.plugin_version), message_type = Message.MessageType.POSITIVE).show()        
        
        self._paramSettingChanged.emit()
        
    def showTestMachineProfile(self):
        
        path = None
        if USE_QT5:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt5", "SettingsPopup.qml")
        else:
            path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qml", "qt6", "SettingsPopup.qml")

        self._popup_dialog = self._application.createQmlComponent(path, {"manager": self})
        self._popup_dialog.show()
        
    # List the parameter to modify    
    def testMachineProfile(self) -> str :
        modi = ''
        link_list=[]
        # For every stack_type="material" associated with the  machine_id
        # Get the list of parameters 
        mat_string=updateDefaultDefinition("material")
        Logger.log("d", "Test Profile Material Parameters : %s", mat_string )
        # For every the container quality_changes
        # Get the list of parameters  present in this container 
        profile_string=updateDefinition("quality_changes")
        link_string=updateLinkDefinition("quality_changes")
        # Logger.log("d", "Link_string : %s", link_string )
        # Logger.log("d", "Test Profile Profile Parameters : %s", profile_string )
        material_plus_settings = mat_string.split(";")
        profile_plus_settings = profile_string.split(";")
        modi_list=[]
        
        for remove_key in material_plus_settings:
            # Logger.log("d", "Remove_key : %s", remove_key )
            if remove_key in profile_plus_settings:
                Logger.log("d", "Remove_key in list : %s", remove_key )
                modi_list.append(remove_key)
            if "default_" in remove_key:
                remove_key=remove_key[8:]
                Logger.log("d", "Remove_key without default_ in list : %s", remove_key )
                if remove_key in profile_plus_settings:
                    modi_list.append(remove_key)           
            
        update_string = ''
        
        for add_key in modi_list:
            update_string += add_key
            update_string += "\n"
                  
        if len(link_string) :
            update_string += "\n"
            update_string = catalog.i18nc("@info:text", "Parameters with Linked definition :\n\n")
            link_list=link_string.split(";")
            
            for add_key in link_list:
                update_string += add_key
                update_string += "\n"        
            
        Logger.log("d", "Profile Parameters : %s", update_string )
        
        #if Remove :
        #    modi += upDateExtruderStacks(update_string)
        #    modi += upDateContainerStack(self._application.getGlobalContainerStack(),update_string)
        # else :
        modi = update_string
        # 
        # Logger.log("d", "Update definition_string : %s", self.definition_string ) 
        if modi == "" or modi == "\n" :
            update_string = catalog.i18nc("@info:text", "! Error Nothing to do ! \n Your Profile is already clean")
        
        return update_string
        
def upDateExtruderStacks(definition_string):
    modi = ''
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks():
        modi += upDateContainerStack(extruder_stack, definition_string)
        position += 1
    return modi

def upDateContainerStack(Cstack, definition_string):
    modi = ''
    if len(definition_string) < 2 :
        Logger.log("d", "upDateContainerStack nothing to do : %s", definition_string )
        return modi
        
    Logger.log("d", "upDateContainerStack : %s", definition_string )
    settingsList = definition_string.split(";")
    
    for container in Cstack.getContainers():
        # Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == "quality_changes" :
            keys = list(container.getAllKeys())
            for key in keys:
                # visi += formatSettingsKeyTableRow(key, formatSettingValue(container, key, key_properties))
                # Logger.log("d", "key :|%s|", key )
                # Naive Method :)
                delRef = True
                for iList in settingsList:
                    if (iList == key) :
                        delRef = False
                        Logger.log("d", "iList :|%s|", iList )
                        
                if delRef == True :
                    Logger.log("d", "delRef :|%s|", key )
                    # The point of no return, will remove the parameter
                    # https://community.ultimaker.com/topic/40968-container-removeinstance-goal-of-the-option-postpone_emit/
                    container.removeInstance(key, postpone_emit=True)
                    modi += key
                    modi += "\n"
    return modi

def linkExtruderStacks(definition_string):
    modi = ''
    # machine = Application.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks():
        modi += linkContainerStack(extruder_stack, definition_string)
        position += 1
    return modi

def linkContainerStack(Cstack, definition_string):
    modi = ''
    if len(definition_string) < 2 :
        Logger.log("d", "upDateContainerStack nothing to do : %s", definition_string )
        return modi
        
    Logger.log("d", "upDateContainerStack : %s", definition_string )
    settingsList = definition_string.split(";")
    
    for container in Cstack.getContainers():
        # Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == "quality_changes" :
            keys = list(container.getAllKeys())
            for key in keys:

                base_value = str(container.getProperty(key, "value"))
                Logger.log("d", "link key : %s", str(key) )
                Logger.log("d", "link base_value : %s", str(base_value) )
                # Naive Method :)
                delRef = True
                for iList in settingsList:
                    if (iList == key) :
                        delRef = False
                        Logger.log("d", "iList :|%s|", iList )
                        
                if delRef == True :
                    if not "extruderValueFromContainer" in base_value:
                        Logger.log("d", "linkRef :|%s|", key )
                        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
                        if not global_container_stack:
                            return modi                       
                        try:
                            material_container_index = global_container_stack.getContainers().index(global_container_stack.material)
                        except ValueError:
                            return modi 

                        settable_per_extruder = global_container_stack.getProperty(key, "settable_per_extruder")
                        resolve_value = global_container_stack.getProperty(key, "resolve")
                        Logger.log("d", "link settable_per_extruder : %s", str(settable_per_extruder) )
                        Logger.log("d", "link resolve_value : %s", str(resolve_value) )
                
                        Logger.log("d", "material_container_index %s",str(material_container_index))
                        
                        # The point of no return, will fix the parameter with the extruderValueFromContainer function
                        #if not settable_per_extruder and resolve_value is None:
                        #    # todo: notify user
                        #    Logger.log("e", "Setting %s can not be set per material", key)
                        #    return modi

                        if settable_per_extruder:
                            value_string = "=extruderValueFromContainer(extruder_nr,\"%s\",%d)" %(key, material_container_index)
                            Logger.log("d", "settable_per_extruder value_string :|%s|", value_string )
                            container.setProperty(key, "value", value_string)
                            modi += key
                            modi += "\n"                            
                        else:
                            active_extruder_index = ExtruderManager.getInstance().activeExtruderIndex
                            value_string = "=extruderValueFromContainer(%d,\"%s\",%d)" %(active_extruder_index, key, material_container_index)
                            Logger.log("d", "value_string :|%s|", value_string )
                            container.setProperty(key, "value", value_string)
                            modi += key
                            modi += "\n"
    return modi

def gotoHelp():
    QDesktopServices.openUrl(QUrl("https://github.com/5axes/ProfilePlus/wiki"))
    
def viewAll():
    HtmlFile = str(CuraVersion).replace('.','-') + '_cura_profile.html'
    openHtmlPage(HtmlFile, htmlPage(True,"Profile"))

def viewProfile():
    HtmlFile = str(CuraVersion).replace('.','-') + '_cura_quality.html'
    openHtmlPage(HtmlFile, htmlPage(False,"quality_changes"))   

def viewMaterial():
    HtmlFile = str(CuraVersion).replace('.','-') + '_cura_material.html'
    openHtmlPage(HtmlFile, htmlPage(False,"material"))   

def viewDefaultMaterial():
    HtmlFile = str(CuraVersion).replace('.','-') + '_cura_materials.html'
    openHtmlPage(HtmlFile, containersOfTypeHtmlPage(False,catalog.i18nc("@html", "Materials"),"material"))  

# For every the container quality_changes
# Get the list of parameters  present in this container   
def updateDefinition(stack_keys="quality_changes", checkCode=0):
    # Logger.log("d", "In updateDefinition")
    def_str = ""
    def_str += formatExtruderDefinitionStacks(stack_keys,checkCode)
    def_str += formatContainerDefinitionStack(CuraApplication.getInstance().getGlobalContainerStack(),stack_keys,checkCode)
    return def_str

# For every the container quality_changes
# Get the list of parameters  present in this container   
def updateLinkDefinition(stack_keys="quality_changes", checkCode=2):
    # Logger.log("d", "In updateLinkDefinition")
    def_str = ""
    def_str += formatExtruderDefinitionStacks(stack_keys,2)
    def_str += formatContainerDefinitionStack(CuraApplication.getInstance().getGlobalContainerStack(),stack_keys,2)
    return def_str

# For every stack_type="material" associated with the  machine_id
# Get the list of parameters 
def updateDefaultDefinition(stack_type="material"):
    def_str = ""
    
    machine_id = getMachineId()

    # if machine_id == '' or machine_id == 'None':
    #    machine_quality_changes = machine_manager.activeMachine.qualityChanges
    #    machine_id=str(machine_quality_changes.getMetaDataEntry('definition'))
    Logger.log("d", "Machine_id : %s", machine_id )
    
    containers = ContainerRegistry.getInstance().findInstanceContainers(definition = machine_id,type=stack_type)
    
    for container in containers:
        keys = list(container.getAllKeys())
        for key in keys:
            if not key in def_str:
                def_str += key
                def_str += ";"
            
    # Logger.log("d", "updateDefaultDefinition : %s", def_str )
    return def_str
    
def formatExtruderDefinitionStacks(stack_keys="quality_changes", checkCode=0):
    def_str = ''
    # machine = CuraApplication.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks():
        def_str += formatContainerDefinitionStack(extruder_stack,stack_keys, checkCode)
        position += 1
    return def_str

# checkCode check if Value defined with extruderValueFromContainer
def formatContainerDefinitionStack(Cstack, stack_keys="quality_changes", checkCode=0):
    def_str = ''
    for container in Cstack.getContainers():
        # Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == stack_keys :
            keys = list(container.getAllKeys())
            for key in keys:
                if checkCode >= 1 :
                    settable_per_extruder = container.getProperty(key, "settable_per_extruder")
                    resolve_value = container.getProperty(key, "resolve")
                    base_value = str(container.getProperty(key, "value"))
                    # if checkCode >= 2 :
                    #    Logger.log("d", "key : %s", str(key) )
                    #    Logger.log("d", "settable_per_extruder : %s", str(settable_per_extruder) )
                    #    Logger.log("d", "resolve_value : %s", str(resolve_value) )
                    #    Logger.log("d", "base_value : %s", str(base_value) )
                    if not "extruderValueFromContainer" in base_value and checkCode < 2 :                  
                        def_str += key
                        def_str += ";"
                    else :
                        if "extruderValueFromContainer" in base_value and checkCode >= 2 :
                            def_str += key
                            def_str += ";"
                        else :                    
                            Logger.log("d", "Value type extruderValueFromContainer : %s", str(base_value) )
                else:
                    def_str += key
                    def_str += ";"
                    
    return def_str



def htmlPage(show_all=False,stack_type="quality_changes"):
    html = getHtmlHeader(stack_type)

    # Menu creation
    html += '<div class="menu">\n'
    html += '<ul>'

    html += '<li><a href="#extruder_stacks">Extruder Stacks</a>\n'
    html += formatExtruderStacksMenu(show_all,stack_type)
    html += '</li>\n'

    html += '<li><a href="#global_stack">Global Stack</a>'
    html += formatContainerStackMenu(CuraApplication.getInstance().getGlobalContainerStack(),show_all, stack_type)
    html += '</li>\n'

    html += '</ul>\n'
    
    # Java script filter function
    # if show_all :
    html += keyFilterWidget(catalog.i18nc("@html", "Filter key"))
    html += '</div>'

    # Contents creation
    html += '<div class="contents">'
    html += formatExtruderStacks(show_all,stack_type)
     
    html += '<h2 id="global_stack">Global Stack</h2>'
    html += formatContainerStack(CuraApplication.getInstance().getGlobalContainerStack(),True,show_all,stack_type)
    
    html += '</div>'

    html += htmlFooter
    return html


def getMachineId():
    machine_manager = CuraApplication.getInstance().getMachineManager()
    g_stack = machine_manager.activeMachine
    machine_id=str(g_stack.quality.getMetaDataEntry('definition'))

    if machine_id == '' or machine_id == 'None':
        machine_quality_changes = machine_manager.activeMachine.qualityChanges
        machine_id=str(machine_quality_changes.getMetaDataEntry('definition'))
    
    Logger.log("d", "Machine_id : %s", machine_id )
    
    return machine_id

def containersOfTypeHtmlPage(show_all = False, name="Materials", stack_type="material"):
    
    machine_id = getMachineId()

    html = getHtmlHeader(machine_id)

    html += "<div class='menu'>\n"
    html += "<ul>"
           
    if show_all :
        containers = ContainerRegistry.getInstance().findInstanceContainers(type=stack_type)
    else :
        containers = ContainerRegistry.getInstance().findInstanceContainers(definition = machine_id,type=stack_type)
        
    containers.sort(key=lambda x: x.getId())
    
    for container in containers:
        # Logger.log("d", "Container : {}".format(container) )
        # Logger.log("d", "Name : {}".format(container.getName()) )
        
        html += "<li><a href='#"+ str(id(container)) + "'>"+encode(container.getName())+"</a></li>\n"
    html += "</ul>"

    html += keyFilterWidget(catalog.i18nc("@html", "Filter key"))
    html += "</div>"

    html += "<div class='contents'>"
    html += formatAllContainersOfType(show_all, machine_id , name, stack_type)
    html += "</div>"


    html += htmlFooter
    return html

def formatAllContainersOfType(show_all, machine_id , name, type_):
    html = "<h2>" + name + "</h2>\n"

    if show_all :
        containers = ContainerRegistry.getInstance().findInstanceContainers(type=type_)
    else :
        containers = ContainerRegistry.getInstance().findInstanceContainers(definition = machine_id,type=type_)

    containers.sort(key=lambda x: x.getId())
    for container in containers:
        html += formatContainer(container)
    
    return html

    
# Change the 'quality_type' to 'standard' if 'not_supported'
# Useless Code but who knows .. one day
def changeToStandardQuality():
    #stack = CuraApplication.getInstance().getGlobalContainerStack()

    machine_id = getMachineId()
    
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
    global_stack = CuraApplication.getInstance().getGlobalContainerStack()
    for container in global_stack.getContainers():
        #
        MetaData_quality_type = container.getMetaDataEntry('quality_type')
        if MetaData_quality_type is not None :
            if MetaData_quality_type == 'not_supported' :
                container.setMetaDataEntry('quality_type', new_quality)
                container.setDirty(True)
                MetaData_quality_type = container.getMetaDataEntry('quality_type')
                Logger.log("d", "New MetaData_quality_type : %s for %s", str(MetaData_quality_type), container.getId() )
    
def formatContainer(container, name=catalog.i18nc("@html:subtitle", "Container"), short_value_properties=False, show_keys=True):
    html = ''
    html += '<a id="' + str(id(container)) + '" ></a>'
    #
    if safeCall(container.getName) == "empty" :
        html += tableHeader(name + ' : ' + safeCall(container.getId))
    else :
        html += tableHeader(name + ' : ' + safeCall(container.getName))
    
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
        # Logger.log("d", "GetType : {} ".format(safeCall(def_container.getType)))
        Logger.log("d", "Def_container : {} ".format(def_container))
        html += formatKeyValueTableRow(catalog.i18nc("@html:row", "type"), def_container.getMetaDataEntry('type'), extra_class='metadata') 
        # html += formatKeyValueTableRow('<type>', type(def_container), extra_class='metadata')
        # html += formatKeyValueTableRow('<id>', def_container, extra_class='metadata')
        html += formatKeyValueTableRow(catalog.i18nc("@html:row", "id"), safeCall(def_container.getId), extra_class='metadata')
        html += formatKeyValueTableRow(catalog.i18nc("@html:row", "name"), safeCall(def_container.getName), extra_class='metadata')
 
        MetaData_definition = def_container.getMetaDataEntry('definition')
        if MetaData_definition is not None:
            html += formatKeyValueTableRow(catalog.i18nc("@html:row", "definition"), MetaData_definition, extra_class='metadata')
        # if safeCall(def_container.getType) == "material" :
        s = "{}".format(def_container)
        html += formatStringTableRow(catalog.i18nc("@html:row", "detail"), s , extra_class='metadata')   

        MetaData_quality_type = def_container.getMetaDataEntry('quality_type')
        if MetaData_quality_type is not None:
            html += formatKeyValueTableRow(catalog.i18nc("@html:row", "quality_type"), MetaData_quality_type, extra_class='metadata')  
            
        # hasattr() method returns true if an object has the given named attribute and false if it does not
        html += formatKeyValueTableRow('read only', safeCall(def_container.isReadOnly), extra_class='metadata')
        if hasattr(def_container, 'getPath'):
            html += formatKeyValueTableRowFile(catalog.i18nc("@html:row", "path"), safeCall(def_container.getPath), extra_class='metadata')
        if hasattr(def_container, 'getType'):
            html += formatStringTableRow(catalog.i18nc("@html:row", "type"), safeCall(def_container.getType), extra_class='metadata')

    except:
        pass

    return html
    
def formatExtruderStacks(show_all=False,stack_keys="quality_changes"):
    html = ''
    html += '<h2 id="extruder_stacks">' + catalog.i18nc("@html:title", "Extruder Stacks") + '</h2>'
    # machine = CuraApplication.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks():
        html += '<h3 id="extruder_index_' + str(position) + '">' + catalog.i18nc("@html:subtitle", "Index") + ' ' + str(position) + '</h3>'
        html += formatContainerStack(extruder_stack,True,show_all,stack_keys)
        position += 1
    return html

def formatExtruderStacksMenu(show_all=True,stack_keys="quality_changes"):
    html = ''
    html += '<ul>'
    # machine = CuraApplication.getInstance().getMachineManager().activeMachine
    # for position, extruder_stack in sorted([(int(p), es) for p, es in machine.extruders.items()]):
    position=0
    for extruder_stack in CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks():
        html += '<li>'
        html += '<a href="#extruder_index_' + str(position) + '">' + catalog.i18nc("@html:subtitle", "Index") + ' ' + str(position) + '</a>\n'
        html += formatContainerStackMenu(extruder_stack, show_all, stack_keys)
        html += '</li>'
        position += 1
    html += '</ul>'
    return html
    
def formatContainerStack(Cstack, show_stack_keys=True, show_all=True, stack_keys="quality_changes" ):
    html = '<div class="container_stack">\n'
    if show_all :
        html += formatContainer(Cstack, name='Container Stack', short_value_properties=True)
        html += '<div class="container_stack_containers">\n'
    html += '<h3>' + catalog.i18nc("@html:subtitle", "Containers") + '</h3>\n'
    for container in Cstack.getContainers():
        Logger.log("d", "type : %s", str(container.getMetaDataEntry("type")) )
        if str(container.getMetaDataEntry("type")) == stack_keys or show_all :
            html += formatContainer(container, show_keys=show_stack_keys)
    if show_all :
        html += '</div>\n'
    html += '</div>\n'
    return html
    

def formatContainerStackMenu(stack, show_all=True, stack_keys="quality_changes"):
    html = ''
    html += '<a href="#' + str(id(stack)) + '"></a><br />\n'
    html += '<ul>\n'
    for container in stack.getContainers():
        if str(container.getMetaDataEntry("type")) == stack_keys or show_all:
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

# Row with a link on a File    
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

def keyFilterWidget(txt_balise):
    html = '''
    <div class="key_filter">
    &#x1F50E; {balise}: <input type="text" id="key_filter" />
    </div>
    '''
    html = html.format(balise=txt_balise)
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
        if self.Major == 4 and self.Minor < 11 :
            Message(text = catalog.i18nc("@info:text", "Default browser not defined open \n %s") % (target), title = i18n_cura_catalog.i18nc("@info:title", "Warning ! Profile Plus")).show()
        else :
            Message(text = catalog.i18nc("@info:text", "Default browser not defined open \n %s") % (target), title = i18n_cura_catalog.i18nc("@info:title", "Warning ! Profile Plus"), message_type = Message.MessageType.WARNING).show()
       
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
    
