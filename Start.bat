@echo off
title Mutexx Advertiser
cd /d "%~dp0"

rem Python 3.10+ is the only requirement. Try the "py" launcher first (installed
rem with every python.org setup), then "python" on PATH.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo.
  echo  Python was not found.
  echo  Install Python 3.10 or newer from https://www.python.org/downloads/
  echo  and tick "Add python.exe to PATH" during setup.
  echo.
  echo  Python wurde nicht gefunden. Bitte Python 3.10 oder neuer von
  echo  https://www.python.org/downloads/ installieren und beim Setup
  echo  "Add python.exe to PATH" ankreuzen.
  echo.
  pause
  exit /b 1
)

%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo.
  echo  Mutexx Advertiser needs Python 3.10 or newer.
  echo  Mutexx Advertiser braucht Python 3.10 oder neuer.
  echo.
  pause
  exit /b 1
)

%PY% start.py
if errorlevel 1 (
  echo.
  echo  The app stopped with an error. / Die App wurde mit einem Fehler beendet.
  pause
)
