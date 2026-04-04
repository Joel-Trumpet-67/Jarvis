@echo off
REM build.bat — Build EIGENFORM.exe
REM Run from the project root: build.bat

echo.
echo ============================================================
echo   EIGENFORM — Building .exe
echo ============================================================
echo.

REM Run PyInstaller with the spec file
python -m PyInstaller eigenform.spec --noconfirm

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo Copying data folder to dist...
xcopy /E /I /Y data dist\EIGENFORM\data

echo.
echo ============================================================
echo   BUILD COMPLETE
echo   Your app is at: dist\EIGENFORM\EIGENFORM.exe
echo   Double-click EIGENFORM.exe to launch.
echo ============================================================
echo.
pause
