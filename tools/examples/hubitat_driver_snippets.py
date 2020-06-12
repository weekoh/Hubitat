#  Copyright 2019 Markus Liljergren
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from datetime import date
import base64
import binascii
import cv2
import math
import os

driverVersion = "v0.0.0MMDDb"

def getDriverVersion(driverVersionSpecial=None):
    if(driverVersionSpecial != None):
        driver_version_current = driverVersionSpecial
    else:
        driver_version_current = driverVersion
    if(driver_version_current.find("MMDD") != -1):
        driver_version_current = driver_version_current.replace("MMDD", date.today().strftime("%m%d"))
    return driver_version_current

from hubitat_codebuilder import HubitatCodeBuilderError

"""
  Snippets used by hubitat-driver-helper-tool
"""

def getHeaderLicense(driverVersionSpecial=None):
    driverVersionActual = getDriverVersion(driverVersionSpecial)
    return """/**
 *  Copyright 2020 Markus Liljergren
 *
 *  Version: """ + driverVersionActual + """
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at:
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 *  NOTE: This is an auto-generated file and most comments have been removed!
 *
 */"""

def getDefaultImports():
    return """/** Default Imports */
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
// Used for MD5 calculations
import java.security.MessageDigest
"""
#import java.math.MathContext NOT ALLOWED!!! WHY?
#import groovy.transform.TypeChecked
#import groovy.transform.TypeCheckingMode

def getChildComponentDefaultUpdatedContent():
    return """
// This is code needed to run in updated() in ALL Child drivers
getDriverVersion()
"""

def getDefaultParentImports():
    return getDefaultImports() + """/* Default Parent Imports */
"""

def getUpdateNeededSettingsTasmotaHeader():
    return """// updateNeededSettings() Generic header BEGINS here
Map currentProperties = state.currentProperties ?: [:]

state.settings = settings

//def configuration = new XmlSlurper().parseText(configuration_model_tasmota())
String isUpdateNeeded = "NO"

if(runReset != null && runReset == 'RESET') {
    for ( e in state.settings ) {
        logging("Deleting '${e.key}' with value = ${e.value} from Settings", 50)
        // Not sure which ones are needed, so doing all...
        device.clearSetting("${e.key}")
        device.removeSetting("${e.key}")
        state?.settings?.remove("${e.key}")
    }
}

tasmota_prepareDNI()

// updateNeededSettings() Generic header ENDS here
"""

def getUpdateNeededSettingsTasmotaModuleCommand(moduleNumber):
    return '''
// Tasmota Module selection command (autogenerated)
moduleNumber = '''+str(moduleNumber)+'''   // Defined earlier
tasmota_getAction(tasmota_getCommandString("Module", null))
tasmota_getAction(tasmota_getCommandString("Template", null))
if(disableModuleSelection == null) disableModuleSelection = false
if(disableModuleSelection == false) {
    logging("Setting the Module soon...", 10)
    logging(device.currentValue('module'), 10)
    if(device.currentValue('module') != null && !device.currentValue('module').startsWith("[${moduleNumber}:")) {
        logging("This DOESN'T start with [${moduleNumber} ${device.currentValue('module')}",10)
        tasmota_getAction(tasmota_getCommandString("Module", "${moduleNumber}"))
    } else {
        logging("This starts with [${moduleNumber} ${device.currentValue('module')}",10)
    }
} else {
    logging("Setting the Module has been disabled!", 10)
}
'''

