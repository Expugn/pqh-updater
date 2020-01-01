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
1) Update `priconne-quest-helper/language/ja.json`
    - Make sure that all character names and thematics are up to date.
2) Run the DMM version of `Princess Connect! Re:Dive`
    - This will download the latest image assets to be extracted later.
3) Edit the `ACCOUNT_NAME` variable in `pqh-updater.py` with your current **Windows Account Username**.
4) Edit the `PRICONNE_QUEST_HELPER_DIRECTORY` variable to be the directory where `priconne-quest-helper` is located.

**AFTER THE ABOVE STEPS HAVE BEEN COMPLETED ; RUN SCRIPT**   
1) Copy required setup files from `priconne-quest-helper`
2) Grab latest `Princess Connect! Re:Dive` (JP) database.
3) Build updated `equipment_data.json`.
4) Create `data/translate_me.json` and pause program ; **User translates the item names in the program before continuing.**
5) Read `data/translate_me.json` and grab the latest English translations provided.
6) Build updated `character_data.json`
7) Build updated `quest_data.json`
8) Compile a list of new equipment and units
9) Extract new equipment and unit images
10) Rename all images and place them in their appropriate folder
11) Convert all images to `.webp` and place the `.webp` versions in their appropriate folder
12) Clean files ; The script has now finished running.

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
- webp
    - Used for `.png` to `.webp` conversion.
    - <https://pypi.org/project/webp/>
    - Also requires `Pillow`
- wget
    - Used to download the `Princess Connect! Re:Dive` database
    - <https://pypi.org/project/wget/>
