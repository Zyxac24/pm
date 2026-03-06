@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.."

docker compose down --remove-orphans
if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

echo Application is stopped.
popd