def getUpdateNeededSettingsTasmotaDynamicModuleCommand(moduleNumber = -1, defaultDeviceTemplate = ''):
    return """
// Tasmota Module and Template selection command (autogenerated)
tasmota_getAction(tasmota_getCommandString("Module", null))
tasmota_getAction(tasmota_getCommandString("Template", null))
boolean disableModuleSelectionSetting = disableModuleSelection
if(disableModuleSelectionSetting == null) disableModuleSelectionSetting = false

Integer moduleNumberUsed = null
if(moduleNumber == null || moduleNumber == '-1') {
    moduleNumberUsed = """+str(moduleNumber)+"""
} else {
    moduleNumberUsed = moduleNumber.toInteger()
}
boolean useDefaultTemplate = false
String defaultDeviceTemplate = ''
if(deviceTemplateInput != null && deviceTemplateInput == "0") {
    useDefaultTemplate = true
    defaultDeviceTemplate = ''
}
if(deviceTemplateInput == null || deviceTemplateInput == "") {
    // We should use the default of the driver
    useDefaultTemplate = true
    defaultDeviceTemplate = '""" + defaultDeviceTemplate + """'
}
if(deviceTemplateInput != null) deviceTemplateInput = deviceTemplateInput.replaceAll(' ','')
logging("disableModuleSelectionSetting=$disableModuleSelectionSetting, deviceTemplateInput=$deviceTemplateInput, moduleNumberUsed=$moduleNumberUsed, moduleNumber=$moduleNumber", 1)
if(disableModuleSelectionSetting == false && ((deviceTemplateInput != null && deviceTemplateInput != "") || 
                                       (useDefaultTemplate && defaultDeviceTemplate != ""))) {
    def usedDeviceTemplate = defaultDeviceTemplate
    if(useDefaultTemplate == false && deviceTemplateInput != null && deviceTemplateInput != "") {
        usedDeviceTemplate = deviceTemplateInput
    }
    logging("Setting the Template (${usedDeviceTemplate}) soon...", 100)
    logging("templateData = ${device.currentValue('templateData')}", 10)
    if(usedDeviceTemplate != '') moduleNumberUsed = 0  // This activates the Template when set
    // Checking this makes installs fail: device.currentValue('templateData') != null 
    if(usedDeviceTemplate != null && device.currentValue('templateData') != usedDeviceTemplate) {
        logging("The template is currently NOT set to '${usedDeviceTemplate}', it is set to '${device.currentValue('templateData')}'", 100)
        // The NAME part of th Device Template can't exceed 14 characters! More than that and they will be truncated.
        // TODO: Parse and limit the size of NAME???
        tasmota_getAction(tasmota_getCommandString("Template", usedDeviceTemplate))
    } else if (device.currentValue('module') == null){
        // Update our stored value!
        tasmota_getAction(tasmota_getCommandString("Template", null))
    }else if (usedDeviceTemplate != null) {
        logging("The template is set to '${usedDeviceTemplate}' already!", 100)
    }
} else {
    logging("Can't set the Template...", 10)
    logging(device.currentValue('templateData'), 10)
    //logging("deviceTemplateInput: '${deviceTemplateInput}'", 10)
    //logging("disableModuleSelection: '${disableModuleSelectionSetting}'", 10)
}
if(disableModuleSelectionSetting == false && moduleNumberUsed != null && moduleNumberUsed >= 0) {
    logging("Setting the Module (${moduleNumberUsed}) soon...", 100)
    logging("device.currentValue('module'): '${device.currentValue('module')}'", 10)
    // Don't filter in this case: device.currentValue('module') != null 
    if(moduleNumberUsed != null && (device.currentValue('module') == null || !(device.currentValue('module').startsWith("[${moduleNumberUsed}:") || device.currentValue('module') == '0'))) {
        logging("Currently not using module ${moduleNumberUsed}, using ${device.currentValue('module')}", 100)
        tasmota_getAction(tasmota_getCommandString("Module", "${moduleNumberUsed}"))
    } else if (moduleNumberUsed != null && device.currentValue('module') != null){
        logging("This starts with [${moduleNumberUsed} ${device.currentValue('module')}",10)
    } else if (device.currentValue('module') == null){
        // Update our stored value!
        tasmota_getAction(tasmota_getCommandString("Module", null))
    } else {
        logging("Module is set to '${device.currentValue('module')}', and it's set to be null, report this to the creator of this driver!",10)
    }
} else {
    logging("Setting the Module has been disabled!", 10)
}
"""

def getUpdateNeededSettingsTelePeriod(forcedTelePeriod=None):
    if (forcedTelePeriod==None):
        return """
// updateNeededSettings() TelePeriod setting
tasmota_getAction(tasmota_getCommandString("TelePeriod", (telePeriod == '' || telePeriod == null ? "300" : telePeriod)))
"""
    else:
        return '''
// updateNeededSettings() TelePeriod setting
tasmota_getAction(tasmota_getCommandString("TelePeriod", "''' + str(forcedTelePeriod) + '''"))
'''

def getUpdateNeededSettingsTHMonitor():
    return """
// updateNeededSettings() Temperature/Humidity/Pressure setting
tasmota_getAction(tasmota_getCommandString("TempRes", (tempRes == '' || tempRes == null ? "1" : tempRes)))
"""

