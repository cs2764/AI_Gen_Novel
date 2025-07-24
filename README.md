# 🤖 AI 网络小说生成器 v2.2.0

> 🎨 基于多种先进AI模型的智能小说创作工具，支持从想法到完整小说的一键生成

## 🔒 重要安全提醒

**⚠️ 在使用和分享本项目前，请务必注意：**

- 🚨 **配置文件包含API密钥**：`config.py` 文件包含您的AI提供商API密钥，绝对不能上传到公开仓库
- 🛡️ **用户数据保护**：`output/` 和 `autosave/` 目录包含您的创作内容，应保持私有
- ✅ **安全检查**：项目内置 `github_upload_ready.py` 脚本，上传前请运行安全检查
- 📖 **详细指南**：参见 [GitHub上传安全指南](GITHUB_UPLOAD_GUIDE.md) 了解完整的安全措施

```bash
# 运行安全检查
python github_upload_ready.py
```

---

## ✨ 核心特性

### 🎯 一键生成流程
- **智能大纲**：基于用户想法自动生成完整小说结构
- **角色塑造**：自动创建丰富的人物设定和关系网络  
- **章节拓展**：将简单大纲扩展为详细的章节梗概
- **故事线生成**：为每章生成详细剧情，确保情节连贯
- **自动生成**：支持连续生成多章节，可随时暂停继续

### 🤖 多AI提供商支持
支持8个主流AI提供商，满足不同需求：

| 提供商 | 特点 | 推荐场景 |
|--------|------|----------|
| **🚀 DeepSeek** | 性价比高，中文优化 | 日常创作 |
| **🌟 OpenRouter** | 多模型聚合，选择丰富 | 高质量创作 |
| **🧠 Claude** | 长文本处理强 | 复杂情节 |
| **💎 Gemini** | Google出品，稳定可靠 | 通用创作 |
| **🏠 LM Studio** | 本地部署，隐私保护 | 离线创作 |
| **🇨🇳 智谱AI** | 国产模型，中文理解佳 | 中文小说 |
| **☁️ 阿里云** | 长文本模型，上下文大 | 长篇创作 |
| **⚡ Lambda** | 成本低，多模型选择 | 经济型创作 |

### 🎨 现代化用户界面
- **直观操作**：步骤清晰的创作流程
- **实时反馈**：生成过程可视化展示
- **灵活配置**：可调节创作参数和AI温度
- **响应式设计**：适配各种屏幕尺寸

### 💾 智能数据管理
- **本地存储**：数据安全保存在本地文件
- **自动保存**：创作过程自动备份，防止意外丢失
- **一键导出**：支持TXT、EPUB等多种格式
- **数据同步**：界面与后端实时同步

## 🚀 快速开始

### 📋 系统要求
- Python 3.8+
- 4GB+ 可用内存
- 稳定的网络连接

### ⚡ 一键安装

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/AI_Gen_Novel.git
cd AI_Gen_Novel

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python app.py
```

### 🔧 配置API密钥

启动后访问 `http://localhost:7860`，在配置面板中：

1. 选择AI提供商
2. 输入API密钥
3. 测试连接
4. 保存配置

## 📖 使用指南

### 1️⃣ 基础创作流程

```
💡 输入创作想法 → 🎯 生成智能大纲 → 👥 创建角色设定 
    ↓
📖 扩展详细大纲 → 📝 生成故事线 → 🚀 自动生成小说
```

### 2️⃣ 高级功能

- **🎛️ 参数调节**：调整AI创作温度，控制随机性
- **📊 进度跟踪**：实时查看生成进度和章节统计
- **🔄 增量生成**：可从任意章节继续生成
- **💾 数据管理**：完整的保存、加载、导出功能

### 3️⃣ 创作技巧

- **想法描述**：越详细的想法，生成效果越好
- **参数设置**：高温度增加创意，低温度提高一致性
- **章节控制**：合理设置目标章节数，避免过长或过短
- **及时保存**：重要创作请及时手动保存备份

## 🔧 高级配置

### 📁 文件结构
```
AI_Gen_Novel/
├── app.py                 # 主应用程序
├── config_template.py     # 配置模板
├── AIGN.py               # 核心生成逻辑
├── auto_save_manager.py  # 自动保存管理
├── local_data_manager.py # 本地数据管理
├── output/               # 生成的小说文件（不上传）
├── autosave/            # 自动保存数据（不上传）
└── uniai/               # AI提供商适配器
```

