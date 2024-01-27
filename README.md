# PalEdit
A simple tool for Editing and Generating Pals within PalWorld Saves

# Setup
First things first you'll need to download the ['palworld-save-tools' created by cheahjs](https://github.com/cheahjs/palworld-save-tools); make sure to download v0.12 so the `*.json` files are formatted correctly.
Both my program and their one require Python to run, ideally Python 3, [which can be downloaded here](https://www.python.org/downloads/).
For best results, make sure to add Python 3 to your PATH variable.

When this is installed, you will need to add PIL to your python installation. Simply open a Command Prompt and type the following
```
python -m pip install pillow
```

~~You will also need 'uesave.exe' for the Deserializer to work, [which is available here](https://github.com/trumank/uesave-rs/releases/download/v0.3.0/uesave-x86_64-pc-windows-msvc.zip).~~
You no longer need uesave.

# Manual Installation (Github Source Code)
Use 'run.bat' (faster results) or open the PalEdit.py using your Python IDE.
When in the app, simply load a _deserialized_ save file using the file menu. Wait patiently for it to load the `*.json` and gather the data.
You can then replace the traits of your Pals with ones that you want. 

# Automatic Installation (Nexus Mods)
Download the compiled executable from [Nexus Mods](https://www.nexusmods.com/palworld/mods/104). You will still need to download palworld-save-tools. 

# A word of warning
> [!CAUTION]
> It is advised that you backup ALL save files before using the tool; it will eventually do this on it's own but doesn't yet.

It is recommended to save your edited pals as a `*.pson` file for easier access. You can choose to save as a `*.pson` file. When you want to inject the changes into your save, simply save over your `Level.sav.json` and the program will splice it in at the correct location. Then Serialize the save again using 'palworld-save-tools' and put the resulting `Level.sav` into your save folder where the original one was. Load up PalWorld and enjoy. 
