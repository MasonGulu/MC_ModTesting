import toml
from zipfile import ZipFile as zf
import os
import random
import PySimpleGUI as sg
import csv

EXTRACTED_TOML_FOLDER = 'extractedTomls/'
DISABLED_MODS = 'inactiveMods/'
VERSION = '0.20'

sg.theme('SystemDefault')

try:
    os.mkdir(EXTRACTED_TOML_FOLDER)
except FileExistsError:
    pass

try:
    os.mkdir(DISABLED_MODS)
except FileExistsError:
    pass 

MOD_PATH = sg.PopupGetFolder('Select your mods folder.', default_path='') + '/'

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

def cacheMod(path,modFilename):
    with zf(path+modFilename) as z:
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
        try:
            activemods.append(mod_filename_cache[x]['modId'])
        except KeyError:
            print('WARNING: Cache is out of date!')
    for x in activemods:
        for y in mod_id_cache[x]['dependencies']:
            if y not in activemods:
                print(x+' requires '+y+'. Attempting to reenable..')
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

def cacheAll():
    mods = os.listdir(MOD_PATH)
    dmods = os.listdir(DISABLED_MODS)
    layout = [[sg.Text('',key='modname', size=(20,1))],
                [sg.ProgressBar(len(mods)+len(dmods), orientation='h', size=(20,20),key='bar')]]
    win = sg.Window('Caching Mods...', layout=layout, finalize=True)
    i = 0
    for x in mods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)
        cacheMod(MOD_PATH,x)
    for x in dmods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)
        cacheMod(DISABLED_MODS,x)
    win.close()


def updateFilelists():
    win['DISABLED_filelist'].update(values=os.listdir(DISABLED_MODS))
    win['ENABLED_filelist'].update(values=os.listdir(MOD_PATH))
    win.finalize()

DEFAULT_WIDTH = 30

columns = [[],[],[],[]]
columns[0] = [[sg.Text('Disabled Mods')],[sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,size=(DEFAULT_WIDTH,20),key='DISABLED_filelist',enable_events=True)]]

columns[1] = [[sg.Text('Filename:')],[sg.Text('',size=(DEFAULT_WIDTH,1),key='DISABLED_filename')],
                [sg.Text('ModId:')], [sg.Text('',size=(DEFAULT_WIDTH,1),key='DISABLED_modId')],
                [sg.Checkbox('Keep',default=False,key='DISABLED_keep', enable_events=True)],
                [sg.Button(button_text='>>> Enable >>>',key='DISABLED_button_to_enable')],
                [sg.Text('Dependencies:')],
                [sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,size=(DEFAULT_WIDTH,5),key='DISABLED_dependencies')],
                [sg.Input(size=(DEFAULT_WIDTH,1),key='DISABLED_input_for_new_dependency')],
                [sg.Button(button_text='Add New', key='DISABLED_button_to_add_dependency'), sg.Button(button_text='Remove', key='DISABLED_button_to_remove_dependency')]]

columns[2] = [[sg.Text('Enabled Mods')],[sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,size=(DEFAULT_WIDTH,20),key='ENABLED_filelist',enable_events=True)]]

columns[3] = [[sg.Text('Filename:')],[sg.Text('',size=(DEFAULT_WIDTH,1),key='ENABLED_filename')],
                [sg.Text('ModId:')], [sg.Text('',size=(DEFAULT_WIDTH,1),key='ENABLED_modId')],
                [sg.Checkbox('Keep',default=False,key='ENABLED_keep', enable_events=True)],
                [sg.Button(button_text='<<< Disable <<<',key='ENABLED_button_to_disable')],
                [sg.Text('Dependencies:')],
                [sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,size=(DEFAULT_WIDTH,5),key='ENABLED_dependencies')],
                [sg.Input(size=(DEFAULT_WIDTH,1),key='ENABLED_input_for_new_dependency')],
                [sg.Button(button_text='Add New', key='ENABLED_button_to_add_dependency'), sg.Button(button_text='Remove', key='ENABLED_button_to_remove_dependency')]]