def getUpdateNeededSettingsTasmotaFooter():
    return """
tasmota_getAction(tasmota_getCommandString("TelePeriod", "${tasmota_getTelePeriodValue()}"))
// updateNeededSettings() Generic footer BEGINS here
tasmota_getAction(tasmota_getCommandString("SetOption113", "1")) // Hubitat Enabled
// Disabling Emulation so that we don't flood the logs with upnp traffic
tasmota_getAction(tasmota_getCommandString("Emulation", "2")) // Hue Emulation Enabled, REQUIRED for device discovery
tasmota_getAction(tasmota_getCommandString("HubitatHost", device.hub.getDataValue("localIP")))
logging("HubitatPort: ${device.hub.getDataValue("localSrvPortTCP")}", 1)
tasmota_getAction(tasmota_getCommandString("HubitatPort", device.hub.getDataValue("localSrvPortTCP")))
tasmota_getAction(tasmota_getCommandString("FriendlyName1", device.displayName.take(32))) // Set to a maximum of 32 characters
// We need the Backlog inter-command delay to be 20ms instead of 200...
tasmota_getAction(tasmota_getCommandString("SetOption34", "20"))

// Set the timezone
int tzoffset = getLocation().timeZone.getOffset(now()) / 3600000
String tzoffsetWithSign = tzoffset < 0 ? "${tzoffset}" : "+${tzoffset}"
logging("Setting timezone to $tzoffsetWithSign", 10)
tasmota_getAction(tasmota_getCommandString("Timezone", tzoffsetWithSign))

// Just make sure we update the child devices
logging("Scheduling tasmota_refreshChildren...", 1)
runIn(30, "tasmota_refreshChildren")
runIn(60, "tasmota_refreshChildrenAgain")
logging("Done scheduling tasmota_refreshChildren...", 1)

if(override == true) {
    tasmota_sync(ipAddress)
}

//logging("Cmds: " +cmds,1)
sendEvent(name:"needUpdate", value: isUpdateNeeded, displayed:false, isStateChange: false)
// updateNeededSettings() Generic footer ENDS here
"""

#configuration.Value.each
#{     
#    if ("${it.@setting_type}" == "lan" && it.@disabled != "true"){
#        if (currentProperties."${it.@index}" == null)
#        {
#            if (it.@setonly == "true"){
#                logging("Setting ${it.@index} will be updated to ${it.@value}", 2)
#                cmds << tasmota_getAction("/configSet?name=${it.@index}&value=${it.@value}")
#            } else {
#                isUpdateNeeded = "YES"
#                logging("Current value of setting ${it.@index} is unknown", 2)
#                cmds << tasmota_getAction("/configGet?name=${it.@index}")
#            }
#        }
#        else if ((settings."${it.@index}" != null || it.@hidden == "true") && currentProperties."${it.@index}" != (settings."${it.@index}" != null? settings."${it.@index}".toString() : "${it.@value}"))
#        { 
#            isUpdateNeeded = "YES"
#            logging("Setting ${it.@index} will be updated to ${settings."${it.@index}"}", 2)
#            cmds << tasmota_getAction("/configSet?name=${it.@index}&value=${settings."${it.@index}"}")
#        } 
#    }
#}

def getGenericOnOffFunctions():
    return """
/* Generic On/Off functions used when only 1 switch/button exists */
def on() {
	logging("on()", 50)
    def cmds = []
    cmds << tasmota_getAction(tasmota_getCommandString("Power", "On"))
    return cmds
}

def off() {
    logging("off()", 50)
	def cmds = []
    cmds << tasmota_getAction(tasmota_getCommandString("Power", "Off"))
    return cmds
}
"""

def getRGBWOnOffFunctions():
    return """
/* RGBW On/Off functions used when only 1 switch/button exists */
def on() {
	logging("on()", 50)
    def cmds = []
    def h = null
    def s = null
    def b = 100
    if(state != null) {
        //h = state.containsKey("hue") ? state.hue : null
        //s = state.containsKey("saturation") ? state.saturation : null
        b = state.containsKey("level") ? state.level : 100
    }
    if(b < 20) b = 20
    if(state.colorMode == "CT") {
        state.level = b
        cmds << tasmota_rgbw_setColorTemperature(colorTemperature ? colorTemperature : 3000)
        cmds << tasmota_rgbw_setLevel(state.level, 0)
    } else {
        cmds << tasmota_rgbw_setHSB(h, s, b)
    }
    cmds << tasmota_getAction(tasmota_getCommandString("Power", "On"))
    return cmds
}

def off() {
    logging("off()", 50)
	def cmds = []
    cmds << tasmota_getAction(tasmota_getCommandString("Power", "Off"))
    return cmds
}
"""

