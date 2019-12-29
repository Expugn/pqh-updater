# priconne-quest-helper Updater<br>(pqh-updater)

## Information
`pqh-updater` is a tool written in Python to automatically generate the `.json` files needed for 
[priconne-quest-helper](https://github.com/Expugn/priconne-quest-helper).

This tool uses the latest `Princess Connect! Re:Dive` (JP) database provided by **esterTion**.  
You can find the APIs esterTion provides on their website [here](<https://redive.estertion.win/api.htm>).  
As of this writing, the `Japan` and `Taiwan` server databases are available.

This repository is public in case people are interested in the process behind the updating of `priconne-quest-helper`.  
It is not useful at all for most cases.

This script has been written while using `Windows 10`, directory paths may differ if using different operating systems.

## Usage
Command: `python pqh-updater.py`

## Runtime Process
**BEFORE RUNNING THE PYTHON SCRIPT**
1) User places the required setup files in the appropriate locations:
    - `data/equipment_data.json`
        - Used to add existing English translations to the updated `equipment_data.json`
    - `data/ja.json`
        - Used to set the `.json` keys needed for the updated `character_data.json`
2) Run the DMM version of `Princess Connect! Re:Dive`
    - This will download the latest image assets to be extracted later.
3) Edit the `ACCOUNT_NAME` variable in `pqh-updater.py` with your current **Windows Account Username**.

**AFTER THE ABOVE STEPS HAVE BEEN COMPLETED**   
1) Grab latest `Princess Connect! Re:Dive` (JP) database.
2) Build updated `equipment_data.json`.
3) Create `data/translate_me.json` and pause program ; **User translates the item names in the program before continuing.**
4) Read `data/translate_me.json` and grab the latest English translations provided.
5) Build updated `character_data.json`
6) Build updated `quest_data.json`
7) Extract new equipment images ; Automatically rename the images to appropriately work.
8) Clean files ; The program has finished running.

## Dependencies
**THESE DEPENDENCIES MUST BE INSTALLED OR THE SCRIPT WILL NOT FUNCTION PROPERLY.**
- brotli
    - Used for decryption of `Princess Connect! Re:Dive` database
    - <https://github.com/google/brotli>
- decrunch
    - Used for `.unity3d` Texture2D decryption.
    - <https://github.com/HearthSim/decrunch>
    - `Build Tools for Visual Studio` (C++ Compiler) is required to install.
      - <https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019>
- lz4
    - Used for `.unity3d` Texture2D decryption.
    - <https://pypi.org/project/lz4/>
- Pillow
    - Used for `.unity3d` Texture2D decryption.
    - <https://pypi.org/project/Pillow/>
    - <https://github.com/python-pillow/Pillow>
- UnityPack
    - Used for `.unity3d` Texture2D decryption.
    - <https://github.com/HearthSim/UnityPack>
    - UnityPack has been provided and does not require an installation.
- wget
    - Used to download the `Princess Connect! Re:Dive` database
    - <https://pypi.org/project/wget/>
