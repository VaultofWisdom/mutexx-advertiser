@echo off
title Mutexx Advertiser
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python wurde nicht gefunden. Bitte von python.org installieren
  echo und beim Setup "Add python.exe to PATH" ankreuzen.
  pause
  exit /b 1
)

python start.py
if errorlevel 1 (
  echo.
  echo Die App wurde mit einem Fehler beendet.
  pause
)
