import toml 
import csv
from zipfile import ZipFile as zf
import os

EXTRACTED_TOML_FOLDER = 'extractedTomls/'
DISABLED_MODS = 'inactiveMods/'

print("Please enter the full path to Minecraft's mod folder.")
MOD_PATH = '/home/mason/.local/share/multimc/instances/TheRealm/.minecraft/mods/'


COMMANDS = {
    'QUIT': {'q','quit','exit'},
    'REGENCACHE': {'rc'},
    'STATUS': {'s'}
}

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
    for mod in temp['dependencies'][mod_filename_cache[modFilename]['modId']]:
        if (mod['modId'] not in ('minecraft', 'forge') and mod['mandatory']):
            mod_filename_cache[modFilename]['dependencies'].append(mod['modId'])
            mod_id_cache[tempId]['dependencies'].append(mod['modId'])

def printSingleSummary(mod_info):
    print(mod_info['filename'])
    print('  modId: '+mod_info['modId'])
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
    else:
        print("Unrecognized command.")
# Done
# Cache all modIds and filenames
#    - command to regenerate cache of modIds and filenames

# TODO 
#  Save as csv file, for easy loading later
#    - command to save a file, and to load a file
#  Keep track of mods that are confirmed working
#    - command to reset list of mods that are confirmed working

#  Command to arbritrarily remove half of the mods from the mod folder
#    Keep track of dependancies, make sure they're met

#  Command to arbritrarily add half of the mods back to the mod folder
#    Keep track of dependancies, make sure they're met

#  Command to add all mods back into mod folder

#  Command to mark all mods in mod folder as confirmed working

# Command to print path
# and to change path

#  Command to swap the halves of mods moved