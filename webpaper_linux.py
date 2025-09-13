import gi
import os
import sys
import threading
import argparse
import mimetypes
from urllib.parse import urlparse
from werkzeug.wrappers import Request, Response
from werkzeug.serving import make_server
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import secure_filename

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")  # 更新到4.1版本
# 添加gtk-layer-shell支持
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, WebKit2, GtkLayerShell, Gdk

# 基于Werkzeug的HTTP服务器类
class WerkzeugHTTPServer:
    def __init__(self, directory, port=8080):
        self.directory = os.path.abspath(directory)
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.app = None
        
        # 验证目录是否存在
        if not os.path.exists(self.directory) or not os.path.isdir(self.directory):
            raise ValueError(f"Directory does not exist: {self.directory}")
        
    def _create_app(self):
        """创建WSGI应用"""
        def serve_static_file(environ, start_response):
            # 获取请求路径
            path = environ.get('PATH_INFO', '').lstrip('/')
            # 安全化文件名
            path = secure_filename(path) if path else 'index.html'
            
            # 构建文件路径
            if path:
                file_path = os.path.join(self.directory, path)
            else:
                file_path = os.path.join(self.directory, 'index.html')
                
            # 检查文件是否存在且在指定目录内
            if (os.path.exists(file_path) and 
                os.path.isfile(file_path) and 
                os.path.commonpath([self.directory, file_path]) == self.directory):
                
                # 确定内容类型
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                # 读取文件内容
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # 创建响应
                    response = Response(
                        response=content,
                        status=200,
                        content_type=content_type
                    )
                    
                    # 添加缓存控制头部
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    
                    # 添加安全头部
                    response.headers['X-Content-Type-Options'] = 'nosniff'
                    response.headers['X-Frame-Options'] = 'DENY'
                    
                    return response(environ, start_response)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
            else:
                # 文件未找到
                response = Response(
                    response=b"File not found",
                    status=404,
                    content_type="text/plain"
                )
                return response(environ, start_response)
        
        return serve_static_file
    
    def start(self):
        """启动HTTP服务器"""
        try:
            # 创建WSGI应用
            self.app = self._create_app()
            
            # 创建Werkzeug服务器
            self.server = make_server('localhost', self.port, self.app, threaded=True)
            self.server.host = 'localhost'  # 明确设置主机名
            
            # 在新线程中启动服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.is_running = True
            
            print(f"Werkzeug server started at http://localhost:{self.port}")
            print(f"Serving directory: {self.directory}")
            
        except Exception as e:
            print(f"Failed to start Werkzeug server: {e}")
            raise
    
    def stop(self):
        """停止HTTP服务器"""
        if self.is_running and self.server:
            try:
                self.server.shutdown()
                self.is_running = False
                print("Werkzeug server stopped")
            except Exception as e:
                print(f"Error stopping server: {e}")

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
    server = WerkzeugHTTPServer(directory)
    server.start()
    
    # 构造URL
    if filename:
        uri = f"http://localhost:{server.port}/{filename}"
    else:
        uri = f"http://localhost:{server.port}/"
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