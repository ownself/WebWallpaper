#!/usr/bin/env python3
"""
WebPaper - Display web content as desktop background on Windows
Simplified approach focusing on basic functionality
"""

import os
import sys
import threading
import http.server
import socketserver
import webview
import win32gui
import win32con
import argparse
from urllib.parse import urlparse
import time
import ctypes

# Enable high DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Simple HTTP server class (same as Linux version)
class SimpleHTTPServer:
    def __init__(self, directory, port=8080):
        self.directory = directory
        self.port = port
        self.httpd = None
        self.server_thread = None
        
    def start(self):
        # Change to specified directory
        os.chdir(self.directory)
        
        # Create HTTP request handler with cache disabled
        class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                # Add headers to disable caching
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
        
        # Create socket server
        self.httpd = socketserver.TCPServer(("", self.port), NoCacheHTTPRequestHandler)
        
        # Start server in new thread
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Local server started at http://localhost:{self.port}")
        
    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

# Get screen dimensions
def get_screen_size():
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except:
        import tkinter
        root = tkinter.Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height

# Window create event handler
def on_window_create(window):
    print("Window created, starting background setup")
    
    # Start a thread to handle window setup after a delay
    def setup_window():
        time.sleep(1.0)  # Give the window more time to fully initialize
        
        # Try to find our window by its title
        hwnd = None
        for _ in range(20):  # Try for 2 seconds
            hwnd = win32gui.FindWindow(None, "WebPaper")
            if hwnd:
                break
            time.sleep(0.1)
        
        if hwnd:
            print(f"Found window handle: {hwnd}")
            
            # Get screen dimensions
            width, height = get_screen_size()
            print(f"Screen size: {width}x{height}")
            
            # Set window styles to make it behave like a wallpaper
            try:
                # Set window style to popup (no title bar, no border)
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, win32con.WS_POPUP)
                
                # Set extended styles
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                # WS_EX_TOOLWINDOW - prevents it from appearing in taskbar
                # WS_EX_NOACTIVATE - prevents it from being activated
                # WS_EX_TRANSPARENT - makes it transparent to mouse events
                # WS_EX_LAYERED - for better transparency handling
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                                      ex_style | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TRANSPARENT)
                
                # Remove WS_EX_APPWINDOW which would cause it to appear in taskbar
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style & ~win32con.WS_EX_APPWINDOW)
                
                # Position window to cover entire screen
                win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, width, height,
                                     win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)
                
                print("Window configured as wallpaper")
                
                # Keep it at the bottom periodically
                def keep_wallpaper():
                    while True:
                        try:
                            # Ensure it stays at the bottom and doesn't appear in taskbar
                            win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, width, height,
                                                 win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)
                            # Re-apply styles periodically to ensure they're maintained
                            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                                                  ex_style | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TRANSPARENT)
                            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style & ~win32con.WS_EX_APPWINDOW)
                            time.sleep(1.0)
                        except:
                            break
                
                # Start background thread to maintain position
                wallpaper_thread = threading.Thread(target=keep_wallpaper, daemon=True)
                wallpaper_thread.start()
                
            except Exception as e:
                print(f"Error configuring window: {e}")
        else:
            print("Could not get window handle")
    
    setup_thread = threading.Thread(target=setup_window, daemon=True)
    setup_thread.start()

# Main function
def main():
    parser = argparse.ArgumentParser(description='WebPaper - A web-based wallpaper tool for Windows')
    parser.add_argument('url_or_path', nargs='?', default="http://localhost:8080", help='URL or file path to load')
    parser.add_argument('--clear-cache', action='store_true', help='Clear browser cache before loading')
    args = parser.parse_args()
    
    url_or_path = args.url_or_path
    clear_cache = args.clear_cache

    # Check if it's a local file path or URL
    server = None
    if os.path.exists(url_or_path):
        if os.path.isfile(url_or_path):
            directory = os.path.dirname(os.path.abspath(url_or_path))
            filename = os.path.basename(url_or_path)
        else:
            directory = os.path.abspath(url_or_path)
            filename = ""
        
        server = SimpleHTTPServer(directory)
        server.start()
        
        if filename:
            uri = f"http://localhost:8080/{filename}"
        else:
            uri = f"http://localhost:8080/"
    else:
        uri = url_or_path

    print(f"Loading: {uri}")
    
    width, height = get_screen_size()
    
    # Create webview window
    window = webview.create_window(
        'WebPaper',
        uri,
        width=width,
        height=height,
        resizable=False,
        frameless=True,
        on_top=False,
        transparent=False  # Disable transparency for better compatibility
    )
    
    if clear_cache:
        try:
            window.clear_cache()
            print("Cache cleared")
        except AttributeError:
            print("Cache clearing not supported in this version of pywebview")
    
    # Start webview
    webview.start(on_window_create, window, gui='edgechromium')
    
    if server:
        server.stop()

if __name__ == "__main__":
    main()