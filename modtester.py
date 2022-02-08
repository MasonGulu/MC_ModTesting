import toml
from zipfile import ZipFile as zf
import os
import random

EXTRACTED_TOML_FOLDER = 'extractedTomls/'
DISABLED_MODS = 'inactiveMods/'

print("Please enter the full path to Minecraft's mod folder.")
print("The path MUST end with a / or \\, depending on the OS")
print('An example path is /home/mason/.local/share/multimc/instances/TheRealm/.minecraft/mods/')
MOD_PATH = input()

# Example mod_filename_cache
# mod_filename_cache = {
#   'filename.jar': {
#       'modId': 'coolmod',
#       'dependencies': {'forge', 'minecraft'},
#       'filename': 'filename.jar',
#       'confirmedWorking': False
#     }
# }

mod_filename_cache = {

}

mod_id_cache = {

}

def cacheMod(modFilename):
    with zf(MOD_PATH+modFilename) as z:
        z.extract('META-INF/mods.toml', EXTRACTED_TOML_FOLDER+modFilename)
    temp = toml.load(EXTRACTED_TOML_FOLDER+modFilename+'/META-INF/mods.toml')
    tempId = temp['mods'][0]['modId']
    mod_filename_cache[modFilename] = {'modId': tempId, 'dependencies': [], 'filename': modFilename, 'confirmedWorking': False}
    mod_id_cache[tempId] = {'modId': tempId, 'dependencies': [], 'filename': modFilename, 'confirmedWorking': False}
    try:
        for mod in temp['dependencies'][mod_filename_cache[modFilename]['modId']]:
            if (mod['modId'] not in ('minecraft', 'forge') and mod['mandatory']):
                mod_filename_cache[modFilename]['dependencies'].append(mod['modId'])
                mod_id_cache[tempId]['dependencies'].append(mod['modId'])
    except KeyError:
        pass 

def printSingleSummary(mod_info):
    print(mod_info['filename'])
    print('  modId: '+mod_info['modId'])
    if (mod_info['confirmedWorking']):
        print('  marked WORKING')
    if (len(mod_info['dependencies']) > 0):
        print('  depends on:')
        for y in mod_info['dependencies']:
            print('  - '+y)
        
def printStatus(temp):
    try:
        printSingleSummary(mod_filename_cache[temp])
    except KeyError:
        try:
            printSingleSummary(mod_id_cache[temp])
        except KeyError:
            for x in mod_filename_cache:
                printSingleSummary(mod_filename_cache[x])

mods_added = []

def addModByID(id):
    for x in os.listdir(DISABLED_MODS):
        if (mod_filename_cache[x]['modId'] == id):
            os.replace(DISABLED_MODS+x, MOD_PATH+x)
            return True 
    return False

def verifyDependancies():
    print('Verifying dependancies..')
    activemods = []
    for x in os.listdir(MOD_PATH):
        activemods.append(mod_filename_cache[x]['modId'])
    for x in activemods:
        for y in mod_id_cache[x]['dependencies']:
            if y not in activemods:
                print(x+' requires '+y+'. Checking if mod is just disabled..')
                if not addModByID(y):
                    print('!!! Mod '+y+' not found. Aborting.')
                    return 
                else:
                    activemods.append(y)
    print('All dependancies found. Game should launch.')

def markAllAsSafe():
    for x in os.listdir(MOD_PATH):
        mod_filename_cache[x]['confirmedWorking'] = True
        mod_id_cache[mod_filename_cache[x]['modId']]['confirmedWorking'] = True 

def swap():
    global mods_added
    if len(mods_added) == 0:
        print("There are no mods to swap.")
        return
    temp = []
    for x in os.listdir(DISABLED_MODS):
        os.replace(DISABLED_MODS+x, MOD_PATH+x)
        temp.append(x)
    for x in mods_added:
        os.replace(MOD_PATH+x, DISABLED_MODS+x)
    mods_added = temp
    verifyDependancies()

def removeAllMods():
    global mods_added
    mods_added = []
    for x in os.listdir(MOD_PATH):
        if (not mod_filename_cache[x]['confirmedWorking']):
            os.replace(MOD_PATH+x, DISABLED_MODS+x)
    verifyDependancies()

def addAllMods():
    global mods_added
    mods_added = []
    for x in os.listdir(DISABLED_MODS):
        os.replace(DISABLED_MODS+x, MOD_PATH+x)
        mods_added.append(x)
    verifyDependancies()

def addHalf():
    global mods_added 
    dir = os.listdir(DISABLED_MODS)
    mods_added = random.sample(dir, round(len(dir)/2))
    for x in mods_added:
        os.replace(DISABLED_MODS+x, MOD_PATH+x)
    verifyDependancies()

COMMANDS = {
    'QUIT': ['q','quit','exit'],
    'REGENCACHE': ['rc'],
    'STATUS': ['s'],
    'SWAP': ['swap'],
    'REMOVEALL': ['removeall'],
    'ADDALL': ['addall'],
    'SAFE': ['safe', 'works'],
    'KEEPMOD': ['keep'],
    'RESETWORKING': ['resetworking'],
    'ADDHALF': ['addhalf'],
    'HELP': ['help', 'h'],
    'MANUALDEPENDENCY': ['mdep'],
    'REMOVEDEPENDENCY': ['rdep']
}

