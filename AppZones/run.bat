@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Running AppZones...
python main.py
echo.
pause