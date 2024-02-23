@echo off
for %%I in (.) do set WD=%%~nxI
@title = %WD%
@call venv\Scripts\activate.bat
python autotest.py
pause
exit