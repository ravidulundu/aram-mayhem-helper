@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Create the project environment and install requirements-quality.txt first.
  exit /b 1
)
".venv\Scripts\python.exe" quality.py %*
exit /b %errorlevel%
