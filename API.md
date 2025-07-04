# API 接口文档

本文档详细描述了 AI 网络小说生成器的内部 API 接口，供开发者参考和扩展使用。

## 目录

- [核心 API](#核心-api)
- [配置管理 API](#配置管理-api)
- [AI 提供商 API](#ai-提供商-api)
- [文件管理 API](#文件管理-api)
- [Web 界面 API](#web-界面-api)
- [工具类 API](#工具类-api)

## 核心 API

### AIGN 类

主要的小说生成引擎类，负责协调各个智能体的工作。

#### 构造函数

```python
AIGN(chatLLM: Callable) -> AIGN
```

**参数:**
- `chatLLM`: ChatLLM 实例，用于与 AI 提供商通信

**示例:**
```python
from AIGN import AIGN
from LLM import get_chatllm

chatLLM = get_chatllm()
aign = AIGN(chatLLM)
```

#### 核心方法

##### genNovelOutline()

```python
genNovelOutline() -> None
```

根据用户想法生成小说大纲。

**前置条件:**
- `self.user_idea` 已设置

**副作用:**
- 更新 `self.novel_outline`
- 更新 `self.novel_title`

##### genBeginning()

```python
genBeginning() -> None
```

生成小说开头部分。

**前置条件:**
- `self.novel_outline` 已设置
- `self.user_requriments` 已设置（可选）
- `self.embellishment_idea` 已设置（可选）

**副作用:**
- 更新 `self.novel_content`
- 更新 `self.writing_plan`
- 更新 `self.temp_setting`
- 创建输出文件

##### genNextParagraph()

```python
genNextParagraph() -> None
```

生成下一段小说内容。

**前置条件:**
- 已有小说内容基础

**副作用:**
- 追加到 `self.novel_content`
- 更新记忆和设定

##### autoGenerate()

```python
autoGenerate(target_chapters: int) -> None
```

自动生成指定数量的章节。

**参数:**
- `target_chapters`: 目标章节数 (5-500)

**特性:**
- 多线程执行
- 支持中断
- 自动保存
- 进度跟踪

##### stopAutoGeneration()

```python
stopAutoGeneration() -> None
```

停止自动生成过程。

**副作用:**
- 设置停止标志
- 等待当前章节完成

##### getProgress()

```python
getProgress() -> Dict[str, Any]
```

获取生成进度信息。

**返回值:**
```python
{
    "current_chapter": int,      # 当前章节数
    "target_chapters": int,      # 目标章节数
    "progress_percent": float,   # 完成百分比
    "is_running": bool,         # 是否正在运行
    "title": str,               # 小说标题
    "output_file": str,         # 输出文件路径
    "estimated_time": str       # 预计完成时间
}
```

#### 属性

```python
class AIGN:
    # 用户输入
    user_idea: str              # 用户想法
    user_requriments: str       # 写作要求
    embellishment_idea: str     # 润色要求
    
    # 生成内容
    novel_outline: str          # 小说大纲
    novel_title: str            # 小说标题
    novel_content: str          # 小说正文
    writing_plan: str           # 写作计划
    temp_setting: str           # 临时设定
    writing_memory: str         # 写作记忆
    
    # 文件管理
    current_output_file: str    # 当前输出文件路径
    
    # 自动生成控制
    target_chapter_count: int   # 目标章节数
    current_chapter: int        # 当前章节数
    auto_generate_thread: Thread # 自动生成线程
    stop_auto_generate: bool    # 停止标志
    
    # 功能开关
    enable_chapters: bool       # 启用章节标题
    enable_ending: bool         # 启用智能结尾
```

## 配置管理 API

### DynamicConfigManager 类

动态配置管理器，支持运行时配置修改。

#### 核心方法

##### get_config_manager()

```python
get_config_manager() -> DynamicConfigManager
```

获取全局配置管理器实例（单例模式）。

##### get_current_provider()

```python
get_current_provider() -> str
```

获取当前激活的 AI 提供商名称。

**返回值:**
- `"deepseek"`, `"openrouter"`, `"claude"`, 等

##### set_current_provider()

```python
set_current_provider(provider: str) -> bool
```

设置当前 AI 提供商。

**参数:**
- `provider`: 提供商名称

**返回值:**
- `True`: 设置成功
- `False`: 提供商不存在

##### get_current_config()

```python
get_current_config() -> Optional[ProviderConfig]
```

获取当前提供商的配置。

**返回值:**
```python
class ProviderConfig:
    api_key: str
    model_name: str
    base_url: Optional[str]
    system_prompt: str
```

##### update_provider_config()

```python
update_provider_config(provider: str, config_dict: Dict[str, Any]) -> bool
```

更新指定提供商的配置。

**参数:**
- `provider`: 提供商名称
- `config_dict`: 配置字典

**示例:**
```python
config_manager = get_config_manager()
config_manager.update_provider_config("deepseek", {
    "api_key": "your-api-key",
    "model_name": "deepseek-chat",
    "base_url": "https://api.deepseek.com"
})
```

##### test_provider_connection()

```python
test_provider_connection(provider: str) -> Tuple[bool, str]
```

测试指定提供商的连接。

**返回值:**
- `(True, "连接成功")`: 连接正常
- `(False, "错误信息")`: 连接失败

## AI 提供商 API

### 基础接口

所有 AI 提供商都实现以下接口：

```python
class BaseAI:
    def __init__(self, config: Dict[str, Any]):
        """初始化 AI 提供商"""
        pass
    
    def __call__(self, messages: List[Dict], **kwargs) -> Iterator[Dict]:
        """调用 AI API"""
        pass
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试连接"""
        pass
```

#### 标准调用接口

```python
def __call__(
    self, 
    messages: List[Dict[str, str]], 
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    stream: bool = True
) -> Iterator[Dict[str, Any]]
```

**参数:**
- `messages`: 消息列表，格式为 `[{"role": "user", "content": "..."}]`
- `temperature`: 创意程度 (0.0-2.0)
- `top_p`: 核采样参数 (0.0-1.0)
- `stream`: 是否流式返回

**返回值:**
每次迭代返回：
```python
{
    "content": str,      # 生成的内容
    "total_tokens": int  # 使用的 token 数量
}
```

### 具体提供商

#### DeepSeekAI

```python
class DeepSeekAI(BaseAI):
    def __init__(self, config):
        self.api_key = config["api_key"]
        self.model_name = config.get("model_name", "deepseek-chat")
        self.base_url = config.get("base_url", "https://api.deepseek.com")
```

**特殊配置:**
- 支持 `deepseek-chat` 和 `deepseek-coder` 模型
- 中文优化

#### OpenRouterAI

```python
class OpenRouterAI(BaseAI):
    def __init__(self, config):
        self.api_key = config["api_key"]
        self.model_name = config.get("model_name", "openai/gpt-4")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
```

**特殊配置:**
- 支持多种模型：`openai/gpt-4`, `anthropic/claude-3`, `meta/llama-2` 等
- 统一 API 格式

#### ClaudeAI

```python
class ClaudeAI(BaseAI):
    def __init__(self, config):
        self.api_key = config["api_key"]
        self.model_name = config.get("model_name", "claude-3-sonnet-20240229")
        self.base_url = config.get("base_url", "https://api.anthropic.com")
```

**特殊配置:**
- 支持 Claude-3 系列模型
- 长文本处理能力强

## 文件管理 API

### 文件操作

#### create_output_file()

```python
create_output_file(title: str, content: str) -> str
```

创建输出文件。

**参数:**
- `title`: 小说标题
- `content`: 初始内容

**返回值:**
- 文件路径

#### append_to_file()

```python
append_to_file(file_path: str, content: str) -> bool
```

追加内容到文件。

#### safe_filename()

```python
safe_filename(filename: str) -> str
```

生成安全的文件名（移除非法字符）。

**示例:**
```python
safe_name = safe_filename("我的小说/第一章")
# 返回: "我的小说_第一章"
```

## Web 界面 API

### Gradio 界面组件

#### 主要事件处理函数

##### gen_ouline_button_clicked()

```python
gen_ouline_button_clicked(
    aign: AIGN, 
    user_idea: str, 
    history: List
) -> Iterator[List]
```

处理生成大纲按钮点击事件。

##### gen_beginning_button_clicked()

```python
gen_beginning_button_clicked(
    aign: AIGN,
    history: List,
    novel_outline: str,
    user_requriments: str,
    embellishment_idea: str,
    enable_chapters: bool,
    enable_ending: bool
) -> Iterator[List]
```

处理生成开头按钮点击事件。

##### auto_generate_button_clicked()

```python
auto_generate_button_clicked(
    aign: AIGN,
    target_chapters: int,
    enable_chapters: bool,
    enable_ending: bool
) -> List
```

处理自动生成按钮点击事件。

#### 配置界面

##### get_web_config_interface()

```python
get_web_config_interface() -> WebConfigInterface
```

获取 Web 配置界面实例。

##### create_config_interface()

```python
create_config_interface() -> Dict[str, Any]
```

创建配置界面组件。

**返回值:**
```python
{
    "provider_dropdown": gr.Dropdown,
    "api_key_input": gr.Textbox,
    "model_input": gr.Textbox,
    "test_btn": gr.Button,
    "save_btn": gr.Button,
    "reload_btn": gr.Button,
    "status_output": gr.Textbox
}
```

## 工具类 API

### 版本管理

#### get_version()

```python
get_version() -> str
```

获取当前版本号。

#### get_full_version_info()

```python
get_full_version_info() -> Dict[str, Any]
```

获取完整版本信息。

**返回值:**
```python
{
    "version": "2.0.0",
    "author": "Claude Code",
    "description": "AI 网络小说生成器 - 增强版",
    "url": "https://github.com/cs2764/AI_Gen_Novel",
    "features": [...],
    "ai_providers": [...]
}
```

### 提示词管理

#### get_system_prompt()

```python
get_system_prompt(agent_type: str) -> str
```

获取指定智能体的系统提示词。

**参数:**
- `agent_type`: 智能体类型（`"outline_writer"`, `"title_generator"` 等）

#### merge_system_prompt()

```python
merge_system_prompt(system_prompt: str, user_message: str) -> str
```

将系统提示词合并到用户消息中。

## 错误处理

### 异常类型

```python
class ConfigError(Exception):
    """配置相关错误"""
    pass

class APIError(Exception):
    """API 调用错误"""
    pass

class FileError(Exception):
    """文件操作错误"""
    pass
```

### 错误码

```python
ERROR_CODES = {
    "CONFIG_NOT_FOUND": 1001,
    "API_KEY_INVALID": 1002,
    "NETWORK_ERROR": 1003,
    "FILE_WRITE_ERROR": 2001,
    "GENERATION_FAILED": 3001
}
```

## 使用示例

### 基本使用

```python
from AIGN import AIGN
from LLM import get_chatllm
from dynamic_config_manager import get_config_manager

# 1. 获取配置管理器
config_manager = get_config_manager()

# 2. 设置 AI 提供商
config_manager.set_current_provider("deepseek")
config_manager.update_provider_config("deepseek", {
    "api_key": "your-api-key",
    "model_name": "deepseek-chat"
})

# 3. 获取 ChatLLM 实例
chatLLM = get_chatllm()

# 4. 创建 AIGN 实例
aign = AIGN(chatLLM)

# 5. 设置想法并生成大纲
aign.user_idea = "一个关于时间旅行的科幻小说"
aign.genNovelOutline()

# 6. 生成开头
aign.user_requriments = "轻松幽默的风格"
aign.genBeginning()

# 7. 自动生成
aign.autoGenerate(20)  # 生成20章
```

### 自定义 AI 提供商

```python
from uniai.base import BaseAI

class CustomAI(BaseAI):
    def __init__(self, config):
        super().__init__(config)
        # 初始化自定义 API 客户端
    
    def __call__(self, messages, **kwargs):
        # 实现 API 调用逻辑
        for chunk in self.stream_api_call(messages, **kwargs):
            yield {
                "content": chunk.get("text", ""),
                "total_tokens": chunk.get("usage", {}).get("total_tokens", 0)
            }
    
    def test_connection(self):
        try:
            # 测试连接逻辑
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

# 注册到系统
from LLM import register_provider
register_provider("custom", CustomAI)
```

## 性能考虑

### API 调用优化

- 使用连接池减少连接开销
- 实现请求重试机制
- 合理设置超时时间

### 内存优化

- 定期清理长文本内容
- 使用生成器减少内存占用
- 实现智能记忆压缩

### 并发处理

- 使用线程池处理并发请求
- 实现任务队列管理
- 避免竞态条件

---

*本文档与代码同步更新，如有疑问请查看源码或提交 Issue。*