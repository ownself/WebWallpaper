import gi
import os
import sys
import threading
import http.server
import socketserver
import webbrowser
import argparse
from urllib.parse import urlparse

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")  # 更新到4.1版本
# 添加gtk-layer-shell支持
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, WebKit2, GtkLayerShell, Gdk

# 简单的HTTP服务器类
class SimpleHTTPServer:
    def __init__(self, directory, port=8080):
        self.directory = directory
        self.port = port
        self.httpd = None
        self.server_thread = None
        
    def start(self):
        # 切换到指定目录
        os.chdir(self.directory)
        
        # 创建HTTP请求处理器，禁用缓存
        class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                # 添加禁用缓存的头部
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
        
        # 创建socket服务器
        self.httpd = socketserver.TCPServer(("", self.port), NoCacheHTTPRequestHandler)
        
        # 在新线程中启动服务器
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Local server started at http://localhost:{self.port}")
        
    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

# 创建WebView
view = WebKit2.WebView()

# 解析命令行参数
parser = argparse.ArgumentParser(description='WebPaper - A web-based wallpaper tool')
parser.add_argument('url_or_path', nargs='?', default="http://localhost:8080", help='URL or file path to load')
parser.add_argument('--clear-cache', action='store_true', help='Clear browser cache before loading')
args = parser.parse_args()

# 获取要加载的URL或文件路径
url_or_path = args.url_or_path
clear_cache = args.clear_cache

# 检查是本地文件路径还是URL
server = None
if os.path.exists(url_or_path):
    # 是本地文件路径
    if os.path.isfile(url_or_path):
        # 如果是文件，获取其所在目录
        directory = os.path.dirname(os.path.abspath(url_or_path))
        filename = os.path.basename(url_or_path)
    else:
        # 如果是目录，直接使用
        directory = os.path.abspath(url_or_path)
        filename = ""
    
    # 启动本地服务器
    server = SimpleHTTPServer(directory)
    server.start()
    
    # 构造URL
    if filename:
        uri = f"http://localhost:8080/{filename}"
    else:
        uri = f"http://localhost:8080/"
else:
    # 是URL，直接使用
    uri = url_or_path

# 根据命令行参数决定是否清除WebView缓存
if clear_cache:
    web_context = view.get_context()
    web_context.clear_cache()
    print("Cache cleared")

print(f"Loading: {uri}")
view.load_uri(uri)

# 禁用WebView的输入事件
view.set_can_focus(False)

# 创建窗口
win = Gtk.Window()
win.add(view)

# 初始化gtk-layer-shell
GtkLayerShell.init_for_window(win)
# 设置为背景层
GtkLayerShell.set_layer(win, GtkLayerShell.Layer.BACKGROUND)
# 锚定到所有边缘
GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.BOTTOM, True)
GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.LEFT, True)
GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT, True)
# 禁用键盘交互（使用新API）
GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.NONE)
# 禁用鼠标交互
GtkLayerShell.set_exclusive_zone(win, -1)

# 额外方法1: 设置窗口类型提示为桌面，减少输入交互
win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)

# 额外方法2: 设置空的输入区域，使窗口对所有输入事件透明
def on_realize(window):
    try:
        gdk_window = window.get_window()
        if gdk_window:
            # 创建一个空的cairo区域，使窗口对所有输入事件透明
            import cairo
            region = cairo.Region()
            gdk_window.input_shape_combine_region(region, 0, 0)
            # 设置窗口为被动输入模式
            gdk_window.set_pass_through(True)
    except Exception as e:
        print(f"Warning: Could not set input shape: {e}")

win.connect('realize', on_realize)

# 额外方法3: 禁用所有可能的输入事件
win.set_can_focus(False)
win.set_focus_on_map(False)
win.set_accept_focus(False)

# 额外方法4: 在GDK级别覆盖事件处理
def on_event_before(window, event):
    # 检查是否为指针事件
    event_type = event.type
    if event_type in [Gdk.EventType.BUTTON_PRESS,
                      Gdk.EventType.BUTTON_RELEASE,
                      Gdk.EventType.MOTION_NOTIFY,
                      Gdk.EventType.ENTER_NOTIFY,
                      Gdk.EventType.LEAVE_NOTIFY,
                      Gdk.EventType.SCROLL,
                      Gdk.EventType.TOUCH_BEGIN,
                      Gdk.EventType.TOUCH_UPDATE,
                      Gdk.EventType.TOUCH_END]:
        return True  # 返回True以停止事件传播
    return False  # 返回False以允许正常处理

# 连接到事件信号
win.connect('event', on_event_before)

# 移除fullscreen()调用，因为layer-shell会自动处理大小
win.show_all()

# 运行GTK主循环
Gtk.main()

# 停止服务器（如果已启动）
if server:
    server.stop()