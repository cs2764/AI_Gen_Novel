@echo off
chcp 65001 >nul
title 修复Gradio版本问题

echo ====================================================
echo                修复Gradio版本问题
echo ====================================================
echo.

echo 🔧 正在卸载当前Gradio版本...
pip uninstall gradio -y

echo.
echo 🔧 正在安装Gradio 4.8.0 (稳定版本)...
pip install gradio==4.8.0

echo.
echo 🔍 验证Gradio安装...
pip show gradio

echo.
echo ✅ Gradio版本修复完成
echo 💡 现在可以重新运行 start.bat 启动程序
echo.
pause