def getDefaultFunctions(comment="", driverVersionSpecial=None):
    driverVersionActual = getDriverVersion(driverVersionSpecial)
    return '''/* Default Driver Methods go here */
private String getDriverVersion() {
    comment = "''' + comment + '''"
    if(comment != "") state.comment = comment
    String version = "''' + driverVersionActual + '''"
    logging("getDriverVersion() = ${version}", 100)
    sendEvent(name: "driver", value: version)
    updateDataValue('driver', version)
    return version
}
'''

def getDefaultAppMethods(driverVersionSpecial=None):
    driverVersionActual = getDriverVersion(driverVersionSpecial)
    return '''/* Default App Methods go here */
private String getAppVersion() {
    String version = "''' + driverVersionActual + '''"
    logging("getAppVersion() = ${version}", 50)
    return version
}
'''

def getLoggingFunction(specialDebugLevel=True, minimized=True):
    extraDebug = ""
    if(specialDebugLevel):
        extraDebug = """
        case 100: // Only special debug messages, eg IR and RF codes
            if (level == 100 ) {
                log.info "$message"
                didLogging = true
            }
        break"""

    additionalLevels = ""
    if(minimized == False):
        additionalLevels = """
        case -1: // Insanely verbose
            if (level >= 0 && level < 100) {
                log.debug "$message"
                didLogging = true
            } else if (level == 100) {
                log.info "$message"
                didLogging = true
            }
        break
        case 10: // A little less
            if (level >= 10 && level < 99) {
                log.debug "$message"
                didLogging = true
            } else if (level == 100) {
                log.info "$message"
                didLogging = true
            }
        break
        case 50: // Rather chatty
            if (level >= 50 ) {
                log.debug "$message"
                didLogging = true
            }
        break
        case 99: // Only parsing reports
            if (level >= 99 ) {
                log.debug "$message"
                didLogging = true
            }
        break"""


    return """/* Logging function included in all drivers */
private boolean logging(message, level) {
    boolean didLogging = false
    //Integer logLevelLocal = (logLevel != null ? logLevel.toInteger() : 0)
    //if(!isDeveloperHub()) {
    Integer logLevelLocal = 0
    if (infoLogging == null || infoLogging == true) {
        logLevelLocal = 100
    }
    if (debugLogging == true) {
        logLevelLocal = 1
    }
    //}
    if (logLevelLocal != 0){
        switch (logLevelLocal) {
        case 1: // Very verbose
            if (level >= 1 && level < 99) {
                log.debug "$message"
                didLogging = true
            } else if (level == 100) {
                log.info "$message"
                didLogging = true
            }
        break""" + extraDebug + additionalLevels + """
        }
    }
    return didLogging
}
"""

def getSpecialDebugEntry(label=None):
    if(label==None):
        return '<Item label="descriptionText" value="100" />'
    else:
        return '<Item label="' + label + '" value="100" />'

def getCreateChildDevicesCommand(childType='component'):
    #childType == 'not_component' should 
    start = "try {\n"
    end = """
        } catch (com.hubitat.app.exception.UnknownDeviceTypeException e) {
            log.error "'${getChildDriverName()}' driver can't be found! Did you forget to install the child driver?"
        }"""
    if(childType=='component'):
        #return('addChildDevice("${getDeviceInfoByName("namespace")}", "${getChildDriverName()}", "$device.id-$i", [name: "$device.name #$i", label: "$device.displayName $i", isComponent: true])')
        
        return(start + 'addChildDevice("${getDeviceInfoByName("namespace")}", "${getChildDriverName()}", "$device.id-$i", [name: "${getFilteredDeviceDriverName()} #$i", label: "${getFilteredDeviceDisplayName()} $i", isComponent: true])' + end)
    elif(childType=='not_component'):
        return(start + 'addChildDevice("${getDeviceInfoByName("namespace")}", "${getChildDriverName()}", "$device.id-$i", [name: "${getFilteredDeviceDriverName()} #$i", label: "${getFilteredDeviceDisplayName()} $i", isComponent: false])' + end)
    else:
        raise HubitatCodeBuilderError('Unknown childType specified in getcreateChildDevicesCommand(childType={})'.format(str(childType)))

