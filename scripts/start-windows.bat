@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.."

docker compose up --build -d
if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

echo Application is starting on http://localhost:8000
popd
