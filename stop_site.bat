@echo off
setlocal

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":8000 .*LISTENING"') do (
  taskkill /PID %%P /F >nul 2>&1
  echo [Gram.AI] Stopped process %%P on port 8000
)

exit /b 0
