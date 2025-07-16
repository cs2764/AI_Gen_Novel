@echo off
chcp 65001 >nul
title AI网络小说生成器

echo ====================================================
echo            AI网络小说生成器启动脚本
echo ====================================================
echo.

:: 设置项目根目录
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo 🔍 当前工作目录: %CD%
echo.

:: 检查是否有可用的Python环境

:: 设置虚拟环境路径（优先使用venv）
set "VENV_PATH=%PROJECT_DIR%venv_ai_novel"
set "ENV_PATH=%PROJECT_DIR%ai_novel_env"
set "SETUP_FLAG=%PROJECT_DIR%.setup_complete"

echo 🔍 检查项目虚拟环境...

:: 优先检查venv环境
if exist "%VENV_PATH%\Scripts\python.exe" (
    echo ✅ 找到Python venv环境
    echo 📁 环境路径: %VENV_PATH%
    set "USE_VENV=1"
    set "PYTHON_PATH=%VENV_PATH%\Scripts\python.exe"
    set "PIP_PATH=%VENV_PATH%\Scripts\pip.exe"
    echo 🔍 环境信息：
    "%PYTHON_PATH%" --version
) else if exist "%ENV_PATH%" (
    echo ✅ 找到conda环境
    echo 📁 环境路径: %ENV_PATH%
    set "USE_VENV=0"
    if exist "%ENV_PATH%\python.exe" (
        set "PYTHON_PATH=%ENV_PATH%\python.exe"
        set "PIP_PATH=%ENV_PATH%\Scripts\pip.exe"
        echo 🔍 环境信息：
        "%PYTHON_PATH%" --version
    ) else (
        echo ❌ 警告：虚拟环境存在但Python可执行文件缺失
        echo 💡 建议运行clean_env.bat清理后重新运行install.bat
        pause
        exit /b 1
    )
) else (
    echo ⚠️  未找到虚拟环境，检查全局Python...
    
    :: 检查全局Python
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo ❌ 未找到Python安装
        echo 💡 请先运行安装程序：
        echo.
        echo    推荐: install_global.bat (使用全局Python，无虚拟环境)
        echo    或者: install_venv.bat (使用Python venv)
        echo    备选: install_minimal.bat (使用conda)
        echo.
        pause
        exit /b 1
    )
    
    echo ✅ 找到全局Python，检查依赖包...
    python -c "import gradio" >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo ❌ 全局Python缺少必需包
        echo 💡 请运行: install_global.bat 安装依赖
        echo.
        pause
        exit /b 1
    )
    
    echo ✅ 全局Python环境可用
    echo 📁 使用全局Python
    set "USE_GLOBAL=1"
    set "PYTHON_PATH=python"
    set "PIP_PATH=python -m pip"
    echo 🔍 环境信息：
    python --version
)

echo.
if defined USE_GLOBAL (
    echo 🔄 使用全局Python环境...
    echo 🔧 Python路径: %PYTHON_PATH%
    
    :: 测试Python是否可以运行
    %PYTHON_PATH% --version >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ 全局Python无法正常运行
        pause
        exit /b 1
    )
    
    echo ✅ 全局Python环境准备就绪
) else if %USE_VENV%==1 (
    echo 🔄 激活Python venv环境...
    echo 🔧 使用Python venv环境
    echo 🔧 Python路径: %PYTHON_PATH%
    
    :: 测试Python是否可以运行
    "%PYTHON_PATH%" --version >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Python无法正常运行
        echo 💡 虚拟环境可能损坏，建议删除venv_ai_novel文件夹重新创建
        pause
        exit /b 1
    )
    
    echo ✅ venv环境准备就绪
) else (
    echo 🔄 激活conda环境...
    :: 检查conda是否安装
    where conda >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ 错误: conda环境需要conda命令，但未找到
        echo 💡 请安装Anaconda或Miniconda，或使用其他安装器
        pause
        exit /b 1
    )
    
    :: 初始化conda为批处理文件
    call conda init --all >nul 2>nul

    :: 激活环境
    echo 🔧 尝试激活环境: conda activate "%ENV_PATH%"
    call conda activate "%ENV_PATH%" 2>nul
    if %errorlevel% neq 0 (
        echo ⚠️  conda activate失败，使用备用激活方法...
        
        :: 备用激活方法：直接设置环境变量
        set "PATH=%ENV_PATH%;%ENV_PATH%\Scripts;%ENV_PATH%\Library\bin;%PATH%"
        set "CONDA_DEFAULT_ENV=%ENV_PATH%"
        set "CONDA_PREFIX=%ENV_PATH%"
        
        echo 🔄 使用备用方法激活环境...
        echo 🔧 Python路径: %ENV_PATH%\python.exe
        
        :: 测试Python是否可以运行
        "%PYTHON_PATH%" --version >nul 2>nul
        if %errorlevel% neq 0 (
            echo ❌ Python无法正常运行
            echo 💡 虚拟环境可能损坏，建议运行clean_env.bat重新创建
            pause
            exit /b 1
        )
        
        echo ✅ 备用方法激活成功
    ) else (
        echo ✅ conda环境激活成功
    )
)

