from turtle import update
import toml
from zipfile import ZipFile
import os
import random
import PySimpleGUI as sg
import csv
import json

EXTRACTED_TOML_DIR = 'extractedTomls/'
DISABLED_MODS_DIR = 'inactiveMods/'
VERSION = '0.30'

sg.theme('SystemDefault')

try:
    os.mkdir(EXTRACTED_TOML_DIR)
except FileExistsError:
    pass

try:
    os.mkdir(DISABLED_MODS_DIR)
except FileExistsError:
    pass 

MOD_PATH = sg.PopupGetFolder('Select your mods folder.', default_path='/home/mason/Downloads/ATM6-1.8.19-server/mods')
if MOD_PATH == None or MOD_PATH == '':
    print("Cancelled.")
    quit()

if MOD_PATH[-1] != '/' or MOD_PATH[-1] != '\\':
    MOD_PATH += '/'

# Example mod_filename_cache
# mod_filename_cache = {
#   'filename.jar': {
#       'modId': 'coolmod',
#       'dependencies': {'forge', 'minecraft'},
#       'filename': 'filename.jar',
#       'keepFlag': False
#     }
# }

settings = {
    'autoResolveDependencies': True,
    'autoVerifyDependencies': True,
    'autoCloseDependenciesWindow': True,

    'autoCloseCacheWindow': True
}

mod_filename_cache = {}

mod_id_cache = {}

def cacheForgeMod(path,modFilename):
    # This function takes path (the path to the mod file '.minecraft/mods'), and modFilename (the filename of the mod 'example.jar')
    # It then tries to extract the mods.toml file from the Jar file, then gets dependency and modId information from the mods.toml file
    # Then it adds entries to both dictionaries (mod_filename_cache and mod_id_cache)
    try:
        with ZipFile(path+modFilename) as z:
            z.extract('META-INF/mods.toml', EXTRACTED_TOML_DIR+modFilename)
    except Exception as temp:
        print('!! Erorr: '+modFilename+' is probably not a forge mod.')
        print(temp)
        return [False,'META-INF/mods.toml does not exist in the mod.']
        # Extract META-INF/mods.toml from the .jar file
    try:
        temp = toml.load(EXTRACTED_TOML_DIR+modFilename+'/META-INF/mods.toml')
    except toml.TomlDecodeError as err:
        return [False, err]
    tempId = temp['mods'][0]['modId']
    # Get the modId from the mods.toml we extracted
    mod_filename_cache[modFilename] = {'modId': tempId, 'dependencies': [], 'filename': modFilename, 'keepFlag': False}
    mod_id_cache[tempId] = mod_filename_cache[modFilename]
    # Set up the filename and id cache.
    try:
        for mod in temp['dependencies'][tempId]:
            # Iterate every mod in the dependencies list
            if (mod['modId'] not in ('minecraft', 'forge') and mod['mandatory']):
                # If the requirement is not minecraft or forge, and it's a mandatory dependency then add it to the caches
                mod_filename_cache[modFilename]['dependencies'].append(mod['modId'])
    except KeyError:
        pass 
    except TypeError:
        return [False, 'The mod does not follow Forge dependency standards.']
    return [True,'']

