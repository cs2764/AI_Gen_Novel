@echo off
chcp 65001 >nul
title AI网络小说生成器 - Gradio 5.38.0

echo.
echo ========================================
echo    AI网络小说生成器 - Gradio 5.38.0
echo ========================================
echo.
echo ��� 正在启动应用...
echo ��� 使用环境: gradio5_env
echo ��� 界面版本: Gradio 5.38.0 独立版
echo.

REM 检查虚拟环境是否存在
if not exist "gradio5_env" (
    echo ❌ 错误: gradio5_env 虚拟环境不存在
    echo ��� 请先运行环境安装脚本
    pause
    exit /b 1
)

REM 检查主程序文件是否存在
if not exist "app.py" (
    echo ❌ 错误: app.py 主程序文件不存在
    pause
    exit /b 1
)

REM 使用gradio5_env环境的Python直接启动应用
echo ��� 使用gradio5_env环境启动...

echo ��� 启动AI网络小说生成器...
echo.
echo ��� 启动完成后，浏览器将自动打开应用界面
echo ��� 如果浏览器未自动打开，请手动访问显示的地址
echo ⏹️  按 Ctrl+C 可以停止应用
echo.

gradio5_env\python.exe app.py

echo.
echo �� 应用已关闭
pause
