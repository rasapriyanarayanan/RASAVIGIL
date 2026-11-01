@echo off
REM Builds a standalone RASAVIGIL.exe (no Python needed on the target PC).
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name RASAVIGIL ^
  --icon assets\owl.ico ^
  --add-data "assets;assets" ^
  --add-data "rasavigil\default_config.json;rasavigil" ^
  main.py
echo.
echo Done. Your program is in dist\RASAVIGIL.exe
pause
