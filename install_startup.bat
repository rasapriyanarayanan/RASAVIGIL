@echo off
REM Make RASAVIGIL start automatically when you log in to Windows.
cd /d "%~dp0"
python main.py --install-startup
pause