menu_bar = [['Important!', ['Refresh Cache', 'Reset Keep Flags']],
            ['File', ['Save...', 'Load...']],
            ['Move All Unknown', ['To Enabled','To Disabled']],
            ['Operations', ['Add New Half', 'Swap Halves', 'Mark Active Keep']],
            ['Help', ['How To Use', 'About']]]
layout = [[sg.MenuBar(menu_bar)], [sg.Column(columns[0]),sg.Column(columns[1]),sg.VerticalSeparator(),sg.Column(columns[2]),sg.Column(columns[3])]]


win = sg.Window('MC Mod Tester', layout=layout)

win.finalize()
updateFilelists()
cacheAll()

while True:
    event, values = win.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    # Every event should refresh the file listings

    if event == 'Refresh Cache':
        cacheAll()
        updateFilelists()
    
    elif event == 'Reset Keep Flags':
        for x in mod_filename_cache:
            mod_filename_cache[x]['confirmedWorking'] = False
        for x in mod_id_cache:
            mod_id_cache[x]['confirmedWorking'] = False

    elif event == 'Save...':
        filename = sg.PopupGetFile('Choose a file to save your state.', save_as=True)
        if filename != None:
            with open(filename, 'w') as csvfile:
                w = csv.writer(csvfile)
                temp = []
                for x in mod_id_cache:
                    temp.append(x)
                    temp.append(mod_id_cache[x]['confirmedWorking'])
                w.writerow(temp)
                temp = []
                for x in mods_added:
                    temp.append(x)
                w.writerow(temp)

    elif event == 'Load...':
        filename = sg.PopupGetFile('Choose a file to load a state.')
        if filename != None:
            try:
                with open(filename, 'r') as csvfile:
                    r = csv.reader(csvfile)
                    temp = []
                    for row in r:
                        temp.append(row)
                    for x in range(0, len(temp[0]), 2):
                        mod_id_cache[temp[0][x]]['confirmedWorking'] = (temp[0][x+1] == 'True')
                        mod_filename_cache[mod_id_cache[temp[0][x]]['filename']]['confirmedWorking'] = (temp[0][x+1] == 'True')
                    mods_added = []
                    for x in temp[1]:
                        mods_added.append(x)
            except:
                print("!! An issue occured loading!")

    elif event == 'To Enabled':
        addAllMods()
        updateFilelists()
    
    elif event == 'To Disabled':
        removeAllMods()
        updateFilelists()
    
    elif event == 'Add New Half':
        addHalf()
        updateFilelists()

    elif event == 'Swap Halves':
        swap()
        updateFilelists()

    elif event == 'Mark Active Keep':
        markAllAsSafe()

    elif event == 'How To Use':
        sg.PopupNoButtons("""
        * First, when you launch the script a window will pop up, asking for your mod directory. Make sure to give the full path to where your mod folder (of the modpack you're testing) is located. Ensure there is not a / at the end of the directory.
        * The cache will refresh. This extracts the mod dependancy information from every mod in the mods folder. This will reset any custom dependancy information and any keep flags you set. There is a button to do this manually [Important! > Refresh Cache], if ever required.
        * Disable all mods (Move All Unknown > To Disabled).
        * Add one half of the mods back (Operations > Add New Half) and test. If it works, move on. If it doesn't swap the halves (Operation > Swap Halves), this swaps which half is enabled.
        * Mark all the active mods that work to be kept (Operations > Mark Active Keep), this prevents them being moved by mass operations. 
        * Repeat until you have one mod left.

        If you have a mod that's required to recreate the issue, or mods that are *known* good you can manually enable the keep flag, simply select the mod in the side menu, and check the keep box. If there's a mod that does not specify a required dependency as a dependency you can manually add the dependencies' modId, simply type it in the box underneath the dependency block and click add. Sometimes both halves may crash, in that case disable all mods, then enable a new half.
        """, title='How To Use')

    elif event == 'About':
        sg.PopupNoButtons('Version '+VERSION+'\nWritten by Mason Gulu'+'\nhttps://github.com/MasonGulu/MC_ModTesting',title='About')

    # Enabled Side Operations
    elif event == 'ENABLED_filelist':
        try:
            filename = values['ENABLED_filelist'][0]
            win['ENABLED_filename'].update(filename)
            win['ENABLED_modId'].update(mod_filename_cache[filename]['modId'])
            win['ENABLED_keep'].update(mod_filename_cache[filename]['confirmedWorking'])
            win['ENABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
        except KeyError:
            pass
    
    elif event == 'ENABLED_keep':
        try:
            filename = values['ENABLED_filelist'][0]
            mod_filename_cache[filename]['confirmedWorking'] = values['ENABLED_keep']
            mod_id_cache[mod_filename_cache[filename]['modId']]['confirmedWorking'] = values['ENABLED_keep']
        except IndexError:
            pass
        except KeyError:
            pass 
    
    elif event == 'ENABLED_button_to_disable':
        try:
            filename = values['ENABLED_filelist'][0]
            os.replace(MOD_PATH+filename, DISABLED_MODS+filename)
            verifyDependancies()
            updateFilelists()
        except IndexError:
            pass 

    elif event == 'ENABLED_button_to_add_dependency':
        try:
            filename = values['ENABLED_filelist'][0]
            mod_filename_cache[filename]['dependencies'].append(values['ENABLED_input_for_new_dependency'])
            mod_id_cache[mod_filename_cache[filename]['modId']]['dependencies'].append(values['ENABLED_input_for_new_dependency'])
            win['ENABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
    
    elif event == 'ENABLED_button_to_remove_dependency':
        try:
            filename = values['ENABLED_filelist'][0]
            mod_filename_cache[filename]['dependencies'].remove(values['ENABLED_dependencies'][0])
            mod_id_cache[mod_filename_cache[filename]['modId']]['dependencies'].remove(values['ENABLED_dependencies'][0])
            win['ENABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass 

    # Disabled Side Operations
    elif event == 'DISABLED_filelist':
        try:
            filename = values['DISABLED_filelist'][0]
            win['DISABLED_filename'].update(filename)
            win['DISABLED_modId'].update(mod_filename_cache[filename]['modId'])
            win['DISABLED_keep'].update(mod_filename_cache[filename]['confirmedWorking'])
            win['DISABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
        except KeyError:
            pass
    
    elif event == 'DISABLED_keep':
        try:
            filename = values['DISABLED_filelist'][0]
            mod_filename_cache[filename]['confirmedWorking'] = values['DISABLED_keep']
            mod_id_cache[mod_filename_cache[filename]['modId']]['confirmedWorking'] = values['DISABLED_keep']
        except IndexError:
            pass
        except KeyError:
            pass 
    
    elif event == 'DISABLED_button_to_enable':
        try:
            filename = values['DISABLED_filelist'][0]
            os.replace(DISABLED_MODS+filename, MOD_PATH+filename)
            verifyDependancies()
            updateFilelists()
        except IndexError:
            pass 

    elif event == 'DISABLED_button_to_add_dependency':
        try:
            filename = values['DISABLED_filelist'][0]
            mod_filename_cache[filename]['dependencies'].append(values['DISABLED_input_for_new_dependency'])
            mod_id_cache[mod_filename_cache[filename]['modId']]['dependencies'].append(values['DISABLED_input_for_new_dependency'])
            win['DISABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
    
    elif event == 'DISABLED_button_to_remove_dependency':
        try:
            filename = values['DISABLED_filelist'][0]
            mod_filename_cache[filename]['dependencies'].remove(values['DISABLED_dependencies'][0])
            mod_id_cache[mod_filename_cache[filename]['modId']]['dependencies'].remove(values['DISABLED_dependencies'][0])
            win['DISABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass 