echo.
echo 📋 检查Python依赖...

:: 检查requirements.txt文件
set "REQUIREMENTS_FILE=%PROJECT_DIR%requirements.txt"
if not exist "%REQUIREMENTS_FILE%" (
    echo ❌ 找不到requirements.txt文件
    echo 📁 预期位置: %REQUIREMENTS_FILE%
    pause
    exit /b 1
)

echo 📄 找到requirements.txt: %REQUIREMENTS_FILE%

echo 🔧 使用pip路径: %PIP_PATH%

:: 检查是否需要安装依赖
set "NEED_INSTALL=0"
if defined USE_GLOBAL (
    echo 🔍 检查全局Python依赖包...
    python -c "import gradio, openai, requests" >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  全局Python缺少依赖包
        echo 💡 建议运行: install_global.bat
        set "NEED_INSTALL=1"
    ) else (
        echo ✅ 全局Python依赖包完整
    )
) else (
    :: 虚拟环境依赖检查
    if not exist "%SETUP_FLAG%" (
        set "NEED_INSTALL=1"
    ) else (
        echo 🔍 检查关键依赖包...
        %PIP_PATH% show gradio >nul 2>nul
        if %errorlevel% neq 0 (
            set "NEED_INSTALL=1"
        )
    )
)

if %NEED_INSTALL%==1 (
    echo.
    echo 📦 正在安装依赖包...
    echo 🔧 执行命令: %PIP_PATH% install -r "%REQUIREMENTS_FILE%"
    echo.
    
    :: 升级pip以避免兼容性问题
    echo 🔄 更新pip...
    %PIP_PATH% install --upgrade pip
    
    :: 安装依赖
    %PIP_PATH% install -r "%REQUIREMENTS_FILE%"
    
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败，错误码: %errorlevel%
        echo 💡 请检查网络连接和requirements.txt文件
        echo 💡 也可以尝试手动运行: %PIP_PATH% install -r "%REQUIREMENTS_FILE%"
        pause
        exit /b 1
    )
    
    echo.
    echo 🔍 验证关键依赖安装...
    
    :: 检查关键依赖
    %PIP_PATH% show gradio >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ gradio 安装失败
        echo 💡 请检查网络连接和requirements.txt文件
        pause
        exit /b 1
    )
    
    %PIP_PATH% show openai >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ openai 安装失败
        echo 💡 请检查网络连接和requirements.txt文件
        pause
        exit /b 1
    )
    
    %PIP_PATH% show dashscope >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ dashscope 安装失败
        echo 💡 请检查网络连接和requirements.txt文件
        pause
        exit /b 1
    )
    
    :: 创建安装完成标志
    echo Installation completed on %date% %time% > "%SETUP_FLAG%"
    echo ✅ 依赖安装完成
) else (
    echo ✅ 关键依赖已安装，跳过安装步骤
)

echo.
echo 🚀 启动AI网络小说生成器...
echo 📍 访问地址: http://localhost:7860
echo 💡 按Ctrl+C可停止程序
echo.

echo 🔧 使用Python路径: %PYTHON_PATH%

if not exist "%PYTHON_PATH%" (
    echo ❌ 找不到Python可执行文件
    pause
    exit /b 1
)

:: 检查app.py文件
set "APP_FILE=%PROJECT_DIR%app.py"
if not exist "%APP_FILE%" (
    echo ❌ 找不到app.py文件
    echo 📁 预期位置: %APP_FILE%
    pause
    exit /b 1
)

echo 🔧 启动文件: %APP_FILE%
echo.
echo ⏳ 正在启动，请稍候...
echo 📍 程序启动后将自动打开浏览器访问: http://localhost:7860
echo 💡 如果浏览器未自动打开，请手动访问上述地址
echo.

:: 启动应用程序
%PYTHON_PATH% "%APP_FILE%"

:: 捕获启动结果
if %errorlevel% neq 0 (
    echo.
    echo ❌ 程序启动失败，错误码: %errorlevel%
    echo 💡 可能的原因：
    echo    - 端口7860被占用
    echo    - 依赖包版本冲突
    echo    - 配置文件错误
    echo.
    echo 🔧 建议解决方案：
    echo    1. 检查是否有其他程序占用7860端口
    echo    2. 运行clean_env.bat重新安装依赖
    echo    3. 检查config.py配置文件
) else (
    echo.
    echo ✅ 程序正常退出
)

echo.
echo 👋 感谢使用AI网络小说生成器
pause