#!/usr/bin/env python3
"""
Windows version of WebPaper - Display web content as desktop background
Based on webpaper.py but adapted for Windows platform using pywebview and Windows API
"""

import os
import sys
import threading
import http.server
import socketserver
import webbrowser
import webview
import win32gui
import win32con
import argparse
from urllib.parse import urlparse

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
    import tkinter
    root = tkinter.Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

# Set window as desktop background
def set_as_desktop_background(hwnd):
    # Set window to be always on bottom
    win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                         win32con.SWP_NOSIZE | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE)
    
    # Additional styles to make it behave like desktop background
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                          ex_style | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TRANSPARENT)
    
    # Try to position behind desktop icons
    try:
        progman = win32gui.FindWindow("Progman", None)
        win32gui.SetParent(hwnd, progman)
    except:
        pass

# Window create event handler
def on_window_create(window):
    # Get window handle
    hwnd = window._hwnd  # Get the window handle correctly
    if hwnd:
        set_as_desktop_background(hwnd)

# Main function
def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='WebPaper - A web-based wallpaper tool for Windows')
    parser.add_argument('url_or_path', nargs='?', default="http://localhost:8080", help='URL or file path to load')
    parser.add_argument('--clear-cache', action='store_true', help='Clear browser cache before loading')
    args = parser.parse_args()
    
    # Get URL or file path to load
    url_or_path = args.url_or_path
    clear_cache = args.clear_cache

    # Check if it's a local file path or URL
    server = None
    if os.path.exists(url_or_path):
        # It's a local file path
        if os.path.isfile(url_or_path):
            # If it's a file, get its directory
            directory = os.path.dirname(os.path.abspath(url_or_path))
            filename = os.path.basename(url_or_path)
        else:
            # If it's a directory, use directly
            directory = os.path.abspath(url_or_path)
            filename = ""
        
        # Start local server
        server = SimpleHTTPServer(directory)
        server.start()
        
        # Construct URL
        if filename:
            uri = f"http://localhost:8080/{filename}"
        else:
            uri = f"http://localhost:8080/"
    else:
        # It's a URL, use directly
        uri = url_or_path

    print(f"Loading: {uri}")
    
    # Get screen dimensions
    width, height = get_screen_size()
    
    # Create webview window
    window = webview.create_window(
        'WebPaper', 
        uri,
        width=width,
        height=height,
        resizable=False,
        frameless=True,
        on_top=False  # We'll position it properly using Windows API
    )
    
    # Clear cache if requested
    if clear_cache:
        # Clear cache using webview's built-in method if available
        try:
            window.clear_cache()
            print("Cache cleared")
        except AttributeError:
            # If clear_cache method is not available, try alternative approach
            print("Cache clearing not supported in this version of pywebview")
    
    # Start webview with custom create handler
    webview.start(on_window_create, window)
    
    # Stop server if it was started
    if server:
        server.stop()

if __name__ == "__main__":
    main()