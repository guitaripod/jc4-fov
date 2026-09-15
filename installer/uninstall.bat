@echo off
setlocal
set "GAME=%~1"
if "%GAME%"=="" set "GAME=%CD%"
if not exist "%GAME%\oo2core_7_win64_real.dll" (
  echo Nothing to uninstall in "%GAME%".
  pause
  exit /b 1
)
del /q "%GAME%\oo2core_7_win64.dll"
ren "%GAME%\oo2core_7_win64_real.dll" oo2core_7_win64.dll
del /q "%GAME%\jc4_fov.txt" 2>nul
del /q "%GAME%\jc4_fov.log" 2>nul
echo Uninstalled.
pause
