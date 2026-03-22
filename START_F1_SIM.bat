@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start http://localhost:8000
python web_app.py
pause
