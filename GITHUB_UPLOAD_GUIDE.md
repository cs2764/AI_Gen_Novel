# 🚀 GitHub上传安全指南

## 📋 项目准备概述

本指南确保AI网络小说生成器项目能够安全地上传到GitHub，同时保护用户隐私和API密钥安全。

## 🔒 安全措施

### 1. 敏感文件保护

项目已配置完善的 `.gitignore` 文件，确保以下敏感文件不会被上传：

#### 🔑 配置文件（绝对不能上传）
- `config.py` - 包含所有API密钥的主配置文件
- `config.json` - JSON格式配置文件
- `runtime_config.json` - 运行时动态配置
- `default_ideas.json` - 用户自定义默认想法配置
- `*.key`, `*.secret` - 各种密钥和敏感凭证文件
- `.env*` - 环境变量文件

#### 📁 用户数据目录（包含个人创作）
- `output/` - 用户生成的小说文件和元数据
- `autosave/` - 自动保存的用户数据（大纲、故事线、设置等）
- `metadata/` - 元数据目录
- `ai_novel_env/` - Python虚拟环境

#### 📄 用户生成的数据文件
- `ai_novel_data_*.json` - 导出的用户数据
- `export_*.json`, `*_export.json` - 各种导出文件
- `*_backup.json`, `*_user.json`, `*_personal.json` - 备份和个人数据文件
- `novel_record.md` - 小说记录文件

### 2. 安全检查脚本

项目包含 `github_upload_ready.py` 脚本，提供以下安全检查：

- ✅ 检查 `.gitignore` 文件存在性和覆盖范围
- ✅ 扫描源代码中的敏感内容（API密钥等）
- ✅ 验证敏感文件是否被Git正确忽略
- ✅ 检查用户数据目录是否被保护
- ✅ 分析Git状态，防止意外提交敏感文件

## 🛡️ 使用安全检查脚本

### 运行安全检查

```bash
# 运行GitHub上传准备检查
python github_upload_ready.py
```

### 检查结果示例

```
🛡️  开始GitHub上传安全检查...
==================================================
🔍 检查 .gitignore 文件...
✅ .gitignore 文件存在

🔍 检查 .gitignore 覆盖范围...
✅ .gitignore 覆盖范围充分

🔍 扫描敏感内容...
✅ 未发现敏感内容

🔍 检查敏感文件是否被忽略...
✅ 所有敏感文件都被正确忽略

🔍 检查用户数据目录...
✅ 所有用户数据目录都被正确忽略

🔍 检查Git状态...
✅ Git状态安全

==================================================
🎉 所有安全检查通过！
```

## 📤 安全上传流程

### 1. 预检查

```bash
# 运行安全检查
python github_upload_ready.py

# 手动确认敏感文件被忽略
git check-ignore config.py output/ autosave/

# 查看当前Git状态
git status
```

### 2. 暂存和提交

```bash
# 添加所有安全文件
git add .

# 查看将要提交的文件（确保没有敏感文件）
git diff --cached --name-only

# 创建提交
git commit -m "feat: AI网络小说生成器初始版本

- 完整的AI小说生成功能
- 支持8个主流AI提供商
- 现代化Web界面设计
- 本地数据管理系统
- 完善的安全措施和文档"
```

### 3. 推送到GitHub

```bash
# 设置远程仓库（如果是新仓库）
git remote add origin https://github.com/yourusername/AI_Gen_Novel.git

# 设置主分枝
git branch -M main

# 推送代码
git push -u origin main
```

### 4. 验证上传结果

上传完成后，请在GitHub仓库中验证：

- ❌ 确认没有 `config.py` 文件
- ❌ 确认没有 `output/` 目录
- ❌ 确认没有 `autosave/` 目录
- ❌ 确认没有任何 `*.json` 配置文件（除了package.json等标准文件）
- ✅ 确认 `.gitignore` 文件存在且内容完整
- ✅ 确认 `config_template.py` 文件存在
- ✅ 确认所有源代码和文档文件正常

## 🚨 重要安全提醒

### 🔥 绝对不要做的事情

1. **不要上传真实的API密钥**
   - `config.py` 已被加入 `.gitignore`
   - 如果意外上传，立即删除仓库并重新创建

2. **不要上传用户数据**
   - `output/` 和 `autosave/` 包含用户创作内容
   - 这些目录已被自动忽略

3. **不要在代码中硬编码密钥**
   - 使用配置文件或环境变量
   - 所有密钥都应该通过安全的方式管理

4. **不要在截图或文档中暴露敏感信息**
   - 分享截图时遮挡API密钥
   - 文档中使用占位符而非真实密钥

### ✅ 安全的分享方式

1. **分享配置模板**
   - 只分享 `config_template.py`
   - 包含占位符和使用说明

2. **提供详细文档**
   - 配置指南和安装说明
   - 不包含真实密钥的示例

3. **使用环境变量**
   - 在文档中推荐使用环境变量
   - 提供设置环境变量的指南

## 🔧 故障排除

### 如果安全检查失败

1. **检查 `.gitignore` 文件**
   ```bash
   # 确认文件存在
   ls -la .gitignore
   
   # 查看内容
   cat .gitignore
   ```

2. **手动检查敏感文件**
   ```bash
   # 检查config.py是否被忽略
   git check-ignore config.py
   
   # 检查output目录是否被忽略
   git check-ignore output/
   ```

3. **清理已跟踪的敏感文件**
   ```bash
   # 如果敏感文件已被Git跟踪，需要取消跟踪
   git rm --cached config.py
   git rm --cached -r output/
   
   # 然后提交更改
   git commit -m "remove sensitive files from tracking"
   ```

### 如果意外上传了敏感文件

1. **立即删除敏感文件**
   ```bash
   git rm config.py
   git commit -m "remove sensitive config file"
   git push
   ```

2. **更换API密钥**
   - 在对应平台撤销泄露的API密钥
   - 生成新的API密钥
   - 更新本地配置

3. **考虑重新创建仓库**
   - 如果泄露严重，删除GitHub仓库
   - 清理本地Git历史
   - 重新创建干净的仓库

## 📚 相关文档

- [安装指南](INSTALL.md) - 详细的安装和配置说明
- [配置安全指南](CONFIG_SECURITY_GUIDE.md) - API密钥安全管理
- [提供商配置指南](README_Provider_Config.md) - 各AI提供商配置方法
- [本地数据管理](LOCAL_DATA_MANAGEMENT.md) - 用户数据保存和管理
- [📋 文件管理通用准则](GITHUB_FILE_MANAGEMENT_GUIDE.md) - **适用于所有项目的通用文件管理指南**

## 💡 最佳实践

### 项目维护

1. **定期运行安全检查**
   ```bash
   # 定期检查项目安全性
   python github_upload_ready.py
   ```

2. **更新 `.gitignore`**
   - 添加新的敏感文件类型时及时更新
   - 关注用户反馈中提到的隐私文件

3. **代码审查**
   - 在接受Pull Request前检查敏感信息
   - 使用自动化工具扫描API密钥

### 协作开发

1. **团队安全规范**
   - 教育团队成员不要提交敏感文件
   - 建立代码审查流程

2. **环境隔离**
   - 开发、测试、生产环境使用不同的API密钥
   - 通过环境变量管理配置

3. **权限管理**
   - 限制仓库访问权限
   - 定期审查协作者列表

---

通过遵循本指南，您可以安全地将AI网络小说生成器项目分享到GitHub，既保护了用户隐私，又确保了API密钥的安全。记住：**安全第一，分享第二！**🔒✨ 