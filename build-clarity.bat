@echo off
echo ================================
echo    Building Clarity Desktop
echo ================================
echo.

cd apps\desktop

echo Step 1: Preparing release...
node scripts/prepare-release.js
if %errorlevel% neq 0 (
    echo Failed to prepare release
    pause
    exit /b 1
)

echo.
echo Step 2: Building executable...
npm run build:win
if %errorlevel% neq 0 (
    echo Build failed
    pause
    exit /b 1
)

echo.
echo ================================
echo    Build Complete!
echo ================================
echo.
echo Your executable is ready in: apps\desktop\dist\
echo.
echo Files created:
echo - Clarity Setup.exe (installer)
echo - win-unpacked\ (portable version)
echo.
echo Test the executable before your demo!
echo.
pause
