# **PalEdit**

**A simple tool for Editing and Generating Pals within PalWorld saves.**

You no longer need to download anything separately; only the release zip.

## **Table of Contents**

- [**Table of Contents**](#table-of-contents)
- [**Installation**](#installation)
- [**A word of warning**](#a-word-of-warning)
- [**Usage**](#usage)
- [**Saving Edited Pals**](#saving-edited-pals)
- [**Backing up your save**](#backing-up-your-save)
- [**Project roadmap**](#project-roadmap)

## **Installation**

Download the compiled executable from [Nexus Mods](https://www.nexusmods.com/palworld/mods/104) or over on the [Releases Page](https://github.com/EternalWraith/PalEdit/releases).

## **A word of warning**

When in the app, simply load a _deserialized_ save file using the file menu. Wait **patiently** for it to load the `*.json` and gather the data.
You can then replace the traits of your Pals with ones that you want.

> [!CAUTION]
> It is advised that you backup ALL save files before using the tool; it will eventually do this on it's own but doesn't yet.
> For more information on how to do this, see the [**Backing up your save**](#backing-up-your-save) section.

It is recommended to save your edited pals as a `*.pson` file for easier access. You can choose to save as a `*.pson` file. When you want to inject the changes into your save, simply save over your `Level.sav.json` and the program will splice it in at the correct location. Then Serialize the save again using 'palworld-save-tools' and put the resulting `Level.sav` into your save folder where the original one was. Load up PalWorld and enjoy.

## **Usage**

1. Convert your save to a `*.sav.json` using the Convert menu at the top.
2. Load the `*.sav.json` file using the File menu.
3. Edit your Pals as desired.
4. Save the changes to the same `*.sav.json` file.
5. Convert it back to a `*.sav` using the Convert menu again.

## **Saving Edited Pals**

1. Save your edited pals as a `*.pson` file for easier access.
2. Choose to save as a `*.pson` file.
3. To inject the changes into your save, save over your `Level.sav.json`.
4. The program will splice it in at the correct location.
5. Serialize the save again using the Convert menu.
6. Put the resulting `Level.sav` into your save folder where the original one was.
7. Load up PalWorld and enjoy.

## **Backing up your save**

It is advised that you backup ALL save files before using the tool. Although the tool will eventually do this on its own, it doesn't yet.

On Windows, the saves can be found in the following locations:

- `%appdata%/Local/Pal/Save/Savegames`
- `C:\Users\<username>\AppData\Local\Pal\Saved\SaveGames`

Replace `<username>` with your Windows username.

If you’ve installed Palworld via Steam, you can also access your save files by following these steps:

1. Open your Steam library.
2. Right-click on Palworld, then select Manage > Browse local files.
3. This will open the folder where Palworld’s installed files are stored, named Pal.
4. From here, go to Saved > SaveGames to access your save files for the game.

## **Project roadmap**

- **v0.3 Release:**
  - [x] Integrate SaveTools into PalEdit natively.
  - [x] Nickname Compatibility
  - [x] Ability to Change Species

- **Future Releases:**
  - [ ] Defence Editing
  - [ ] Gender Swapping
  - [ ] Converting Pal to Lucky
  - [ ] Converting Pal to Alpha (Boss)
  - [ ] Generating new Pals
  - [ ] Player Filtered Pals so you know who belongs to who
  - [ ] Sorted lists so that everything is alphabetical
  - [ ] Database system to make things easier to update
  - [ ] Localisation support for Chinese, Japanese, Spanish, French, German, and English (for starters)
  - [ ] Rank editing (Pal Essence Condenser)
  - [ ] Stat Editing (Hero Statue)
  - [ ] Pal Deletion
