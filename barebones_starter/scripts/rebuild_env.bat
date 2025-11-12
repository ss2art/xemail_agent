@echo off
echo =====================================
echo  Rebuild Python Environment (Windows)
echo =====================================
setlocal

REM Remove old virtual environment if exists
if exist .venv (
    echo Removing existing virtual environment...
    rmdir /s /q .venv
)

REM Create new virtual environment
python -m venv .venv
call .venv\Scripts\activate

echo Upgrading pip and setuptools...
python -m pip install --upgrade pip setuptools wheel

echo Installing requirements...
pip install -r requirements.txt

echo Done! To activate later, run:
echo     call .venv\Scripts\activate
echo Then start Streamlit with:
echo     streamlit run ui\streamlit_app.py

endlocal
pause
