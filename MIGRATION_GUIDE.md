# 🔄 AI网络小说生成器 - 版本迁移指南

## 📋 迁移概览

**目标版本**: v3.0.0 (Gradio 5.38.0 独立版)  
**支持迁移**: v2.x → v3.0.0  
**迁移时间**: 约10-15分钟  
**数据安全**: ✅ 用户数据完全保留  

## 🎯 版本对比

### v2.x vs v3.0.0 主要变更

| 项目 | v2.x (旧版本) | v3.0.0 (新版本) |
|------|---------------|-----------------|
| **界面框架** | Gradio 4.x | Gradio 5.38.0 |
| **默认端口** | 7860 | 7861 |
| **虚拟环境** | ai_novel_env | gradio5_env |
| **依赖文件** | requirements.txt | requirements_gradio5.txt |
| **配置文件** | config.py | config_template.py + config.py |
| **状态显示** | 基础状态 | 实时分阶段状态 |
| **用户确认** | 无 | 防误操作确认机制 |
| **错误处理** | 基础处理 | 智能错误恢复 |

## 🚀 快速迁移 (推荐)

### 步骤1: 数据备份

```bash
# 进入项目目录
cd AI_Gen_Novel

# 备份用户数据
mkdir migration_backup
cp -r output/ migration_backup/
cp -r autosave/ migration_backup/
cp -r metadata/ migration_backup/
cp config.py migration_backup/config_backup.py

# 记录当前配置
echo "备份完成: $(date)" > migration_backup/backup_info.txt
```

### 步骤2: 更新代码

```bash
# 获取最新代码
git fetch origin
git checkout main  # 或 dev_gradio5 分支
git pull origin main

# 检查版本
python version.py  # 应该显示 v3.0.0
```

### 步骤3: 环境迁移

```bash
# 停用旧环境 (如果正在使用)
deactivate

# 创建新环境
python -m venv gradio5_env

# 激活新环境
# Windows:
gradio5_env\Scripts\activate.bat
# Linux/Mac:
source gradio5_env/bin/activate

# 验证环境
which python  # 应该指向gradio5_env
```

### 步骤4: 依赖安装

```bash
# 安装Gradio 5.38.0依赖
pip install -r requirements_gradio5.txt

# 验证关键包
pip show gradio  # 应该显示 5.38.0
pip list | grep -E "(gradio|requests|anthropic)"
```

### 步骤5: 配置迁移

```bash
# 使用新配置模板
cp config_template.py config.py

# 手动迁移API密钥 (从备份文件)
# 编辑 config.py，填入您的API密钥
```

### 步骤6: 启动验证

```bash
# 启动新版本
python app.py

# 验证访问
# 浏览器访问: http://localhost:7861
# 检查数据加载是否正常
```

## 🔧 详细迁移步骤

### 1. 迁移前检查

#### 环境检查
```bash
# 检查Python版本 (需要3.10+)
python --version

# 检查当前项目状态
git status
git branch

# 检查现有数据
ls -la output/
ls -la autosave/
```