def cacheFabricMod(path,modFilename):
    # This function takes path (the path to the mod file '.minecraft/mods'), and modFilename (the filename of the mod 'example.jar')
    # It then tries to extract the mods.toml file from the Jar file, then gets dependency and modId information from the mods.toml file
    # Then it adds entries to both dictionaries (mod_filename_cache and mod_id_cache)
    try:
        with ZipFile(path+modFilename) as z:
            z.extract('fabric.mod.json', EXTRACTED_TOML_DIR+modFilename)
    except Exception as temp:
        print('!! Erorr: '+modFilename+' is probably not a fabric mod.')
        print(temp)
        return False, ''
        # Extract META-INF/mods.toml from the .jar file
    try:
        temp = json.load(open(EXTRACTED_TOML_DIR+modFilename+'/fabric.mod.json'))
    except json.JSONDecodeError as err:
        print('!! Error: '+modFilename+' JSON file is formatted incorrectly.. ', err)
        mod_filename_cache[modFilename] = {'dependencies':[], 'keepFlag':False, 'filename':modFilename}
        return False, err
    tempId = temp['id']
    # Get the modId from the mods.toml we extracted
    mod_filename_cache[modFilename] = {'modId': tempId, 'dependencies': [], 'filename': modFilename, 'keepFlag': False}
    mod_id_cache[tempId] = mod_filename_cache[modFilename]
    # Set up the filename and id cache.
    try:
        for mod in temp['depends']:
            # Iterate every mod in the dependencies list
            if (mod not in ('fabric', 'fabricloader','minecraft', 'java', 'fabric-resource-loader-v0' )):
                # If the requirement is not minecraft or fabric, and it's a mandatory dependency then add it to the caches
                mod_filename_cache[modFilename]['dependencies'].append(mod)
    except KeyError:
        pass 
    return True, ''

mods_last_swapped = []

def addModByID(id):
    for x in os.listdir(DISABLED_MODS_DIR):
        try:
            if (mod_filename_cache[x]['modId'] == id):
                os.replace(DISABLED_MODS_DIR+x, MOD_PATH+x)
                return True 
        except KeyError:
            pass 
    return False

def verifyDependencies():
    mods = os.listdir(MOD_PATH)
    layout = [[sg.Text('',key='modname', size=(30,1))],
                [sg.ProgressBar(len(mods), orientation='h', size=(30,20),key='bar')],
                [sg.Multiline(key='warnlist', size=(40,10))]]
    win = sg.Window('Verifying Dependencies...', layout=layout, finalize=True)
    keepWindowOpen = False
    dependenciesMet = True
    activemods = []
    for x in mods:
        try:
            activemods.append(mod_filename_cache[x]['modId'])
        except KeyError:
            win['warnlist'].print('[WARN]','Cache is out of date! File',x,'not cached.')
            keepWindowOpen = True
    i = 0
    for x in activemods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)

        for y in mod_id_cache[x]['dependencies']:
            if y not in activemods:
                if settings['autoResolveDependencies']:
                    if not addModByID(y):
                        win['warnlist'].print('[ERROR]',y,'required by',x,'not found.')
                        keepWindowOpen = True
                        dependenciesMet = False 
                    else:
                        win['warnlist'].print('[INFO]',y,'enabled to meet requirements of',x)
                        activemods.append(y)

                else:
                    win['warnlist'].print('[WARN]', y, 'is required for', x,)
                    dependenciesMet = False
                    keepWindowOpen = True
    if dependenciesMet:
        win['warnlist'].print('[INFO]', 'SUCCESS, dependencies met.')
    if not keepWindowOpen and settings['autoCloseDependenciesWindow']:
        win.close()
    

def swap():
    global mods_last_swapped
    if len(mods_last_swapped) == 0:
        sg.PopupOK('There are no mods to swap.', title='Swap Mods')
        return
    temp = []
    for x in os.listdir(DISABLED_MODS_DIR):
        os.replace(DISABLED_MODS_DIR+x, MOD_PATH+x)
        temp.append(x)
    for x in mods_last_swapped:
        os.replace(MOD_PATH+x, DISABLED_MODS_DIR+x)
    mods_last_swapped = temp
    if settings['autoVerifyDependencies']:
        verifyDependencies()

def removeAllMods():
    # This function moves all unlocked mods from MOD_PATH to DISABLED_MODS_DIR
    global mods_last_swapped
    mods_last_swapped = []
    for x in os.listdir(MOD_PATH):
        try:
            if (not mod_filename_cache[x]['keepFlag']):
                os.replace(MOD_PATH+x, DISABLED_MODS_DIR+x)
        except KeyError:
            sg.PopupNoButtons(x+' is not cached.', title='Cache out of date!')
    if settings['autoVerifyDependencies']:
        verifyDependencies()

