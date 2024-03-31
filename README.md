> [!NOTE]
> Because apparently it needs to be stated here as well as in the NexusMods; the application is __unsigned__ and therefore can flag up a __False Positive__ with some anti-virus software. If you are really scared about it being a virus, download the application and [compile it yourself](#️-building-from-source-on-windows). Look through the source code. [You can see a virus report here](https://www.virustotal.com/gui/file/d20dcab42b8ba55442c27c16235c27fb80d16f7494ee32a790767a2eb38ceefb)

<h1 align="center">PalEdit</h1>

<div align="center">

[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/EternalWraith/PalEdit.svg)](https://github.com/EternalWraith/PalEdit/pulls)
[![GitHub Issues](https://img.shields.io/github/issues/EternalWraith/PalEdit.svg)](https://github.com/EternalWraith/PalEdit/issues)
![Python](https://img.shields.io/badge/python-FFD43B.svg?&logo=python&logoColor=ffde57&color=4584b6)
<br>
**A simple tool for editing and generating Pals within PalWorld saves.**

</div>

> ⚠️ **Before Opening a new Issue**: Please check the [**🚧 Project roadmap**](#-project-roadmap) section to ensure that your concern or feature request hasn't already been addressed or is planned for a future release. Also check the [Open Issues](https://github.com/EternalWraith/PalEdit/issues).

## **📚 Table of Contents**

- [**🚀 Installation**](#-installation)
- [**⚠️ A word of warning**](#️-a-word-of-warning)
- [**🕹️ Usage**](#️-usage)
- [**💾 Cloning Pals**](#-cloning-pals)
- [**📦 Backing up your save**](#-backing-up-your-save)
- [**🛠️ Building from source (on Windows)**](#️-building-from-source-on-windows)
- [**🚧 Project roadmap**](#-project-roadmap)

## **🚀 Installation**

Download the compiled executable from [Nexus Mods](https://www.nexusmods.com/palworld/mods/104) or over on the [Releases Page](https://github.com/EternalWraith/PalEdit/releases).

## **⚠️ A word of warning**

> [!CAUTION]
> It is advised that you backup ALL save files before using the tool; it will eventually do this on it's own but doesn't yet.
> For more information on how to do this, see the [**📦 Backing up your save**](#-backing-up-your-save) section.

## **🕹️ Usage**

1. Open PalEdit
2. Select your save file
3. Edit your Pals
4. Save
5. Done

## **💾 Cloning Pals**

1. Load a save
2. Select a Pal
3. Click "Dump Pal", and choose a filename (any name)
4. Click "Add Pal" and select the file you just made
5. Edit the clone

## **📦 Backing up your save**

It is advised that you backup ALL save files before using the tool. Although the tool will eventually do this on its own, it doesn't yet.

On Windows, the saves can be found in the following locations:

- `%LocalAppData%\Pal\Saved\SaveGames\`

If you’ve installed Palworld via Steam, you can also access your save files by following these steps:

1. Open your Steam library.
2. Right-click on Palworld, then select Manage > Browse local files.
3. This will open the folder where Palworld’s installed files are stored, named Pal.
4. From here, go to Saved > SaveGames to access your save files for the game.

## **🛠️ Building from source (on Windows)**

1. Install Python, at least version 3.10 (for the CI/CD pipeline we are using Python 3.12.1). You can get it from [here](https://www.python.org/downloads/windows/). Don't forget to check the box to add Python to your PATH.
2. Open a PowerShell window in the root of the project.
3. Create a virtual environment:

    ```powershell
    python -m venv venv
    ```

4. Run the following command to activate the virtual environment:

    ```powershell
    .\venv\Scripts\Activate.ps1
    ```

    > If you get an error about running scripts, you may need to run the following command first:
    >
    > ```powershell
    > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    > ```

5. Install the required packages:

    ```powershell
    pip install -r requirements.txt
    ```

6. Build the binary file. Once done, it will be located in the `dist` folder:

    ```powershell
    pyinstaller --noconfirm --onefile --windowed --icon "palworld_pal_edit/resources/MossandaIcon.ico" --hidden-import=PIL "PalEdit.py"
    ```

    > If you get any error about virus, check the top of this README file. Also this issue comment with some further explanation may interest you: [Issue #41](https://github.com/EternalWraith/PalEdit/issues/41#issuecomment-1914567848)

7. Copy the `resources` folder into the `dist` folder. This is required to display the images inside PalEdit:

    ```powershell
    cp -r palworld_pal_edit\resources dist
    ```

8. Run your newly built binary file and enjoy.

> **Alternatively, to run PalEdit without compiling it, follow steps 1 to 5 and then run the following command:**
>
>    ```powershell
>    python PalEdit.py
>    ```

## **🚧 Project roadmap**

> [!NOTE]
> We could really use the help of the community to make this tool better.
> If you think you can help us deliver any of the features listed below, please feel free to open a pull request.

- **Pending features:**
  - [ ] Pal Deletion
  - [ ] Stat Editing (Hero Statue)
  - [ ] Edit Pals Nickname
  - [ ] Improve Pal ListBox UI to mimic ingame PalBox
  - [ ] Add update notification if a newer version is found
  - [ ] Automatic savefile backup

- **v0.3 Release:**
  - [x] Integrate SaveTools into PalEdit natively.
  - [x] Nickname Compatibility
  - [x] Ability to Change Species

- **v0.4 Release:**
  - [x] Defence Editing
  - [x] Gender Swapping
  - [x] Sorted lists so that everything is alphabetical
  - [x] Rank editing (Pal Essence Condenser)
  - [x] Workspeed Editing
  - [x] Pal presets to speed up creation of workers, fighters and tanks
  - [x] Compatibility for Tower Boss and Human captures
  - [x] Overhauled Attack IV and Level Editing to make it easier
  - [x] Moved species editing to main app instead of tucked away in the Tools menu

- **v0.4.8 Release:**
  - [x] Converting Pal to Lucky
  - [x] Converting Pal to Alpha (Boss)
  - [x] Player Filtered Pals so you know who belongs to who

- **v0.5 Release:**
  - [x] Simplify Loading/Converting/Saving process
  - [x] Database system to make things easier to update
  - [x] Pal Info Database Overhaul
 
- **v0.6 Release:**
  - [x] Generate New Pals/Clone Old Pals
  - [x] Localisation Support
  - [x] Equipped Move Editing
  - [x] Learnt Move Editing
  - [X] Optimised Loading and Saving
  - [X] Changed Code structure to OOP
