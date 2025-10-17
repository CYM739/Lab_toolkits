@echo off
REM This script creates a virtual environment, installs packages, and runs the app.

REM Check if the 'venv' directory exists.
IF NOT EXIST "venv" (
    echo --- Creating a new virtual environment...
    python -m venv venv
    echo --- Virtual environment created.
)

echo --- Activating the virtual environment...
call "venv\Scripts\activate.bat"

echo --- Installing required packages from requirements.txt...
pip install -r requirements.txt

echo.
echo --- Starting the Streamlit application...
streamlit run app.py

@echo on