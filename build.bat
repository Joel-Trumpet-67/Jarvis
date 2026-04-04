@echo off
REM build.bat — Build EIGENFORM.exe
REM Run from the project root: build.bat

echo.
echo ============================================================
echo   EIGENFORM — Building .exe
echo ============================================================
echo.

REM Kill any running instance before rebuilding
taskkill /F /IM EIGENFORM.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Run PyInstaller
python -m PyInstaller eigenform.spec --noconfirm --distpath dist2 --workpath build2

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo Copying data folder to dist2...
python -c "import shutil; shutil.copytree('data', 'dist2/EIGENFORM/data', dirs_exist_ok=True)"

echo.
echo ============================================================
echo   BUILD COMPLETE
echo   Your app is at: dist2\EIGENFORM\EIGENFORM.exe
echo   Double-click EIGENFORM.exe to launch.
echo ============================================================
echo.
pause