def help():
    print('Quit - quits the program')
    print(COMMANDS['QUIT'])
    print('')
    print('Regen cache - gathers dependancy and modId information from all mods in the mods folder.')
    print(COMMANDS['REGENCACHE'])
    print('')
    print('Status - prints information about mods')
    print(COMMANDS['STATUS'])
    print('')
    print('Remove all - removes all mods from the mods folder, excluding mods marked as working')
    print(COMMANDS['REMOVEALL'])
    print('')
    print('Swap - swap the half of mods added last, with the half that was left behind.')
    print(COMMANDS['SWAP'])
    print('')
    print('Add all - adds all mods from the inactive folder to the mods folder')
    print(COMMANDS['ADDALL'])
    print('')
    print('Safe - marks all current mods as working/safe, forces them to stay in the mods folder')
    print(COMMANDS['SAFE'])
    print('')
    print('Keep mod - marks a specific mod as working/safe, forces it to stay in the mods folder')
    print(COMMANDS['KEEPMOD'])
    print('')
    print('Reset working - resets the safe/working status of ALL mods')
    print(COMMANDS['RESETWORKING'])
    print('')
    print('Add half - adds a random half of the mods from the inactive folder to the active folder, swap can swap the half taken')
    print(COMMANDS['ADDHALF'])
    print('')
    print('Help')
    print(COMMANDS['HELP'])
    print('')
    print('Manual Dependency - add a dependency manually')
    print(COMMANDS['MANUALDEPENDENCY'])
    print('')
    print('Remove dependency - remove a dependency manually')
    print(COMMANDS['REMOVEDEPENDENCY'])

while True:
    print('> ', end='')
    command = input()

    if command in COMMANDS['QUIT']:
        break
    elif command in COMMANDS['REGENCACHE']:
        for f in os.listdir(MOD_PATH):
            print(f)
            cacheMod(f)
    elif command in COMMANDS['STATUS']:
        print("Enter a modId, filename, or push enter for a generic listing.")
        temp = input()
        printStatus(temp)
    elif command in COMMANDS['SWAP']:
        swap()
    elif command in COMMANDS['REMOVEALL']:
        removeAllMods()
    elif command in COMMANDS['ADDALL']:
        addAllMods()
    elif command in COMMANDS['SAFE']:
        markAllAsSafe()
    elif command in COMMANDS['KEEPMOD']:
        print("Enter the modId or filename of the mod you want to keep active.")
        temp = input()
        try:
            mod_filename_cache[temp]['confirmedWorking'] = True 
            mod_id_cache[mod_filename_cache[temp]['modId']]['confirmedWorking'] = True 
        except KeyError:
            try:
                mod_id_cache[temp]['confirmedWorking'] = True 
                mod_filename_cache[mod_id_cache[temp]['filename']]['confirmedWorking'] = True 
            except KeyError:
                print("Invalid modId or filename.")
    elif command in COMMANDS['RESETWORKING']:
        for x in mod_filename_cache:
            mod_filename_cache[x]['confirmedWorking'] = False
        for x in mod_id_cache:
            mod_filename_cache[x]['confirmedWorking'] = False 
    elif command in COMMANDS['ADDHALF']:
        addHalf()
    elif command in COMMANDS['HELP']:
        help()
    elif command in COMMANDS['MANUALDEPENDENCY']:
        print("Enter the modId of the mod that requires a dependancy.")
        temp = input()
        print("Enter the modId of the dependancy")
        tempId = input()
        try:
            mod_id_cache[temp]['dependencies'].append(tempId)
            mod_filename_cache[mod_id_cache[temp]['filename']]['dependencies'].append(tempId)
        except KeyError:
            print("Invalid filename.")
    elif command in COMMANDS['REMOVEDEPENDENCY']:
        print("Enter the modId of the mod you'd like to remove a dependency from.")
        temp = input()
        try:
            if len(mod_id_cache[temp]['dependencies']) == 0:
                print('This mod does not have any dependencies')
                break
            print("Enter the index of the dependency you'd like to remove.")
            i = 0
            for x in mod_id_cache[temp]['dependencies']:
                print(str(i) + ' ' + x)
                i += 1
            index = int(input())
            mod_id_cache[temp]['dependencies'].pop(index)
            mod_filename_cache[mod_id_cache[temp]['filename']]['dependencies'].pop(index)
        except KeyError:
            print("Invalid modId.")
        except ValueError:
            print("Invalid number.")
    else:
        print("Unrecognized command.")
# Done
# Cache all modIds and filenames
#    - command to regenerate cache of modIds and filenames

#  Command to swap the halves of mods moved (untested)

#  Command to add all mods back into mod folder

#  Command to remove all mods from mod folder

#  Command to mark all mods in mod folder as confirmed working

#  Keep track of mods that are confirmed working
#    - command to reset list of mods that are confirmed working

# TODO 
#  Save as csv file, for easy loading later
#    - command to save a file, and to load a file

#  Command to arbritrarily add half of the mods back to the mod folder
#    Keep track of dependancies, make sure they're met

# Command to print path
# and to change path


# Might not implement
#  Command to arbritrarily remove half of the mods from the mod folder
#    Keep track of dependancies, make sure they're met