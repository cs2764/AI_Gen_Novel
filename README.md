# AI 网络小说生成器 - 增强版

## 项目简介

这是一个基于 [cjyyx/AI_Gen_Novel](https://github.com/cjyyx/AI_Gen_Novel) 的二次开发项目，旨在探索和优化 AI 在网络小说创作中的应用。本项目完全由 Claude Code 生成和开发，实现了多项新功能和改进。

> **声明**: 本项目是对原项目的二次开发和增强，所有代码都是由 Claude Code 人工智能助手生成。我们感谢原作者对 AI 写作技术的探索和贡献。

### 核心理念

网络小说的创作可以套用**写作的认知过程模型**，该模型将写作视为一个目标导向的思考过程，包括非线性的认知活动：计划、转换和审阅。

LLM 在转换和审阅上表现较好，而在计划阶段存在缺陷。本项目通过以下方式解决：

- 利用 LLM 的能力压缩长文本为几句话组成的记忆
- 优化 Prompt，多智能体协作，激发 LLM 的能力，提升其原创性
- 借鉴 **RecurrentGPT** 的核心思想，基于语言的循环计算，通过迭代的方式创作任意长度的文本
- 结合网络小说创作的先验知识，对创作流程进行优化

## 新增功能 🚀

### 1. 统一的配置管理系统
- **动态配置管理**: 支持运行时配置更新
- **Web 配置界面**: 可视化配置管理
- **多提供商支持**: 统一管理多个 AI 服务提供商

### 2. 系统提示词优化
- **提示词合并**: 将系统提示词直接合并到 API 调用中
- **一致性保证**: 确保所有 AI 提供商使用统一的提示词处理机制
- **简化架构**: 移除复杂的包装器，代码更简洁

### 3. 增强的 AI 提供商支持
- **DeepSeek**: 高性能中文模型
- **OpenRouter**: 多模型聚合平台
- **Claude**: Anthropic 的 AI 助手
- **Gemini**: Google 的多模态 AI
- **LM Studio**: 本地模型支持
- **智谱 AI**: 国产大模型
- **阿里云**: 通义千问系列

### 4. 自动化生成功能
- **批量生成**: 支持自动生成指定章节数的小说
- **智能结尾**: 自动检测并生成合适的结尾
- **进度跟踪**: 实时显示生成进度和状态
- **文件管理**: 自动保存和管理生成的小说文件

### 5. 改进的用户界面
- **现代化设计**: 基于 Gradio 的响应式界面
- **实时预览**: 实时显示生成过程和结果
- **配置验证**: 自动验证 API 配置的有效性
- **错误处理**: 优雅的错误处理和用户提示

## 技术特色

### 多智能体协作
- **大纲作家**: 专门生成故事大纲
- **开头作家**: 创作引人入胜的开头
- **正文作家**: 持续推进故事情节
- **润色师**: 优化文本质量
- **记忆管理器**: 维护故事连贯性
- **标题生成器**: 创作吸引人的标题
- **结尾作家**: 专门处理故事结尾

### 智能记忆管理
- **上下文压缩**: 将长文本压缩为关键记忆点
- **动态更新**: 根据故事发展自动更新记忆
- **连贯性保证**: 确保故事前后逻辑一致

### 流式生成
- **实时反馈**: 支持流式输出，实时查看生成过程
- **进度显示**: 显示生成进度和预计完成时间
- **中断恢复**: 支持暂停和恢复生成过程

## 快速开始

📋 **完整安装指南**: [查看 INSTALL.md](INSTALL.md)

### 1. 环境配置

```bash
# 克隆项目
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API 密钥

⚙️ **详细配置指南**: [查看 AI 提供商配置指南](README_Provider_Config.md)

首次运行时，程序会自动创建配置文件。您需要：

1. 启动程序: `python app.py`
2. 在 Web 界面中配置您的 API 密钥
3. 选择要使用的 AI 提供商
4. 测试连接并保存配置

### 3. 开始创作

1. 在"想法"框中输入您的小说创意
2. 点击"生成大纲"
3. 根据需要调整大纲和设置
4. 点击"生成开头"开始创作
5. 使用"自动生成"功能批量生成多个章节

🎯 **了解更多功能**: [查看功能详情](FEATURES.md)

## 文档导航 📚

完整的项目文档和开发指南：

- **[📋 安装配置指南](INSTALL.md)** - 详细的安装和配置说明
- **[⚙️ AI 提供商配置指南](README_Provider_Config.md)** - 各种 AI 提供商的配置方法
- **[🏗️ 架构设计文档](ARCHITECTURE.md)** - 系统架构和技术设计
- **[🔧 开发者文档](DEVELOPER.md)** - 项目结构和开发指南
- **[📖 API 接口文档](API.md)** - 详细的 API 接口说明
- **[🤝 贡献指南](CONTRIBUTING.md)** - 如何参与项目开发
- **[📝 更新日志](CHANGELOG.md)** - 版本历史和变更记录
- **[🎯 功能详情](FEATURES.md)** - 完整的功能列表

## 支持的 AI 提供商

| 提供商 | 模型示例 | 特点 | 配置指南 |
|--------|----------|------|----------|
| DeepSeek | deepseek-chat | 中文优化，成本低 | [查看配置](README_Provider_Config.md#deepseek-配置) |
| OpenRouter | gpt-4, claude-3 | 多模型选择 | [查看配置](README_Provider_Config.md#openrouter-配置) |
| Claude | claude-3-sonnet | 长文本理解 | [查看配置](README_Provider_Config.md#claude-配置) |
| Gemini | gemini-pro | 多模态支持 | [查看配置](README_Provider_Config.md#gemini-配置) |
| LM Studio | 本地模型 | 隐私保护 | [查看配置](README_Provider_Config.md#lm-studio-配置) |
| 智谱 AI | glm-4 | 国产模型 | [查看配置](README_Provider_Config.md#智谱-ai-配置) |
| 阿里云 | qwen-long | 长文本处理 | [查看配置](README_Provider_Config.md#阿里云配置) |

## 系统架构

```
AI_Gen_Novel/
├── app.py                    # 主应用程序
├── AIGN.py                   # 核心 AI 生成器
├── AIGN_Prompt.py            # 提示词模板
├── config_manager.py         # 静态配置管理
├── dynamic_config_manager.py # 动态配置管理
├── web_config_interface.py   # Web 配置界面
├── uniai/                    # AI 提供商接口
│   ├── deepseekAI.py
│   ├── openrouterAI.py
│   ├── claudeAI.py
│   ├── geminiAI.py
│   ├── lmstudioAI.py
│   ├── zhipuAI.py
│   └── aliAI.py
└── README_*.md               # 详细文档
```

## 版本历史

### v2.0.0 (当前版本)
- 完全重构的配置管理系统
- 统一的系统提示词处理机制
- 新增多个 AI 提供商支持
- 实现自动化批量生成功能
- 优化用户界面和用户体验

### v1.0.0 (原始版本)
- 基础的 AI 小说生成功能
- 多智能体协作框架
- 基于 RecurrentGPT 的循环生成

## 开发者资源 👨‍💻

### 快速开发指南

1. **新手入门**: 参考 [开发者文档](DEVELOPER.md) 了解项目结构
2. **API 使用**: 查看 [API 文档](API.md) 了解接口详情  
3. **代码贡献**: 阅读 [贡献指南](CONTRIBUTING.md) 了解开发流程
4. **架构理解**: 学习 [架构文档](ARCHITECTURE.md) 掌握系统设计

### 扩展开发

- **添加新的 AI 提供商**: 参考 [开发者文档 - AI 提供商扩展](DEVELOPER.md#ai-提供商扩展)
- **自定义智能体**: 参考 [开发者文档 - 智能体开发](DEVELOPER.md#智能体开发)
- **UI 定制**: 参考 [开发者文档 - 用户界面](DEVELOPER.md#用户界面)

### 调试和测试

- **配置调试**: 使用 Web 配置界面的测试功能
- **API 测试**: 参考 [API 文档](API.md) 中的示例代码
- **问题排查**: 查看 [故障排除指南](README_Provider_Config.md#故障排除)

## 开发说明

本项目完全由 Claude Code 开发，体现了 AI 在软件开发中的应用潜力：

- **代码生成**: 所有代码都是由 AI 生成
- **架构设计**: AI 参与了整体架构的设计和优化
- **问题解决**: AI 独立解决了多个技术难题
- **文档编写**: 包括本文档在内的所有文档都是 AI 编写

## 贡献指南

欢迎为项目做出贡献！我们提供了详细的指南帮助您参与开发：

📖 **[完整贡献指南](CONTRIBUTING.md)** - 详细的贡献流程和规范

### 快速贡献步骤

1. Fork 项目到您的 GitHub 账户
2. 阅读 [贡献指南](CONTRIBUTING.md) 了解开发规范
3. 创建特性分支 (`git checkout -b feature/amazing-feature`)
4. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
5. 推送到分支 (`git push origin feature/amazing-feature`)
6. 创建 Pull Request

### 贡献方式

- 🐛 **报告 Bug**: 通过 GitHub Issues 报告问题
- 💡 **功能建议**: 提出新功能或改进建议
- 📝 **改进文档**: 完善项目文档
- 🔧 **代码贡献**: 修复 Bug 或实现新功能
- 🤖 **AI 提供商**: 添加新的 AI 提供商支持

### 开发环境设置

参考 [贡献指南 - 开发环境设置](CONTRIBUTING.md#开发环境设置) 了解如何搭建开发环境。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- 感谢 [cjyyx/AI_Gen_Novel](https://github.com/cjyyx/AI_Gen_Novel) 的原始项目
- 感谢 Claude Code 的开发支持
- 感谢所有 AI 提供商的 API 支持

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系我们。

---

**注意**: 本项目仅用于研究和学习目的，生成的内容仅供参考。请遵守相关法律法规，合理使用 AI 技术。