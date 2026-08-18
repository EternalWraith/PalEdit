import sys, os
from cx_Freeze import setup, Executable

build_options = {
    "excludes": [],
    "zip_include_packages": [],
    "include_files": ["palworld_pal_edit/resources/", "pals/"],
    "zip_includes": ["palworld_pal_edit/resources/", "pals/"],
}

#base = "Win32GUI" if sys.platform == "win32" else None
base = "gui"
base = "console"

setup(
    name = "PalEdit v0.13.1",
    version = "0.13.1",
    description = "A simple tool for editing PalWorld saves",
    options={"build_exe": build_options},
    executables=[Executable("PalEdit.py", base=base, icon="palworld_pal_edit/resources/MossandaIcon.ico")],
)
