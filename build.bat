@echo off
setlocal
cd /d "%~dp0"
title Building SensMatch.exe

where python >nul 2>nul && (set "PY=python") || (set "PY=py")

echo Installing PyInstaller...
%PY% -m pip install --upgrade pyinstaller || goto fail

echo.
echo Including Borderlands turn speeds measured on this PC...
%PY% sensmatch.py --bake || goto fail

echo.
echo Building SensMatch.exe (takes a minute)...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name SensMatch --icon "%~dp0sensmatch.ico" --add-data "baked.json;." sensmatch.py || goto fail

copy /y "dist\SensMatch.exe" "SensMatch.exe" >nul
rmdir /s /q build dist 2>nul
del /q SensMatch.spec baked.json 2>nul

echo.
echo Done. SensMatch.exe is in this folder.
explorer /select,"%~dp0SensMatch.exe"
pause
exit /b 0

:fail
echo.
echo Build failed. Scroll up to see the error.
pause
exit /b 1
