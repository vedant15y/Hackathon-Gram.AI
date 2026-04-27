@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=%CD%\venv\Scripts\pythonw.exe"

if not exist "%PYTHON_EXE%" (
  echo [Gram.AI] Python environment not found at:
  echo %PYTHON_EXE%
  pause
  exit /b 1
)

echo [Gram.AI] Starting local server on http://127.0.0.1:8000
start "" "%PYTHON_EXE%" "%CD%\launch_server.py"

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8000

echo [Gram.AI] Browser opened. You can close this helper window.
exit /b 0
