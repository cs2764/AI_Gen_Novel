@echo off
chcp 65001 >nul
title 修复依赖兼容性问题

echo ====================================================
echo              修复依赖兼容性问题
echo ====================================================
echo.

echo 🔧 正在完全卸载problematic packages...
pip uninstall gradio pydantic fastapi uvicorn starlette zhipuai -y

echo.
echo 🔧 正在安装兼容版本...
pip install gradio==3.50.2
pip install pydantic==1.10.12
pip install fastapi==0.104.1
pip install uvicorn==0.24.0

echo.
echo 🔍 验证安装...
pip show gradio pydantic fastapi uvicorn

echo.
echo ✅ 依赖修复完成
echo 💡 现在可以重新运行 start.bat 启动程序
echo.
pause