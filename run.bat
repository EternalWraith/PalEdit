@ECHO OFF

@REM Check if python is installed, error if not
python --version 2>NUL
IF %ERRORLEVEL% NEQ 0 (
    python3 --version 2>NUL
    IF %ERRORLEVEL% NEQ 0 (
        py3 --version 2>NUL
        IF %ERRORLEVEL% NEQ 0 (
            ECHO Python is not installed. Please install python and try again.
            PAUSE
            EXIT /B 1
        ) ELSE (
            SET PYTHON_BIN=py3
        )
    ) ELSE (
        SET PYTHON_BIN=python3
    )
) ELSE (
    SET PYTHON_BIN=python
)

@REM Switch to script directory
cd /D "%~dp0"

ECHO "%~dp0"
%PYTHON_BIN% PalEdit.py
IF %ERRORLEVEL% NEQ 0 pause