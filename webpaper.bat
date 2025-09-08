REM uv run webpaper_win.py C:\Users\os_so\Projects\Others\SlideShowWallpaper
start "" ".\webpaper_NoConsole.exe" "D:\Projects\Others\SlideShowWallpaper" --monitor 1
timeout /t 6 /nobreak >nul
start "" ".\webpaper_NoConsole.exe" "D:\Projects\Others\SlideShowWallpaper" --monitor 0
