@echo off
REM Starts RASAVIGIL without a console window.
cd /d "%~dp0"
start "" pythonw main.py