def getGetChildDriverNameMethod(childDriverName='default'):
    if(childDriverName == 'default'):
        return """String getChildDriverName() {
    String deviceDriverName = getDeviceInfoByName('name')
    if(deviceDriverName.toLowerCase().endsWith(' (parent)')) {
        deviceDriverName = deviceDriverName.substring(0, deviceDriverName.length()-9)
    }
    String childDriverName = "${deviceDriverName} (Child)"
    logging("childDriverName = '$childDriverName'", 1)
    return(childDriverName)
}"""
    else:
        return """String getChildDriverName() {
    String childDriverName = '""" + childDriverName + """ (Child)'
    logging("childDriverName = '$childDriverName'", 1)
    return(childDriverName)
}"""

def getCalculateB0():
    return """String calculateB0(String inputStr, repeats) {
    // This calculates the B0 value from the B1 for use with the Sonoff RF Bridge
    logging('inputStr: ' + inputStr, 0)
    inputStr = inputStr.replace(' ', '')
    //logging('inputStr.substring(4,6): ' + inputStr.substring(4,6), 0)
    Integer numBuckets = Integer.parseInt(inputStr.substring(4,6), 16)
    List buckets = []

    logging('numBuckets: ' + numBuckets.toString(), 0)

    String outAux = String.format(' %02X ', numBuckets.toInteger())
    outAux = outAux + String.format(' %02X ', repeats.toInteger())
    
    logging('outAux1: ' + outAux, 0)
    
    Integer j = 0
    for(i in (0..numBuckets-1)){
        outAux = outAux + inputStr.substring(6+i*4,10+i*4) + " "
        j = i
    }
    logging('outAux2: ' + outAux, 0)
    outAux = outAux + inputStr.substring(10+j*4, inputStr.length()-2)
    logging('outAux3: ' + outAux, 0)

    String dataStr = outAux.replace(' ', '')
    outAux = outAux + ' 55'
    Integer length = (dataStr.length() / 2).toInteger()
    outAux = "AA B0 " + String.format(' %02X ', length.toInteger()) + outAux
    logging('outAux4: ' + outAux, 0)
    logging('outAux: ' + outAux.replace(' ', ''), 10)

    return(outAux)
}"""

def getGenerateLearningPreferences(types='["Default", "Toggle", "Push", "On", "Off"]', default_type='Default'):
    return '''// Methods for displaying the correct Learning Preferences and returning the 
// current Action Name
def generateLearningPreferences() {
    input(name: "learningMode", type: "bool", title: styling_addTitleDiv("Learning Mode"), description: '<i>Activate this to enter Learning Mode. DO NOT ACTIVATE THIS once you have learned the codes of a device, they will have to be re-learned!</i>', displayDuringSetup: false, required: false)
    if(learningMode) {
        input(name: "actionCurrentName", type: "enum", title: styling_addTitleDiv("Action To Learn"), 
              description: styling_addDescriptionDiv("Select which Action to save to in Learn Mode."), 
              options: ''' + types + ''', defaultValue: "''' + default_type + '''", 
              displayDuringSetup: false, required: false)
        input(name: "learningModeAdvanced", type: "bool", title: styling_addTitleDiv("Advanced Learning Mode"), 
              description: '<i>Activate this to enable setting Advanced settings. Normally this is NOT needed, be careful!</i>', 
              defaultValue: false, displayDuringSetup: false, required: false)
        if(learningModeAdvanced) {
            input(name: "actionCodeSetManual", type: "string", title: styling_addTitleDiv("Set Action Code Manually"), 
              description: '<i>WARNING! For ADVANCED users only!</i>', 
              displayDuringSetup: false, required: false)
            input(name: "actionResetAll", type: "bool", title: styling_addTitleDiv("RESET all Saved Actions"), 
              description: '<i>WARNING! This will DELETE all saved/learned Actions!</i>', 
              defaultValue: false, displayDuringSetup: false, required: false)
        }
    }
}

String getCurrentActionName() {
    String actionName
    if(!binding.hasVariable('actionCurrentName') || 
      (binding.hasVariable('actionCurrentName') && actionCurrentName == null)) {
        logging("Doesn't have the action name defined... Using ''' + default_type + '''!", 1)
        actionName = "''' + default_type + '''"
    } else {
        actionName = actionCurrentName
    }
    return(actionName)
}'''

def getChildComponentMetaConfigCommands():
    return """
// metaConfig is what contains all fields to hide and other configuration
// processed in the "metadata" context of the driver.
def metaConfig = clearThingsToHide()
metaConfig = setDatasToHide(['metaConfig', 'isComponent', 'preferences', 'label', 'name'], metaConfig=metaConfig)
"""