def addAllMods():
    # This function moves all unlocked mods from DISABLED_MODS_DIR to MOD_PATH
    global mods_last_swapped
    mods_last_swapped = []
    for x in os.listdir(DISABLED_MODS_DIR):
        os.replace(DISABLED_MODS_DIR+x, MOD_PATH+x)
        mods_last_swapped.append(x)
    if settings['autoVerifyDependencies']:
        verifyDependencies()

def addHalf():
    # This funciton moves a random half of the mods from the DISABLED_MODS_DIR to MOD_PATH
    global mods_last_swapped 
    dir = os.listdir(DISABLED_MODS_DIR)
    mods_last_swapped = random.sample(dir, round(len(dir)/2))
    for x in mods_last_swapped:
        os.replace(DISABLED_MODS_DIR+x, MOD_PATH+x)
    if settings['autoVerifyDependencies']:
        verifyDependencies()

def cacheAllForge():
    global mod_filename_cache
    global mod_id_cache
    mod_filename_cache = {}
    mod_id_cache = {}
    mods = os.listdir(MOD_PATH)
    dmods = os.listdir(DISABLED_MODS_DIR)
    layout = [[sg.Text('',key='modname', expand_x=True)],
                [sg.ProgressBar(len(mods)+len(dmods), orientation='h', size=(30,20),key='bar')],
                [sg.Multiline(key='warnlist',size=(40,10), expand_x=True)]]
    keepWindowOpen = False
    modsCachedSuccessfully = True
    win = sg.Window('Caching Mods...', layout=layout, finalize=True)
    i = 0
    for x in mods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)
        status = cacheForgeMod(MOD_PATH,x)
        if not status[0]:
            win['warnlist'].print('[ERROR]', x, 'is not a Forge Mod or an issue occured.', status[1])
            keepWindowOpen = True
            modsCachedSuccessfully = False
    for x in dmods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)
        status = cacheForgeMod(DISABLED_MODS_DIR,x)
        if not status[0]:
            win['warnlist'].print('[ERROR]', x, 'is not a Forge Mod or an issue occured.', status[1])
            keepWindowOpen = True
            modsCachedSuccessfully = False 
    if modsCachedSuccessfully:
        win['warnlist'].print('[INFO]','Success, all mods cached.')
    if not keepWindowOpen and settings['autoCloseCacheWindow']:
        win.close()

def cacheAllFabric():
    global mod_filename_cache
    global mod_id_cache
    mod_filename_cache = {}
    mod_id_cache = {}
    mods = os.listdir(MOD_PATH)
    dmods = os.listdir(DISABLED_MODS_DIR)
    layout = [[sg.Text('',key='modname', size=(30,1),expand_x=True)],
                [sg.ProgressBar(len(mods)+len(dmods), orientation='h', size=(30,20),key='bar')],
                [sg.Multiline(key='warnlist',size=(40,10),expand_x=True)]]
    keepWindowOpen = False
    modsCachedSuccessfully = True
    win = sg.Window('Caching Mods...', layout=layout, finalize=True)
    i = 0
    for x in mods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)
        status = cacheFabricMod(MOD_PATH,x)
        if not status[0]:
            if status[1] is json.JSONDecodeError:
                win['warnlist'].print('[ERROR]', x, 'is not a Fabric Mod')
            else:
                win['warnlist'].print('[ERROR]', x, 'has an inproperly formatted JSON file.', status[1])
            keepWindowOpen = True
            modsCachedSuccessfully = False
    for x in dmods:
        i += 1
        win['modname'].update(x)
        win['bar'].UpdateBar(i)
        status = cacheFabricMod(DISABLED_MODS_DIR,x)
        if not status[0]:
            if status[1] is json.JSONDecodeError:
                win['warnlist'].print('[ERROR]', x, 'is not a Fabric Mod')
            else:
                win['warnlist'].print('[ERROR]', x, 'has an inproperly formatted JSON file.', status[1])
            keepWindowOpen = True
            modsCachedSuccessfully = False 
    if modsCachedSuccessfully:
        win['warnlist'].print('[INFO]','Success, all mods cached.')
    if not keepWindowOpen and settings['autoCloseCacheWindow']:
        win.close()

