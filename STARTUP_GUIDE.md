# 🚀 AI网络小说生成器 - 启动指南

**版本**: v5.3.0  
**更新日期**: 2026-06-25  
**适用系统**: Windows, macOS, Linux

## 📋 快速启动

### 🎯 一键启动 (Windows)
```bash
# 直接运行启动脚本
start.bat
```

### 🔧 手动启动流程

#### 1. 激活虚拟环境

**Windows:**
```bash
# 激活虚拟环境
gradio5_env\Scripts\activate.bat

# 或者使用PowerShell
gradio5_env\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
# 激活虚拟环境
source gradio5_env/bin/activate
```

#### 2. 验证环境
```bash
# 检查Python版本
python --version

# 检查Gradio版本
python -c "import gradio; print(f'Gradio版本: {gradio.__version__}')"

# 检查主要依赖
python -c "import openai, anthropic, google.generativeai; print('所有AI提供商库已安装')"
```

#### 3. 启动Web界面
```bash
# 启动应用
python app.py
```

## 🛠️ 环境管理

### 虚拟环境创建 (如需重建)

**创建新的虚拟环境:**
```bash
# 删除旧环境 (如果存在)
rm -rf gradio5_env  # Linux/macOS
# 或
Remove-Item -Recurse -Force gradio5_env  # Windows PowerShell

# 创建新环境
python -m venv gradio5_env

# 激活环境
gradio5_env\Scripts\activate.bat  # Windows
# 或
source gradio5_env/bin/activate  # Linux/macOS
```

**安装依赖:**
```bash
# 升级pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements_gradio5.txt

# 验证安装
pip list | grep gradio
```

### 依赖管理

**查看已安装包:**
```bash
pip list
```

**更新特定包:**
```bash
pip install --upgrade gradio
pip install --upgrade openai
```

**导出当前环境:**
```bash
pip freeze > requirements_current.txt
```

## ⚙️ 配置设置

### 1. API密钥配置

**首次使用:**
```bash
# 复制配置模板
cp config_template.py config.py

# 编辑配置文件
notepad config.py  # Windows
# 或
nano config.py     # Linux/macOS
```

**配置示例:**
```python
# config.py
OPENAI_API_KEY = "your-openai-key-here"
ANTHROPIC_API_KEY = "your-claude-key-here"
GOOGLE_API_KEY = "your-gemini-key-here"
# ... 其他API密钥
```

### 2. 验证配置
```bash
# 运行配置检查
python -c "import config; print('配置文件加载成功')"
```

## 🌐 Web界面访问

### 启动后访问
- **本地访问**: http://127.0.0.1:7860
- **局域网访问**: http://[你的IP]:7860
- **自动打开**: 启动后浏览器会自动打开

### 界面功能
- 📝 **小说创作**: 完整的小说生成流程
- 🤖 **AI选择**: 10个主流AI提供商
- 💾 **自动保存**: 创作内容自动保存
- 📊 **实时状态**: 生成进度实时显示

## 🔧 故障排除

### 常见问题

**1. 虚拟环境激活失败**
```bash
# Windows执行策略问题
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后重新激活
gradio5_env\Scripts\Activate.ps1
```

**2. 依赖安装失败**
```bash
# 清理pip缓存
pip cache purge

# 使用国内镜像
pip install -r requirements_gradio5.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

**3. 端口占用**
```bash
# 检查端口占用
netstat -ano | findstr :7860  # Windows
lsof -i :7860                 # Linux/macOS

# 使用其他端口启动
python app.py --server-port 7861
```

**4. API密钥错误**
```bash
# 检查配置文件
python -c "import config; print(dir(config))"

# 测试API连接
python -c "from uniai.openrouterAI import OpenRouterAI; print('API测试通过')"
```

### 日志查看
```bash
# 查看应用日志
tail -f app.log  # Linux/macOS
Get-Content app.log -Wait  # Windows PowerShell
```

## 📊 性能优化

### 系统要求
- **Python**: 3.10+ (推荐 3.10.11)
- **内存**: 4GB+ 可用内存
- **存储**: 2GB+ 可用空间
- **网络**: 稳定的网络连接

### 优化建议
```bash
# 设置环境变量优化
export PYTHONUNBUFFERED=1
export GRADIO_SERVER_NAME="0.0.0.0"
export GRADIO_SERVER_PORT=7860

# Windows
set PYTHONUNBUFFERED=1
set GRADIO_SERVER_NAME=0.0.0.0
set GRADIO_SERVER_PORT=7860
```

## 🔄 更新和维护

### 项目更新
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements_gradio5.txt --upgrade

# 重启应用
python app.py
```

### 数据备份
```bash
# 备份用户数据
cp -r output/ backup/output_$(date +%Y%m%d)/
cp -r autosave/ backup/autosave_$(date +%Y%m%d)/
```

## 🆘 获取帮助

### 技术支持
- 📖 **文档**: 查看项目README.md
- 🐛 **问题反馈**: GitHub Issues
- 💬 **讨论交流**: GitHub Discussions

### 开发者工具
```bash
# 开发模式启动
python app.py --debug

# 代码格式检查
python -m ruff check .

# 类型检查
python -m mypy app.py
```

---

**🎉 启动成功后，您就可以开始AI小说创作之旅了！**

记住：
- ✅ 虚拟环境必须激活
- ✅ API密钥必须配置
- ✅ 网络连接必须稳定
- ✅ 浏览器支持现代Web标准
