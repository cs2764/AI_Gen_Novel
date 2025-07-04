# 安装和使用指南

## 系统要求

- Python 3.8 或更高版本
- 至少 4GB 可用内存
- 稳定的网络连接（用于 API 调用）

## 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动程序

```bash
python app.py
```

程序会自动：
- 创建配置文件模板
- 启动 Web 界面
- 自动打开浏览器

## 详细配置

### API 密钥配置

首次启动时，您需要配置 AI 提供商的 API 密钥：

1. **在 Web 界面中配置**（推荐）：
   - 启动程序后，打开配置面板
   - 选择要使用的 AI 提供商
   - 输入对应的 API 密钥
   - 点击"测试连接"验证
   - 保存配置

2. **手动编辑配置文件**：
   - 编辑 `config.py` 文件
   - 填入相应的 API 密钥和配置
   - 重启程序

### 支持的 AI 提供商

#### DeepSeek
```python
DEEPSEEK_CONFIG = {
    "api_key": "your-deepseek-api-key",
    "model_name": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "system_prompt": ""
}
```

#### OpenRouter
```python
OPENROUTER_CONFIG = {
    "api_key": "your-openrouter-api-key", 
    "model_name": "openai/gpt-4",
    "base_url": "https://openrouter.ai/api/v1",
    "system_prompt": ""
}
```

#### Claude
```python
CLAUDE_CONFIG = {
    "api_key": "your-claude-api-key",
    "model_name": "claude-3-sonnet-20240229", 
    "base_url": "https://api.anthropic.com",
    "system_prompt": ""
}
```

#### Gemini
```python
GEMINI_CONFIG = {
    "api_key": "your-gemini-api-key",
    "model_name": "gemini-pro",
    "base_url": None,
    "system_prompt": ""
}
```

#### LM Studio (本地模型)
```python
LMSTUDIO_CONFIG = {
    "api_key": "lm-studio",
    "model_name": "local-model",
    "base_url": "http://localhost:1234/v1",
    "system_prompt": ""
}
```

#### 智谱 AI
```python
ZHIPU_CONFIG = {
    "api_key": "your-zhipu-api-key",
    "model_name": "glm-4",
    "base_url": None,
    "system_prompt": ""
}
```

#### 阿里云
```python
ALI_CONFIG = {
    "api_key": "your-ali-api-key",
    "model_name": "qwen-long",
    "base_url": None,
    "system_prompt": ""
}
```

## 使用教程

### 创建第一部小说

1. **输入创意想法**
   - 在"想法"框中描述您的小说创意
   - 例如："主角在异世界冒险，拥有时间回溯能力"

2. **生成大纲**
   - 点击"生成大纲"按钮
   - 等待 AI 生成详细的故事大纲
   - 可以手动编辑和完善大纲

3. **设置写作要求**
   - 在"写作要求"中指定文风、长度等要求
   - 在"润色要求"中设置语言风格偏好

4. **生成开头**
   - 点击"生成开头"按钮
   - 系统会生成吸引人的小说开头
   - 同时建立写作计划和临时设定

5. **继续创作**
   - 点击"生成下一段"继续故事
   - 或使用"自动生成"批量创建多个章节

### 自动化生成

1. **设置参数**
   - 选择是否启用章节标题
   - 选择是否启用智能结尾
   - 设置目标章节数（5-500章）

2. **开始自动生成**
   - 点击"开始自动生成"
   - 系统会自动生成指定数量的章节
   - 可以随时暂停或停止

3. **监控进度**
   - 实时查看生成进度
   - 查看预计完成时间
   - 查看最近的生成日志

## 高级功能

### 配置优化

#### 温度设置
不同智能体的创意程度可在配置中调整：
```python
TEMPERATURE_SETTINGS = {
    "outline_writer": 0.98,    # 大纲生成（高创意）
    "beginning_writer": 0.80,  # 开头写作（高创意）
    "novel_writer": 0.81,      # 正文写作（高创意）
    "embellisher": 0.92,       # 润色（极高创意）
    "memory_maker": 0.66       # 记忆管理（低创意，重准确性）
}
```

#### 网络设置
```python
NETWORK_SETTINGS = {
    "timeout": 60,        # 请求超时时间（秒）
    "max_retries": 3,     # 最大重试次数
    "retry_delay": 2.0    # 重试延迟（秒）
}
```

#### 小说设置
```python
NOVEL_SETTINGS = {
    "default_chapters": 20,  # 默认章节数
    "enable_chapters": True, # 启用章节标题
    "enable_ending": True,   # 启用智能结尾
    "auto_save": True,       # 自动保存
    "output_dir": "output"   # 输出目录
}
```

### 文件管理

- **自动保存**: 每章生成后自动保存到 `output/` 目录
- **文件命名**: 格式为 `{标题}_{日期时间}.txt`
- **备份功能**: 自动生成 `novel_record.md` 记录文件

### 性能优化

#### 内存管理
- 当故事内容超过 2000 字符时，自动压缩为记忆
- 定期清理不必要的缓存数据

#### 网络优化
- 支持流式 API 调用，减少等待时间
- 自动重试机制处理网络异常

## 故障排除

### 常见问题

#### 1. API 调用失败
**症状**: 显示"API调用失败"错误
**解决方案**:
- 检查网络连接
- 验证 API 密钥是否正确
- 确认 API 额度是否充足
- 检查防火墙设置

#### 2. 配置无法保存
**症状**: 配置修改后不生效
**解决方案**:
- 检查文件权限
- 手动删除 `config.py` 重新生成
- 重启程序

#### 3. 生成内容质量不佳
**症状**: 生成的小说质量不满意
**解决方案**:
- 调整温度设置
- 改进提示词描述
- 尝试不同的 AI 提供商
- 细化写作要求

#### 4. 程序启动失败
**症状**: 程序无法启动或报错
**解决方案**:
- 检查 Python 版本（需要 3.8+）
- 重新安装依赖：`pip install -r requirements.txt`
- 检查端口是否被占用

### 调试模式

启用详细日志：
```bash
python app.py --debug
```

检查配置：
```bash
python -c "from version import print_version_info; print_version_info()"
```

## 更新升级

### 从 Git 更新
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### 配置迁移
升级后首次启动时，程序会自动检测并迁移旧配置。

## 性能建议

### 硬件要求
- **CPU**: 双核心或更高
- **内存**: 4GB 或更多
- **存储**: 至少 1GB 可用空间
- **网络**: 稳定的宽带连接

### 优化建议
- 使用 SSD 硬盘提高文件读写速度
- 确保足够的内存避免频繁交换
- 使用稳定的网络连接减少 API 超时

## 技术支持

如遇到问题：
1. 查看 [GitHub Issues](https://github.com/cs2764/AI_Gen_Novel/issues)
2. 提交新的 Issue 描述问题
3. 包含错误日志和系统信息

---

*本指南持续更新中，如有疑问请查看项目文档或提交 Issue。*