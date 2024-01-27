# PalEdit
A simple tool for Editing and Generating Pals within PalWorld Saves.

You no longer need to download anything separately; only the release zip.

# Installation
Download the compiled executable from [Nexus Mods](https://www.nexusmods.com/palworld/mods/104) or over on the [Releases Page](https://github.com/EternalWraith/PalEdit/releases).

You can convert your save to a `*.sav.json` using the Convert menu at the top; then edit what you'd like and save the changes to that same `*.sav.json` file. Finally, convert it back to a `*.sav`

# A word of warning
When in the app, simply load a _deserialized_ save file using the file menu. Wait patiently for it to load the `*.json` and gather the data.
You can then replace the traits of your Pals with ones that you want. 

> [!CAUTION]
> It is advised that you backup ALL save files before using the tool; it will eventually do this on it's own but doesn't yet.

It is recommended to save your edited pals as a `*.pson` file for easier access. You can choose to save as a `*.pson` file. When you want to inject the changes into your save, simply save over your `Level.sav.json` and the program will splice it in at the correct location. Then Serialize the save again using 'palworld-save-tools' and put the resulting `Level.sav` into your save folder where the original one was. Load up PalWorld and enjoy. 
