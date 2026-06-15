@echo off
setlocal

cd /d "%~dp0"

set "RUN_DIR=%~1"
if "%RUN_DIR%"=="" set "RUN_DIR=out\experience\yellow_sign_cold_case"

set "PORT=%~2"
if "%PORT%"=="" set "PORT=8765"

echo Starting RPF viewer...
echo Run output: %RUN_DIR%
echo URL: http://127.0.0.1:%PORT%/

start "RPF Viewer Backend" cmd /k python -m rpf viewer "%RUN_DIR%" --port %PORT%
timeout /t 2 >nul
start "" "http://127.0.0.1:%PORT%/"

endlocal
