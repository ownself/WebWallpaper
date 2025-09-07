# WebPaper 打包说明

## 打包为 EXE 文件

### 快速打包
直接运行打包脚本：
```bash
build_exe.bat
```

### 手动步骤
1. **安装依赖**：
   ```bash
   uv sync
   ```

2. **打包**：
   ```bash
   # 控制台版本（用于调试）
   uv run pyinstaller webpaper.spec
   
   # 无控制台版本（后台运行）
   uv run pyinstaller webpaper_noconsole.spec
   ```

## 打包结果

会生成两个版本：
- **WebPaper.exe** - 显示控制台窗口，用于调试
- **WebPaper_NoConsole.exe** - 无控制台窗口，纯后台运行

## 使用方法

### 控制台版本（WebPaper.exe）
```bash
# 基本使用
WebPaper.exe

# 指定URL或本地文件/文件夹
WebPaper.exe https://example.com
WebPaper.exe "C:\path\to\html\file.html"
WebPaper.exe "C:\path\to\folder"

# 清除缓存
WebPaper.exe --clear-cache
```

### 无控制台版本（WebPaper_NoConsole.exe）
- 双击运行，直接进入后台
- 只能通过系统托盘图标退出
- 适合日常使用

## 退出方法
1. **系统托盘**：右键托盘图标选择"Quit"
2. **键盘**：控制台版本可用 Ctrl+C
3. **任务管理器**：强制结束进程（备用）

## 注意事项
- 首次运行可能较慢（需要解压文件）
- EXE文件包含所有依赖，无需额外安装
- 可以复制到任何位置运行
- 建议将 WebPaper_NoConsole.exe 添加到开机启动项