#!/usr/bin/env python3
"""
WebPaper - Display web content as desktop background on Windows
Simplified approach focusing on basic functionality
"""

import os
import sys
import threading
import webview
import win32gui
import win32con
import argparse
from urllib.parse import urlparse
import time
import ctypes
import pystray
from PIL import Image, ImageDraw

# Enable high DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Global variables for application management
tray_icon = None
server_instance = None
webview_window = None
app_running = True

# Create a simple icon for the system tray
def create_tray_icon():
    """Create a simple icon image for the system tray"""
    # Create a 64x64 image with a simple design
    image = Image.new('RGB', (64, 64), color='blue')
    draw = ImageDraw.Draw(image)
    
    # Draw a simple "W" for WebPaper
    draw.text((20, 20), "W", fill='white', anchor="mm")
    
    return image

# Tray menu actions
def quit_webpaper(icon, item):
    """Quit the application - immediate force exit"""
    print("Force quitting WebPaper...")
    
    # Stop tray icon immediately to prevent multiple clicks
    if icon:
        try:
            icon.stop()
        except:
            pass
    
    # Immediate force termination - no cleanup delays
    def immediate_exit():
        import ctypes
        import subprocess
        
        try:
            # Method 1: Use Windows taskkill to terminate current process
            current_pid = os.getpid()
            subprocess.run(['taskkill', '/F', '/PID', str(current_pid)], 
                          creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            try:
                # Method 2: Direct Windows API call
                import ctypes.wintypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetCurrentProcess()
                kernel32.TerminateProcess(handle, 0)
            except:
                # Method 3: Python exit
                os._exit(0)
    
    # Execute immediately - no threading delay
    immediate_exit()

def show_about(icon, item):
    """Show about information"""
    print("WebPaper - Web-based wallpaper tool for Windows")

# Create system tray
def create_system_tray():
    """Create and run the system tray icon"""
    global tray_icon
    
    # Create menu items
    menu = pystray.Menu(
        pystray.MenuItem("About", show_about),
        pystray.MenuItem("Quit", quit_webpaper)
    )
    
    # Create the tray icon
    tray_icon = pystray.Icon(
        "WebPaper",
        create_tray_icon(),
        "WebPaper - Web Wallpaper",
        menu
    )
    
    # Run the tray icon (this blocks)
    tray_icon.run()

# Stable HTTP server using werkzeug
class StableHTTPServer:
    def __init__(self, directory, port=8080):
        self.directory = directory
        self.port = port
        self.server = None
        self.server_thread = None
        
    def create_app(self):
        """Create WSGI application for serving static files"""
        def application(environ, start_response):
            from werkzeug.wrappers import Request, Response
            from werkzeug.exceptions import NotFound, HTTPException
            import mimetypes
            import pathlib
            
            request = Request(environ)
            
            try:
                # Get the requested path
                path = request.path.lstrip('/')
                if not path:
                    path = 'index.html'
                
                # Security check: prevent directory traversal
                file_path = os.path.join(self.directory, path)
                file_path = os.path.abspath(file_path)
                
                if not file_path.startswith(os.path.abspath(self.directory)):
                    raise NotFound()
                
                # Check if file exists
                if not os.path.exists(file_path):
                    raise NotFound()
                
                # Read file
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Guess content type
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                # Create response with no-cache headers
                response = Response(
                    content,
                    mimetype=content_type,
                    headers={
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                )
                
                return response(environ, start_response)
                
            except HTTPException as e:
                return e(environ, start_response)
            except Exception as e:
                # Return 500 error for unexpected exceptions
                response = Response(f'Internal Server Error: {str(e)}', status=500)
                return response(environ, start_response)
        
        return application
        
    def start(self):
        try:
            from werkzeug.serving import make_server
            print("Using Werkzeug HTTP server")
            
            app = self.create_app()
            self.server = make_server('localhost', self.port, app, threaded=True)
            
            # Start server in new thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"Local server started at http://localhost:{self.port}")
            
        except ImportError:
            # Fallback to basic Python server if werkzeug is not available
            print("Werkzeug not available, using basic Python server with error handling")
            self._start_python_server()
    
    def _start_python_server(self):
        """Fallback Python server with improved error handling"""
        import http.server
        import socketserver
        
        os.chdir(self.directory)
        
        # Create HTTP request handler with cache disabled and better error handling
        class ImprovedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                # Add headers to disable caching
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
            
            def copyfile(self, source, outputfile):
                """Copy file with proper error handling for client disconnections"""
                try:
                    super().copyfile(source, outputfile)
                except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                    # Client disconnected - this is normal, don't log as error
                    pass
                except Exception as e:
                    # Log other unexpected errors
                    print(f"Unexpected error during file transfer: {e}")
            
            def log_error(self, format, *args):
                # Suppress connection reset errors in logs
                msg = format % args
                if "ConnectionResetError" in msg or "WinError 10054" in msg:
                    return
                super().log_error(format, *args)
        
        # Create socket server
        self.httpd = socketserver.TCPServer(("", self.port), ImprovedHTTPRequestHandler)
        
        # Start server in new thread
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Local server started at http://localhost:{self.port}")
        
    def stop(self):
        if hasattr(self, 'server') and self.server:
            self.server.shutdown()
        elif hasattr(self, 'httpd') and self.httpd:
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
                
                # Set extended styles for wallpaper behavior
                # WS_EX_TOOLWINDOW - prevents it from appearing in taskbar
                # WS_EX_NOACTIVATE - prevents it from being activated
                # WS_EX_TRANSPARENT - makes it transparent to mouse events (key for fixing drag response)
                # WS_EX_LAYERED - required for transparency and proper mouse event handling
                new_ex_style = (win32con.WS_EX_NOACTIVATE | 
                              win32con.WS_EX_TOOLWINDOW | 
                              win32con.WS_EX_TRANSPARENT | 
                              win32con.WS_EX_LAYERED)
                
                # Remove WS_EX_APPWINDOW to prevent taskbar appearance
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex_style = (ex_style & ~win32con.WS_EX_APPWINDOW) | new_ex_style
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
                
                # Configure layered window attributes for proper mouse transparency
                try:
                    # LWA_ALPHA = 0x2, make window 99% opaque but with proper mouse transparency
                    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 252, 0x2)
                except Exception as layer_err:
                    print(f"Warning: Could not set layered window attributes: {layer_err}")
                
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
                            new_ex_style = (win32con.WS_EX_NOACTIVATE | 
                                          win32con.WS_EX_TOOLWINDOW | 
                                          win32con.WS_EX_TRANSPARENT | 
                                          win32con.WS_EX_LAYERED)
                            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                            ex_style = (ex_style & ~win32con.WS_EX_APPWINDOW) | new_ex_style
                            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
                            
                            # Maintain layered window attributes
                            try:
                                ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 252, 0x2)
                            except:
                                pass
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
    global server_instance, webview_window
    
    parser = argparse.ArgumentParser(description='WebPaper - A web-based wallpaper tool for Windows')
    parser.add_argument('url_or_path', nargs='?', default="http://localhost:8080", help='URL or file path to load')
    parser.add_argument('--clear-cache', action='store_true', help='Clear browser cache before loading')
    args = parser.parse_args()
    
    url_or_path = args.url_or_path
    clear_cache = args.clear_cache

    # Check if it's a local file path or URL
    if os.path.exists(url_or_path):
        if os.path.isfile(url_or_path):
            directory = os.path.dirname(os.path.abspath(url_or_path))
            filename = os.path.basename(url_or_path)
        else:
            directory = os.path.abspath(url_or_path)
            filename = ""
        
        server_instance = StableHTTPServer(directory)
        server_instance.start()
        
        if filename:
            uri = f"http://localhost:8080/{filename}"
        else:
            uri = f"http://localhost:8080/"
    else:
        uri = url_or_path

    print(f"Loading: {uri}")
    
    width, height = get_screen_size()
    
    # Start system tray in a separate thread
    tray_thread = threading.Thread(target=create_system_tray, daemon=True)
    tray_thread.start()
    print("System tray icon created. Right-click the icon to quit.")
    print("Press Ctrl+C in this terminal to also quit.")
    
    # Create webview window in MAIN thread (required by webview)
    webview_window = webview.create_window(
        'WebPaper',
        uri,
        width=width,
        height=height,
        resizable=False,
        frameless=True,
        on_top=False,
        transparent=False
    )
    
    if clear_cache:
        try:
            webview_window.clear_cache()
            print("Cache cleared")
        except AttributeError:
            print("Cache clearing not supported in this version of pywebview")
    
    try:
        # Start webview in main thread (this will block until window is closed)
        webview.start(on_window_create, webview_window, gui='edgechromium')
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, shutting down...")
    finally:
        # Cleanup when webview exits
        if server_instance:
            server_instance.stop()
        print("Application terminated")

if __name__ == "__main__":
    main()