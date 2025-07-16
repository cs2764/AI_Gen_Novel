@echo off
chcp 65001 >nul
title AI网络小说生成器 - 环境清理工具

echo ====================================================
echo        AI网络小说生成器 - 环境清理工具
echo ====================================================
echo.

:: 设置项目根目录
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo 🔍 当前工作目录: %CD%
echo.

:: 设置路径
set "ENV_PATH=%PROJECT_DIR%ai_novel_env"
set "VENV_PATH=%PROJECT_DIR%venv_ai_novel"
set "SETUP_FLAG=%PROJECT_DIR%.setup_complete"

echo ⚠️  这将删除以下内容:
if exist "%VENV_PATH%" echo 📁 Python venv环境: %VENV_PATH%
if exist "%ENV_PATH%" echo 📁 Conda环境: %ENV_PATH%
echo 📄 安装标志: %SETUP_FLAG%
echo.
echo 💡 删除后下次运行start.bat将重新创建环境并安装依赖
echo.

set /p confirm="确定要继续吗? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo 操作已取消
    pause
    exit /b 0
)

echo.
echo 🗑️  正在清理环境...

:: 删除Python venv环境
if exist "%VENV_PATH%" (
    echo 🔄 删除Python venv环境: %VENV_PATH%
    rmdir /s /q "%VENV_PATH%"
    if exist "%VENV_PATH%" (
        echo ❌ 删除venv环境失败，可能有文件正在使用
        echo 💡 请关闭所有相关程序后重试
        pause
        exit /b 1
    ) else (
        echo ✅ venv环境已删除
    )
) else (
    echo ℹ️  venv环境不存在，跳过
)

:: 删除conda虚拟环境
if exist "%ENV_PATH%" (
    echo 🔄 删除conda环境: %ENV_PATH%
    rmdir /s /q "%ENV_PATH%"
    if exist "%ENV_PATH%" (
        echo ❌ 删除conda环境失败，可能有文件正在使用
        echo 💡 请关闭所有相关程序后重试
        pause
        exit /b 1
    ) else (
        echo ✅ conda环境已删除
    )
) else (
    echo ℹ️  conda环境不存在，跳过
)

:: 删除安装标志
if exist "%SETUP_FLAG%" (
    echo 🔄 删除安装标志: %SETUP_FLAG%
    del "%SETUP_FLAG%"
    echo ✅ 安装标志已删除
) else (
    echo ℹ️  安装标志不存在，跳过
)

echo.
echo ✅ 环境清理完成！
echo 💡 下次运行start.bat时将重新初始化环境
echo.
pause 