@echo off
setlocal enabledelayedexpansion
set "GAME=%~1"
if "%GAME%"=="" set "GAME=%CD%"
if not exist "%GAME%\JustCause4.exe" (
  echo Could not find JustCause4.exe in "%GAME%".
  echo Drag your Just Cause 4 folder onto this file, or copy this file into that folder and run it.
  pause
  exit /b 1
)
for %%A in ("%GAME%\oo2core_7_win64.dll") do set "SIZE=%%~zA"
if not exist "%GAME%\oo2core_7_win64_real.dll" (
  if !SIZE! LSS 500000 (
    echo oo2core_7_win64.dll looks like a mod already and the original is missing.
    echo Verify the game files in Steam, then run this again.
    pause
    exit /b 1
  )
  ren "%GAME%\oo2core_7_win64.dll" oo2core_7_win64_real.dll
)
copy /y "%~dp0oo2core_7_win64.dll" "%GAME%\" >nul
if not exist "%GAME%\jc4_fov.txt" copy /y "%~dp0jc4_fov.txt" "%GAME%\" >nul
echo Installed. Edit jc4_fov.txt in the game folder to change the FOV, then start the game.
pause
