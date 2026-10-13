@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Running WindowZones...
python main.py
echo.
pause