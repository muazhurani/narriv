@echo off
setlocal

cd /d "%~dp0"
set "ROOT=%cd%"
set "API_PY=%ROOT%\.venv-api\Scripts\python.exe"
set "WORKER_PY=%ROOT%\.venv-worker\Scripts\python.exe"
set "WEB_DIR=%ROOT%\apps\web"

if not exist "%API_PY%" (
  echo [error] API venv python not found: "%API_PY%"
  exit /b 1
)

if not exist "%WORKER_PY%" (
  echo [error] Worker venv python not found: "%WORKER_PY%"
  exit /b 1
)

if not exist "%WEB_DIR%\package.json" (
  echo [error] Web app package.json not found in "%WEB_DIR%"
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [error] npm was not found on PATH.
  echo Install Node.js or open a shell where npm is available.
  exit /b 1
)

echo Starting Narriv services...
echo.

start "Narriv Worker" cmd /k "cd /d "%ROOT%" && "%WORKER_PY%" -m uvicorn apps.worker.app.main:app --host 127.0.0.1 --port 8001"
start "Narriv API" cmd /k "cd /d "%ROOT%" && "%API_PY%" -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000"
start "Narriv Web" cmd /k "cd /d "%WEB_DIR%" && npm run dev"

echo Worker: http://127.0.0.1:8001/health
echo API:    http://127.0.0.1:8000/health
echo Web:    http://127.0.0.1:3000
echo.
echo Three terminals were opened for worker, API, and web.

endlocal
