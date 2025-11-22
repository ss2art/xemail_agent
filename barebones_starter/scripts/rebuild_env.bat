@echo off
echo =====================================
echo  Rebuild shared Python Environment (Windows)
echo =====================================
setlocal

for %%I in ("%~dp0\..\..") do set REPO_ROOT=%%~fI
pushd "%REPO_ROOT%"

REM Remove old virtual environment if exists
if exist .venv (
    echo Removing existing root virtual environment...
    rmdir /s /q .venv
)

REM Create new virtual environment
python -m venv .venv
call .venv\Scripts\activate

echo Upgrading pip and setuptools...
python -m pip install --upgrade pip setuptools wheel

echo Installing shared requirements...
pip install -r requirements.txt

echo Done! To activate later, run:
echo     call .venv\Scripts\activate
echo Then start Streamlit with:
echo     python -m streamlit run barebones_starter\ui\streamlit_app.py

popd
endlocal
pause
