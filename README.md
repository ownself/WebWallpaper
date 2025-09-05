# WebPaper

将网页设置为桌面壁纸的工具。

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

### 详细说明
- **默认模式**: 不带参数运行时，程序会启动一个默认的本地服务器，并将默认页面设置为桌面壁纸。
- **在线URL**: 直接指定一个在线网址，程序会加载该网页并设置为桌面壁纸。
- **本地文件**: 指定本地HTML文件路径，程序会加载该文件并设置为桌面壁纸。
- **本地目录**: 指定本地目录路径，程序会自动启动一个本地服务器来服务该目录，并将目录中的默认页面设置为桌面壁纸。

## 依赖

- Python 3
- GTK 3
- WebKit2
- gtk-layer-shell

## 退出

按 Ctrl+C 退出程序。