def updateFilelists():
    disabled_filelist = os.listdir(DISABLED_MODS_DIR)
    disabled_filelist.sort()
    enabled_filelist = os.listdir(MOD_PATH)
    enabled_filelist.sort()
    win['DISABLED_filelist'].update(values=disabled_filelist)
    win['ENABLED_filelist'].update(values=enabled_filelist)
    win.finalize()

DEFAULT_WIDTH = 30

columns = [[],[],[],[]]
columns[0] = [[sg.Text('Disabled Mods')],[sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,size=(DEFAULT_WIDTH,20),key='DISABLED_filelist',enable_events=True)]]

columns[1] = [[sg.Text('Filename:')],[sg.Text('',size=(DEFAULT_WIDTH,1),key='DISABLED_filename')],
                [sg.Text('ModId:')], [sg.Text('',size=(DEFAULT_WIDTH,1),key='DISABLED_modId')],
                [sg.Checkbox('Keep',default=False,key='DISABLED_keep', enable_events=True)],
                [sg.Button(button_text='>>> Enable >>>',key='DISABLED_button_to_enable')],
                [sg.Text('Dependencies:')],
                [sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,size=(DEFAULT_WIDTH,5),key='DISABLED_dependencies')],
                [sg.Input(size=(DEFAULT_WIDTH,1),key='DISABLED_input_for_new_dependency')],
                [sg.Button(button_text='Add New', key='DISABLED_button_to_add_dependency'), sg.Button(button_text='Remove', key='DISABLED_button_to_remove_dependency')]]

columns[2] = [[sg.Text('Enabled Mods')],[sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,size=(DEFAULT_WIDTH,20),key='ENABLED_filelist',enable_events=True)]]

columns[3] = [[sg.Text('Filename:')],[sg.Text('',size=(DEFAULT_WIDTH,1),key='ENABLED_filename')],
                [sg.Text('ModId:')], [sg.Text('',size=(DEFAULT_WIDTH,1),key='ENABLED_modId')],
                [sg.Checkbox('Keep',default=False,key='ENABLED_keep', enable_events=True)],
                [sg.Button(button_text='<<< Disable <<<',key='ENABLED_button_to_disable')],
                [sg.Text('Dependencies:')],
                [sg.Listbox(values=[],select_mode=sg.LISTBOX_SELECT_MODE_SINGLE,size=(DEFAULT_WIDTH,5),key='ENABLED_dependencies')],
                [sg.Input(size=(DEFAULT_WIDTH,1),key='ENABLED_input_for_new_dependency')],
                [sg.Button(button_text='Add New', key='ENABLED_button_to_add_dependency'), sg.Button(button_text='Remove', key='ENABLED_button_to_remove_dependency')]]

TAB_BUTTON_SIZE = (15,1)
tab_start = [[sg.Combo(['Forge', 'Fabric'], key='modloader', readonly=True, default_value='Forge',size=TAB_BUTTON_SIZE)],
            [sg.Button('Refresh Cache', key='Refresh Cache', size=TAB_BUTTON_SIZE), sg.Button('Reset Keep Flags', key='Reset Keep Flags', size=TAB_BUTTON_SIZE), sg.Button('Manually Cache', key='addcache', size=TAB_BUTTON_SIZE)],
            [sg.Button('Save...', key='Save...', size=TAB_BUTTON_SIZE),sg.Button('Load...', key='Load...',size=TAB_BUTTON_SIZE)]]
tab_operations = [[sg.Button('Enable All', key='Enable All', size=TAB_BUTTON_SIZE), sg.Button('Disable All', key='Disable All', size=TAB_BUTTON_SIZE)],
                [sg.Button('Add New Half', key='Add New Half', size=TAB_BUTTON_SIZE), sg.Button('Swap Halves', key='Swap Halves', size=TAB_BUTTON_SIZE)],
                [sg.Button('Verify Dependencies', key='Verify Dependencies', size=TAB_BUTTON_SIZE), sg.Button('Mark Active Keep', key='Mark Active Keep', size=TAB_BUTTON_SIZE)]]
