@echo off
echo === Precise3DM Lead Generator Setup ===

REM --- Step 1: Install Python if not present ---
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Installing Python 3.13 via winget...
    winget install -e --id Python.Python.3.13
)

REM --- Step 2: Create venv if not exists ---
IF NOT EXIST "experimental\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv experimental
)

REM --- Step 3: Activate venv ---
call experimental\Scripts\activate.bat

REM --- Step 4: Upgrade pip ---
python -m pip install --upgrade pip

REM --- Step 5: Install requirements ---
echo Installing dependencies...
pip install -r requirements.txt

echo === Setup complete! ===
pause
