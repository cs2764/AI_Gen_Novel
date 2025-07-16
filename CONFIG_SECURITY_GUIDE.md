# 配置文件安全指南

## 🔒 重要安全说明

本项目包含敏感的配置文件，这些文件对本地运行是必需的，但不应上传到GitHub。

## 📁 敏感文件列表

### 必需但不上传的文件
- `config.py` - 包含API密钥的Python配置文件
- `runtime_config.json` - 运行时配置文件
- `default_ideas.json` - 用户自定义的默认想法（如果存在）

### 为什么这些文件很重要？

#### 1. **本地运行必需**
- 程序启动时需要读取这些配置
- 包含AI提供商的API密钥和设置
- 存储用户的个性化配置

#### 2. **包含敏感信息**
- API密钥：访问AI服务的凭证
- 个人设置：用户的自定义配置
- 服务器地址：可能包含内网信息

## 🛡️ 安全措施

### 1. Git忽略配置
这些文件已在`.gitignore`中配置：
```gitignore
# 配置文件 - 包含API密钥，不应上传到GitHub
config.py
runtime_config.json
default_ideas.json
```

### 2. 模板文件
- `config_template.py` - 提供配置模板，可以安全上传
- 用户需要复制模板并填入自己的API密钥

### 3. 自动检查
- `pre_release_check.py` 会检查这些文件是否被正确忽略
- `quick_start.py` 会检查配置文件是否存在

## 📋 最佳实践

### 1. 首次设置
```bash
# 复制配置模板
cp config_template.py config.py

# 编辑配置文件，填入您的API密钥
# 注意：不要分享或上传包含真实API密钥的config.py
```

### 2. 团队协作
- 每个开发者维护自己的`config.py`
- 通过`config_template.py`共享配置结构
- 在文档中说明如何获取和配置API密钥

### 3. 部署环境
- 生产环境使用环境变量或密钥管理服务
- 不要在代码仓库中存储生产环境的密钥
- 使用CI/CD工具的密钥管理功能

## ⚠️ 安全警告

### 不要做的事情
- ❌ 不要将包含真实API密钥的配置文件上传到GitHub
- ❌ 不要在公开场所分享配置文件内容
- ❌ 不要将API密钥硬编码在源代码中
- ❌ 不要删除本地的配置文件（会导致程序无法运行）

### 应该做的事情
- ✅ 使用模板文件分享配置结构
- ✅ 在.gitignore中正确配置忽略规则
- ✅ 定期检查是否意外提交了敏感文件
- ✅ 使用环境变量或密钥管理服务

## 🔧 故障排除

### 1. 程序无法启动
如果程序提示配置文件不存在：
```bash
# 检查配置文件是否存在
ls -la config.py runtime_config.json

# 如果不存在，从模板创建
cp config_template.py config.py
```

### 2. Git意外跟踪配置文件
如果Git开始跟踪配置文件：
```bash
# 停止跟踪但保留文件
git rm --cached config.py runtime_config.json

# 确保.gitignore包含这些文件
echo "config.py" >> .gitignore
echo "runtime_config.json" >> .gitignore
```

### 3. 检查忽略状态
```bash
# 检查文件是否被忽略
git check-ignore config.py runtime_config.json

# 如果被正确忽略，会显示文件名
# 如果没有输出，说明文件没有被忽略
```

## 📞 获取帮助

如果遇到配置相关的问题：
1. 查看[安装指南](INSTALL.md)
2. 运行`python quick_start.py`进行自动检查
3. 查看[AI提供商配置指南](README_Provider_Config.md)
4. 在GitHub Issues中报告问题

---

**记住：安全第一！保护好您的API密钥，它们就像您的密码一样重要。** 🔐
