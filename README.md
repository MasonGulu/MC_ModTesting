# About
This is a python script (with GUI) that allows for quick and effective modpack debugging. It uses binary searching to find a single mod causing issues in a modpack of huge size shockingly quickly.


# How to use
* First, when you launch the script a window will pop up, asking for your mod directory. Make sure to give the full path to where your mod folder (of the modpack you're testing) is located. Ensure there is not a / at the end of the directory.
* The cache will refresh. This extracts the mod dependancy information from every mod in the mods folder. This will reset any custom dependancy information and any keep flags you set. There is a button to do this manually [Important! > Refresh Cache], if ever required.
* Disable all mods (Move All Unknown > To Disabled).
* Add one half of the mods back (Operations > Add New Half) and test. If it works, move on. If it doesn't swap the halves (Operation > Swap Halves), this swaps which half is enabled.
* Mark all the active mods that work to be kept (Operations > Mark Active Keep), this prevents them being moved by mass operations. 
* Repeat until you have one mod left.

If you have a mod that's required to recreate the issue, or mods that are *known* good you can manually enable the keep flag, simply select the mod in the side menu, and check the keep box. If there's a mod that does not specify a required dependency as a dependency you can manually add the dependencies' modId, simply type it in the box underneath the dependency block and click add. Sometimes both halves may crash, in that case disable all mods, then enable a new half.

## Example Use
I have a modpack of 100 mods. Something is causing the game to crash when interacting with a modded item with an indeciferable crash report. Below are the steps I would take using this script:

First, I would disable all the mods (Move All Unknown > To Disabled). I'd then move one half over, and test the feature that crashed. The game runs successfully, so I then mark all to be kept and add another half. The game crashes when I test it this time, so I swap the mods (Notice, all the mods that worked before are kept (specifically, only the mods moved by the last add half operation are moved back)). The game crashes again, this is unusal but can be explained by a mod that is a requirement to other mods (so it gets included in both sets)...

To get around this crash, I disable all mods, this however leaves behind the mods flagged keep. I'm free to then move another half over (the halves are randomized each time). The game doesn't crash this time, and I repeat the process over and over again until I'm down to my last few mods, then I can make educated guesses on which one is causing a problem. Test, and repeat.

# Requirements
* toml
* PySimpleGUI