### ⚙️ 配置文件说明

**config_template.py** - 配置模板（安全分享）
**config.py** - 实际配置（包含密钥，不要分享）

### 🌡️ 温度参数调节

不同创作阶段的推荐温度设置：

```python
TEMPERATURE_SETTINGS = {
    "outline_writer": 0.98,    # 大纲：高创意
    "beginning_writer": 0.80,  # 开头：中等创意  
    "novel_writer": 0.81,      # 正文：中等创意
    "embellisher": 0.92,       # 润色：高创意
    "memory_maker": 0.66       # 记忆：低创意，高一致性
}
```

## 🆕 版本更新

### v2.2.0 (2025-07-23)
- ✨ **GitHub上传安全**：完善的安全检查和.gitignore配置
- 🛡️ **隐私保护**：确保用户数据和API密钥不会意外泄露
- 📚 **文档完善**：详细的安全指南和最佳实践
- 🔧 **安全脚本**：内置github_upload_ready.py安全检查工具

### v2.1.0
- 🔄 **实时同步**：修复目标章节数实时读取问题
- 💾 **数据管理**：完善的本地数据保存和加载
- 🎨 **界面优化**：改进用户体验和状态显示

[查看完整更新日志](CHANGELOG.md)

## 📚 文档资源

- 📖 [安装指南](INSTALL.md) - 详细安装步骤
- 🔒 [安全指南](GITHUB_UPLOAD_GUIDE.md) - GitHub上传安全措施
- 🗂️ [文件管理通用准则](GITHUB_FILE_MANAGEMENT_GUIDE.md) - 适用于所有项目的文件管理最佳实践
- 🔧 [配置指南](README_Provider_Config.md) - AI提供商配置
- 💾 [数据管理](LOCAL_DATA_MANAGEMENT.md) - 本地数据管理
- 🏗️ [架构文档](ARCHITECTURE.md) - 系统架构设计

## ❓ 常见问题

<details>
<summary><b>Q: 如何获取API密钥？</b></summary>

不同提供商的获取方式：
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)
- **OpenRouter**: [openrouter.ai](https://openrouter.ai/)
- **Claude**: [console.anthropic.com](https://console.anthropic.com/)
- **更多**: 参见[配置指南](README_Provider_Config.md)
</details>

<details>
<summary><b>Q: 生成的内容质量如何提升？</b></summary>

1. **详细描述想法**：提供更多背景信息
2. **调整温度参数**：平衡创意性和一致性
3. **选择合适模型**：不同模型各有特长
4. **分步骤优化**：逐步完善大纲和设定
</details>

<details>
<summary><b>Q: 数据安全如何保障？</b></summary>

- 所有数据保存在本地
- API密钥不会上传到云端
- 支持数据导出和备份
- 严格的.gitignore保护隐私
</details>

## 🤝 贡献指南

欢迎参与项目改进！

### 🔧 开发准备
```bash
# 1. fork项目并克隆
git clone https://github.com/yourusername/AI_Gen_Novel.git

# 2. 创建虚拟环境
python -m venv ai_novel_env
source ai_novel_env/bin/activate  # Linux/Mac
# 或
ai_novel_env\Scripts\activate     # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
```

### 📝 提交规范
- `feat:` 新功能
- `fix:` 错误修复  
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构代码
- `test:` 测试相关

### 🛡️ 安全提醒
- 不要提交包含API密钥的文件
- 运行 `python github_upload_ready.py` 检查安全性
- 遵循[安全指南](GITHUB_UPLOAD_GUIDE.md)

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 💝 支持项目

如果这个项目对您有帮助，请：

- ⭐ 给项目点个星标
- 🐛 报告问题和建议  
- 🤝 参与代码贡献
- 📢 分享给朋友们

## 📞 联系方式

- 💬 **讨论交流**：[GitHub Discussions](https://github.com/yourusername/AI_Gen_Novel/discussions)
- 🐛 **问题反馈**：[GitHub Issues](https://github.com/yourusername/AI_Gen_Novel/issues)
- 📧 **邮件联系**：your-email@example.com

---

<div align="center">

**🌟 让AI成为您创作路上的最佳伙伴！🌟**

Made with ❤️ by AI Novel Generator Team

</div>