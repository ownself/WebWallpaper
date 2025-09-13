# WebPaper

这是个写来自用的小工具，可以将网页设置为桌面壁纸，在Arch Linux + Hyprland环境下测试通过，允许使用[Rain](https://github.com/rocksdanister/rain)这样的基于Web的动态壁纸（原Windows平台的Lively Wallpaper）

## 功能

- 将网页设置为桌面背景
- 支持在线URL和本地HTML文件
- 自动启动本地服务器来服务本地文件
- 无交互模式，不会影响其他应用程序使用

## 使用方法

### 基本用法
```bash
# 不带参数运行，将启动默认服务器
python3 webpaper.py

# 加载在线URL作为壁纸
python3 webpaper.py https://example.com

# 加载本地HTML文件作为壁纸
python3 webpaper.py /path/to/your/file.html

# 加载本地目录作为壁纸（会自动启动本地服务器）
python3 webpaper.py /path/to/your/directory
```

### 可执行文件

或者也可以使用已用PyInstaller打包好的可执行文件：

```bash
# 不带参数运行，将启动默认服务器
webpaper

# 加载在线URL作为壁纸
webpaper https://example.com

# 加载本地HTML文件作为壁纸
webpaper /path/to/your/file.html

# 加载本地目录作为壁纸（会自动启动本地服务器）
webpaper /path/to/your/directory
```

### 详细说明
- **默认模式**: 不带参数运行时，程序会启动一个默认的本地服务器，并将默认页面设置为桌面壁纸。
- **在线URL**: 直接指定一个在线网址，程序会加载该网页并设置为桌面壁纸。
- **本地文件**: 指定本地HTML文件路径，程序会加载该文件并设置为桌面壁纸。
- **本地目录**: 指定本地目录路径，程序会自动启动一个本地服务器来服务该目录，并将目录中的默认页面设置为桌面壁纸。

## 依赖

- Python 3.13+
- GTK 3
- WebKit2
- gtk-layer-shell
- Python packages (automatically installed):
  - pygobject>=3.54.1
  - pyinstaller>=6.15.0
  - werkzeug>=3.1.3

## 安装依赖

### Ubuntu/Debian
```bash
# 安装系统依赖
sudo apt update
sudo apt install python3 python3-pip libgtk-3-dev libwebkit2gtk-4.0-dev libgtk-layer-shell-dev

# 安装Python依赖
pip3 install pygobject pyinstaller werkzeug
```

### Fedora
```bash
# 安装系统依赖
sudo dnf install python3 python3-pip gtk3-devel webkit2gtk4.0-devel gtk-layer-shell-devel

# 安装Python依赖
pip3 install pygobject pyinstaller werkzeug
```

### Arch Linux
```bash
# 安装系统依赖
sudo pacman -S python python-pip gtk3 webkit2gtk gtk-layer-shell

# 安装Python依赖
pip3 install pygobject pyinstaller werkzeug
```

## 退出

按 Ctrl+C 退出程序。
