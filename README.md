# pqh-updater | Node.js Version

## Information
`pqh-updater` is a tool written using JavaScript (Node.js) and Python to automatically generate the `.json` files needed for 
[priconne-quest-helper](https://github.com/Expugn/priconne-quest-helper).

This repository is public in case people are interested in the process behind the updating of `priconne-quest-helper` or datamining `Princess Connect! Re:Dive` in general.  
It is not useful at all for public or general use.

This has been written while using `Windows 10`, directory paths may differ if using different operating systems.

## Why Switch to Node.js?
The previous version of `pqh-updater` that was strictly written in Python had some issues lately. It required a bit too much
manual work still to update `princess-quest-helper`.

Main issue with the old version of `pqh-updater` was that it just downloaded the database from **esterTion**'s website, which has
had an increase in traffic as of late. This means that sometimes it was hard to grab the database.

The main reason for the language switch though was because I wrote the database fetching code on Node.js for a Discord bot, lol.

**Python is still a requirement however, since there are some scripts that must be used to properly update `priconne-quest-helper`.**

> So what's new?

Well, `pqh-updater | Node.js Version` downloads the database straight from `Princess Connect! Re:Dive`'s CDN, so **esterTion**'s source is no longer needed as a middle man.

Also, having the DMM version of the game to get the images from is no longer required, because those are grabbed from `Princess Connect! Re:Dive`'s CDN as well.

Really, the only bothersome requirement to use this is having a copy of `priconne-quest-helper` saved somewhere.

Feature wise, everything is still pretty much the same besides the inclusion of the spritesheet creator that the old public version didn't have.

## Usage
Rename the provided `config.new.json` to `config.json`. 
Under `system`, change `priconne-quest-helper_directory` to the directory where you saved a copy of `priconne-quest-helper`

Example Path: `C:\\Users\\%UserName%\\Desktop\\priconne-quest-helper`

Once you set the path, **make sure you have all the dependencies installed** (listed below).

Then you can just run the program via the command line interface like:<br>
`node pqh-updater.js`

**Unless you know what you're doing, do NOT edit the other values in the `config.json`.**

## Requirements
#### System
Node.js `v11.15.0` or above<br>
Python 3

#### python-tools/deserialize.py
- **lz4** `pip install lz4`
- **Pillow** `pip install Pillow`
- **decrunch** `pip install decrunch`
- **UnityPack** (provided) [GitHub](https://github.com/HearthSim/UnityPack)

#### python-tools/create-spritesheet.py
- **Pillow** `pip install Pillow`

## Special Thanks
> **esterTion**<br>
For making their unity-texture-toolkit which helped a lot in figuring out how to pull files from Princess Connect Re:Dive's CDN.<br>
Also for releasing their Coneshell_call.exe to help decrypt the master.db