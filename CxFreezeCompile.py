import sys, os
from cx_Freeze import setup, Executable

build_options = {
    "excludes": [],
    "zip_include_packages": [],
    "include_files": ["resources/"],
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name = "PalEdit v0.5",
    version = "0.5",
    description = "A simple tool for editing PalWorld saves",
    options={"build_exe": build_options},
    executables=[Executable("PalEdit.py", base=base, icon="resources/MossandaIcon.ico")],
)