def splitImage(image_path, max_parts):
    (image_rootname, image_extension) = os.path.splitext(image_path)
    #print(image_path)
    #print(max_parts)
    img = cv2.imread(image_path)
    img_shape = img.shape
    img_width = int(img_shape[1])
    img_height = int(img_shape[0])

    img_piece_height = math.ceil(img_height / max_parts)
    #print(img_shape)
    #print('width:' + str(img_width))
    #print('height:' + str(img_height))
    #print(img_piece_height)
    #print(image_rootname)
    #print(image_extension)
    img_height_used = 0
    for i in range(1, max_parts + 1):
        if(img_height_used + img_piece_height > img_height):
            img_piece_height = img_height - img_height_used
        #cropped_img = img[0:img_height, 0:img_width].copy()
        cropped_img = img[img_height_used:img_height_used+img_piece_height, 0:img_width]
        #print(img_height_used)
        #print(img_piece_height)
        if(image_extension == ".jpg"):
            cv2.imwrite(image_rootname + "_" + str(i) + image_extension, cropped_img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        else:
            cv2.imwrite(image_rootname + "_" + str(i) + image_extension, cropped_img, [int(cv2.IMWRITE_PNG_COMPRESSION), 5])
        img_height_used += img_piece_height
    #print(img_height_used)

def getImageAsBase64(image_path, variable_name, current_part, max_parts):
    # Maximum App file size is 473 822 bytes
    # Split the image and get current_part
    splitImage(image_path, max_parts)

    (image_rootname, image_extension) = os.path.splitext(image_path)
    image_basename = os.path.basename(image_path)
    image_path_for_part = image_rootname + "_" + str(current_part) + image_extension
    mimetype = "image/png"
    if(image_extension == ".jpg"):
        mimetype = "image/jpg"
    with open(image_path_for_part, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())

    img = cv2.imread(image_path_for_part)
    img_shape = img.shape
    img_width = int(img_shape[1])
    img_height = int(img_shape[0])
    
    decoded_string = encoded_string.decode('utf-8')
    l = len(decoded_string)
    pieces = round(l / 65400)
    print("Length: " + str(l) + ", pieces: " + str(pieces))
    r = "Integer " + variable_name + "Pieces = " + str(pieces) + "\n"
    r += "Integer part = " + str(current_part) + "\n"
    r += "Integer partsTotal = " + str(max_parts) + "\n"
    r += "Integer imgWidth = " + str(img_width) + "\n"
    r += "Integer imgHeight = " + str(img_height) + "\n"
    r += "Integer imgOffset = " + str((current_part - 1) * img_height) + "\n"
    r += "String filename = \"" + image_basename + "\"\n"
    r += "String mimetype = \"" + mimetype + "\"\n"
    r += "List<String> " + variable_name + " = []\n"
    #if(pieces > 7):
    #     pieces = 7
    for i in range(0, pieces + 1):
        decoded_string_part, decoded_string = decoded_string[:65400], decoded_string[65400:]
        r += variable_name + "["+str(i)+"] = '''" + decoded_string_part + "'''\n"
    #r += variable_name + "["+str(7)+"] = '''" + decoded_string[:4174] + "'''\n"
    return r

def getImageAsBinaryString(image_path, variable_name):
    with open(image_path, "rb") as image_file:
        encoded_string = image_file.read()
    print(encoded_string.decode('latin-1').replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\'))
    return "String " + variable_name + " = '''" + encoded_string.decode('latin-1').replace('\\', '\\\\').replace('\n', '\\n') + "'''"

def getHtmlAsString(html_path, variable_name):
    # Maximum App file size is 473 822 bytes
    # Split the image and get current_part
    with open(html_path, "r") as html_file:
        html_string = html_file.read()

    html_string = html_string.replace("'''", "\\'\\'\\'")

    l = len(html_string)
    pieces = round(l / 65400)
    print("Length: " + str(l) + ", pieces: " + str(pieces))
    r = "Integer " + variable_name + "Pieces = " + str(pieces) + "\n"
    r += "List<String> " + variable_name + " = []\n"
    #if(pieces > 7):
    #     pieces = 7
    for i in range(0, pieces + 1):
        html_string_part, html_string = html_string[:65400], html_string[65400:]
        r += variable_name + "["+str(i)+"] = '''" + html_string_part + "'''\n"
    #r += variable_name + "["+str(7)+"] = '''" + decoded_string[:4174] + "'''\n"
    return r

def getTextAsString(text_path, variable_name):
    return getHtmlAsString(text_path, variable_name)