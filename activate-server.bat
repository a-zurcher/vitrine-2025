@echo off
REM change to your project directory
cd /d "%USERPROFILE%\Documents\serveur-vitrine"

REM activate the virtual environment
call .venv\Scripts\activate.bat

REM start uvicorn in minimized window
start /min python -m uvicorn main:app --host 0.0.0.0 --port 8000 --no-use-colors

REM exit the batch script
exit