#### 数据清单
- ✅ **小说文件**: output/*.txt, output/*.epub
- ✅ **元数据**: output/*_metadata.json
- ✅ **自动保存**: autosave/*.json
- ✅ **配置文件**: config.py
- ✅ **用户设置**: default_ideas.json (如果存在)

### 2. 配置文件迁移

#### 旧版本配置格式 (v2.x)
```python
# 旧版本 config.py 示例
OPENROUTER_API_KEY = "your-key"
CLAUDE_API_KEY = "your-key"
# ... 其他配置
```

#### 新版本配置格式 (v3.0.0)
```python
# 新版本 config.py (基于 config_template.py)
# OpenRouter API配置
OPENROUTER_API_KEY = "your_openrouter_api_key_here"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Claude API配置 (Anthropic)
CLAUDE_API_KEY = "your_claude_api_key_here"
CLAUDE_BASE_URL = "https://api.anthropic.com"

# 新增提供商
FIREWORKS_API_KEY = "your_fireworks_api_key_here"
GROK_API_KEY = "your_grok_api_key_here"
LAMBDA_API_KEY = "your_lambda_api_key_here"
```

#### 配置迁移脚本
```python
# 自动配置迁移脚本 (可选)
import re

def migrate_config():
    # 读取旧配置
    with open('migration_backup/config_backup.py', 'r') as f:
        old_config = f.read()
    
    # 读取新模板
    with open('config_template.py', 'r') as f:
        new_template = f.read()
    
    # 提取API密钥
    api_keys = {}
    for line in old_config.split('\n'):
        if '_API_KEY' in line and '=' in line:
            key, value = line.split('=', 1)
            api_keys[key.strip()] = value.strip()
    
    # 应用到新模板
    new_config = new_template
    for key, value in api_keys.items():
        if key in new_config:
            new_config = re.sub(
                f'{key} = ".*"',
                f'{key} = {value}',
                new_config
            )
    
    # 保存新配置
    with open('config.py', 'w') as f:
        f.write(new_config)
    
    print("配置迁移完成!")

# 运行迁移
# migrate_config()
```

### 3. 数据验证

#### 数据完整性检查
```bash
# 检查小说文件
find output/ -name "*.txt" -exec wc -l {} \;
find output/ -name "*.json" | wc -l

# 检查自动保存
ls -la autosave/
cat autosave/title.json
cat autosave/outline.json

# 检查元数据
find metadata/ -name "*.json" | head -5
```

#### 功能验证清单
- [ ] 界面正常加载 (http://localhost:7861)
- [ ] API连接测试通过
- [ ] 历史数据正确显示
- [ ] 生成功能正常工作
- [ ] 自动保存功能正常
- [ ] 导出功能正常

## 🛠️ 故障排除

### 常见问题及解决方案

#### 问题1: 端口冲突
```
错误: Address already in use: 7861
```
**解决方案**:
```bash
# 检查端口占用
netstat -ano | findstr :7861  # Windows
lsof -i :7861                 # Linux/Mac

# 关闭旧版本或使用不同端口
python app.py --port 7862
```

#### 问题2: 依赖冲突
```
错误: gradio 4.x.x conflicts with gradio 5.38.0
```
**解决方案**:
```bash
# 完全清理环境
pip uninstall gradio -y
pip cache purge
pip install -r requirements_gradio5.txt
```

#### 问题3: 配置文件错误
```
错误: config.py not found or invalid
```
**解决方案**:
```bash
# 重新创建配置
rm config.py
cp config_template.py config.py
# 重新填入API密钥
```

#### 问题4: 数据加载失败
```
错误: Failed to load autosave data
```
**解决方案**:
```bash
# 检查数据格式
python -c "import json; print(json.load(open('autosave/title.json')))"

# 修复JSON格式 (如果需要)
python json_auto_repair.py
```

#### 问题5: 虚拟环境问题
```
错误: No module named 'gradio'
```
**解决方案**:
```bash
# 确认环境激活
which python  # 应该指向gradio5_env

# 重新激活环境
deactivate
source gradio5_env/bin/activate  # Linux/Mac
gradio5_env\Scripts\activate.bat  # Windows

# 重新安装依赖
pip install -r requirements_gradio5.txt
```

## 📊 迁移验证清单

### 迁移完成检查

#### ✅ 环境验证
- [ ] Python版本 3.10+
- [ ] gradio5_env 虚拟环境激活
- [ ] Gradio 5.38.0 安装成功
- [ ] 所有依赖包安装完成

#### ✅ 配置验证
- [ ] config.py 文件存在
- [ ] API密钥正确配置
- [ ] 配置格式符合v3.0.0要求
- [ ] 测试连接成功

#### ✅ 数据验证
- [ ] output/ 目录数据完整
- [ ] autosave/ 目录数据完整
- [ ] metadata/ 目录数据完整
- [ ] 历史小说正确显示

#### ✅ 功能验证
- [ ] 界面正常访问 (http://localhost:7861)
- [ ] 实时状态显示正常
- [ ] 用户确认机制工作
- [ ] 生成功能正常
- [ ] 自动保存正常
- [ ] 导出功能正常

## 🔄 回滚方案

如果迁移遇到问题，可以回滚到旧版本：

### 快速回滚
```bash
# 1. 停止新版本
# Ctrl+C 停止应用

# 2. 切换到旧版本分支
git checkout v2.4.4  # 或您之前使用的版本

# 3. 激活旧环境
deactivate
source ai_novel_env/bin/activate  # 如果存在

# 4. 恢复数据 (如果需要)
cp -r migration_backup/output/* output/
cp -r migration_backup/autosave/* autosave/
cp migration_backup/config_backup.py config.py

# 5. 启动旧版本
python app.py  # 访问 http://localhost:7860
```

## 📞 迁移支持

### 获取帮助
- **文档**: README.md, INSTALL.md
- **问题反馈**: GitHub Issues
- **迁移脚本**: 可提供自动迁移脚本

### 迁移最佳实践
1. **充分备份**: 迁移前完整备份所有数据
2. **分步验证**: 每个步骤完成后进行验证
3. **保留旧环境**: 迁移成功前不要删除旧环境
4. **测试功能**: 迁移后全面测试所有功能

---

**迁移指南版本**: v3.0.0  
**最后更新**: 2025-01-24  
**适用范围**: v2.x → v3.0.0  
**预计时间**: 10-15分钟
