@echo off
echo Building WebPaper executable...
echo.

REM Ensure dependencies are installed
echo Installing/updating dependencies...
uv sync
echo.

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "WebPaper.exe" del "WebPaper.exe"
echo Cleaned previous builds.
echo.

REM Build both versions
echo Building console version...
uv run pyinstaller webpaper.spec

echo Building no-console version...
uv run pyinstaller webpaper_noconsole.spec

REM Check if build was successful
if exist "dist\WebPaper.exe" if exist "dist\WebPaper_NoConsole.exe" (
    echo.
    echo ✓ Build successful!
    echo.
    echo Two versions created:
    echo   1. dist\WebPaper.exe         - Shows console (for debugging)
    echo   2. dist\WebPaper_NoConsole.exe - No console (silent background)
    echo.
    echo You can copy them to any location and run directly.
    echo.
    echo Recommendation:
    echo   - Use WebPaper.exe for testing and troubleshooting
    echo   - Use WebPaper_NoConsole.exe for daily use
    
    REM Copy exes to root folder for convenience
    copy "dist\WebPaper.exe" "WebPaper.exe"
    copy "dist\WebPaper_NoConsole.exe" "WebPaper_NoConsole.exe"
    echo.
    echo Also copied to root folder for convenience.
) else (
    echo.
    echo ✗ Build failed!
    echo Check the output above for errors.
)

echo.
pause