tab_settings = [[sg.Button('Apply Settings', key='apply_settings', size=TAB_BUTTON_SIZE)],
                [sg.Checkbox('Auto Resolve Dependencies',key='autoResolveDependencies', default=settings['autoResolveDependencies']), 
                    sg.Checkbox('Auto Verify Dependencies', key='autoVerifyDependencies', default=settings['autoVerifyDependencies']),
                    sg.Checkbox('Auto Close Dependencies Window', key='autoCloseDependenciesWindow', default=settings['autoCloseDependenciesWindow'])],
                [sg.Checkbox('Auto Close Cache Window', key='autoCloseCacheWindow', default=settings['autoCloseCacheWindow'])]]

layout = [[sg.TabGroup([[sg.Tab('Start', tab_start), sg.Tab('Operations', tab_operations), sg.Tab('Settings', tab_settings)]],expand_x=True)], [sg.Column(columns[0]),sg.Column(columns[1]),sg.VerticalSeparator(),sg.Column(columns[2]),sg.Column(columns[3])]]


win = sg.Window('MC Mod Tester', layout=layout)

win.finalize()
updateFilelists()

while True:
    event, values = win.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    # Every event should refresh the file listings

    if event == 'Refresh Cache':
        selection = sg.PopupYesNo('Refreshing the cache will wipe all flags you\'ve set.\nAre you sure?',title='Refresh Cache') 
        if selection == 'Yes':
            if values['modloader'] == 'Forge':
                cacheAllForge()
            elif values['modloader'] == 'Fabric':
                cacheAllFabric()
            updateFilelists()
    
    elif event == 'Reset Keep Flags':
        selection = sg.PopupYesNo('This will set all keep flags to false.\nAre you sure?', title='Reset Flags')
        if selection == 'Yes':
            for x in mod_filename_cache:
                mod_filename_cache[x]['keepFlag'] = False

    elif event == 'addcache':
        # Add a mod to the cache manually
        tmplayout = [[sg.Text('Filename', size=(10,1)), sg.InputText(key='filename')],
                    [sg.Text('ModId', size=(10,1)), sg.InputText(key='modId')],
                    [sg.Button('Cancel'), sg.Button('Submit')]]
        tmpwin = sg.Window('Manually Add Cache Item', layout=tmplayout)
        events, values = tmpwin.read()
        if events == 'Submit':
            mod_filename_cache[values['filename']] = {'modId':values['modId'], 'filename':values['filename'], 'dependencies':[], 'keepFlag': False}
            mod_id_cache[values['modId']] = mod_filename_cache[values['filename']]
        tmpwin.close()

    elif event == 'Verify Dependencies':
        verifyDependencies()
        updateFilelists()

    elif event == 'apply_settings':
        settings['autoResolveDependencies'] = values['autoResolveDependencies']
        settings['autoVerifyDependencies'] = values['autoVerifyDependencies']
        settings['autoCloseDependenciesWindow'] = values['autoCloseDependenciesWindow']

        settings['autoCloseCacheWindow'] = values['autoCloseCacheWindow']

    elif event == 'Save...':
        filename = sg.PopupGetFile('Choose a file to save your state.', save_as=True, default_extension='.csv', file_types=[("CSV Files",(".csv"))])
        if filename != None:
            with open(filename, 'w') as csvfile:
                w = csv.writer(csvfile)
                temp = []
                for x in mods_last_swapped:
                    temp.append(x)
                w.writerow(temp)
                for x in mod_id_cache:
                    temp = []
                    temp.append(x)
                    temp.append(mod_id_cache[x]['keepFlag'])
                    temp.append(mod_id_cache[x]['filename'])
                    for y in mod_id_cache[x]['dependencies']:
                        temp.append(y)
                    w.writerow(temp)

    elif event == 'Load...':
        filename = sg.PopupGetFile('Choose a file to load a state.',default_extension='.csv', file_types=[("CSV Files",(".csv"))])
        if filename != None:
            try:
                with open(filename, 'r') as csvfile:
                    r = csv.reader(csvfile)
                    temp = []
                    for row in r:
                        temp.append(row)
                    for x in temp[0]:
                        mods_last_swapped.append(x)
                    for y in range(1, len(temp)):
                        mod_filename_cache[temp[y][2]] = {'modId': temp[y][0], 'filename': temp[y][2], 'keepFlag': (temp[y][1] == 'True'), 'dependencies': []}
                        for z in range(3, len(temp[y])):
                            mod_filename_cache[temp[y][2]]['dependencies'].append(temp[y][z])
                        mod_id_cache[temp[y][0]] = mod_filename_cache[temp[y][2]]
                    mods_last_swapped = []
                    
            except Exception as err:
                print("!! An issue occured loading!",err)

    elif event == 'Enable All':
        addAllMods()
        updateFilelists()
    
    elif event == 'Disable All':
        removeAllMods()
        updateFilelists()
    
    elif event == 'Add New Half':
        addHalf()
        updateFilelists()

    elif event == 'Swap Halves':
        swap()
        updateFilelists()

    elif event == 'Mark Active Keep':
        for x in os.listdir(MOD_PATH):
            mod_filename_cache[x]['keepFlag'] = True

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
            filename = values['ENABLED_filelist'][-1]
            win['ENABLED_filename'].update(filename)
            win['ENABLED_modId'].update(mod_filename_cache[filename]['modId'])
            win['ENABLED_keep'].update(mod_filename_cache[filename]['keepFlag'])
            win['ENABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
        except KeyError:
            pass
    
    elif event == 'ENABLED_keep':
        for filename in values['ENABLED_filelist']:
            try:
                mod_filename_cache[filename]['keepFlag'] = values['ENABLED_keep']
            except IndexError:
                pass
            except KeyError:
                pass 
    
    elif event == 'ENABLED_button_to_disable':
            for filename in values['ENABLED_filelist']:
                try:
                    os.replace(MOD_PATH+filename, DISABLED_MODS_DIR+filename)
                except IndexError:
                    pass 
            if settings['autoVerifyDependencies']:
                verifyDependencies()
            updateFilelists()

    elif event == 'ENABLED_button_to_add_dependency':
        try:
            filename = values['ENABLED_filelist'][-1]
            mod_filename_cache[filename]['dependencies'].append(values['ENABLED_input_for_new_dependency'])
            win['ENABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
    
    elif event == 'ENABLED_button_to_remove_dependency':
        try:
            filename = values['ENABLED_filelist'][-1]
            mod_filename_cache[filename]['dependencies'].remove(values['ENABLED_dependencies'][0])
            win['ENABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass 

    # Disabled Side Operations
    elif event == 'DISABLED_filelist':
        try:
            filename = values['DISABLED_filelist'][-1]
            win['DISABLED_filename'].update(filename)
            win['DISABLED_modId'].update(mod_filename_cache[filename]['modId'])
            win['DISABLED_keep'].update(mod_filename_cache[filename]['keepFlag'])
            win['DISABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
        except KeyError:
            pass
    
    elif event == 'DISABLED_keep':
        for filename in values['DISABLED_filelist']:
            try:
                mod_filename_cache[filename]['keepFlag'] = values['ENABLED_keep']
            except IndexError:
                pass
            except KeyError:
                pass 
    
    elif event == 'DISABLED_button_to_enable':
            for filename in values['DISABLED_filelist']:
                try:
                    os.replace(DISABLED_MODS_DIR+filename, MOD_PATH+filename)
                except IndexError:
                    pass 
            if settings['autoVerifyDependencies']:
                verifyDependencies()
            updateFilelists()

    elif event == 'DISABLED_button_to_add_dependency':
        try:
            filename = values['DISABLED_filelist'][-1]
            mod_filename_cache[filename]['dependencies'].append(values['DISABLED_input_for_new_dependency'])
            win['DISABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass
    
    elif event == 'DISABLED_button_to_remove_dependency':
        try:
            filename = values['DISABLED_filelist'][-1]
            mod_filename_cache[filename]['dependencies'].remove(values['DISABLED_dependencies'][0])
            win['DISABLED_dependencies'].update(values=mod_filename_cache[filename]['dependencies'])
        except IndexError:
            pass 
    

