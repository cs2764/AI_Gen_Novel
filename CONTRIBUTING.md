# 贡献指南

欢迎为 AI 网络小说生成器项目做出贡献！本指南将帮助您了解如何参与项目开发。

## 目录

- [贡献方式](#贡献方式)
- [开发环境设置](#开发环境设置)
- [代码贡献流程](#代码贡献流程)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [文档编写](#文档编写)
- [问题反馈](#问题反馈)
- [功能建议](#功能建议)

## 贡献方式

您可以通过以下方式为项目做出贡献：

- 🐛 **报告 Bug**: 发现并报告程序错误
- 💡 **建议功能**: 提出新功能或改进建议
- 📝 **改进文档**: 完善项目文档
- 🔧 **代码贡献**: 修复 Bug 或实现新功能
- 🎨 **界面改进**: 优化用户界面体验
- 🤖 **AI 提供商**: 添加新的 AI 提供商支持
- 🌐 **国际化**: 添加多语言支持
- 📊 **性能优化**: 提升系统性能

## 开发环境设置

### 前置要求

- Python 3.8 或更高版本
- Git 版本控制工具
- 文本编辑器或 IDE (推荐 VS Code, PyCharm)

### 环境搭建

1. **Fork 项目**

   点击 GitHub 页面右上角的 "Fork" 按钮，将项目复制到您的账户下。

2. **克隆代码**

   ```bash
   git clone https://github.com/您的用户名/AI_Gen_Novel.git
   cd AI_Gen_Novel
   ```

3. **创建虚拟环境**

   ```bash
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

5. **配置开发环境**

   ```bash
   # 复制配置模板
   cp config_template.py config.py
   
   # 编辑配置文件，添加您的 API 密钥
   # 至少配置一个 AI 提供商用于测试
   ```

6. **运行项目**

   ```bash
   python app.py
   ```

   访问 `http://localhost:7860` 确认项目正常运行。

### 开发工具推荐

#### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "venv/": true
    }
}
```

#### 推荐扩展

- Python
- Pylance
- Black Formatter
- GitLens
- Markdown All in One

## 代码贡献流程

### 1. 创建分支

```bash
# 切换到主分支
git checkout main

# 拉取最新代码
git pull origin main

# 创建新分支
git checkout -b feature/your-feature-name
# 或者
git checkout -b fix/your-bug-fix
```

### 2. 分支命名规范

- `feature/功能名称`: 新功能开发
- `fix/bug描述`: Bug 修复
- `docs/文档更新`: 文档修改
- `refactor/重构描述`: 代码重构
- `test/测试更新`: 测试相关修改

### 3. 编写代码

请遵循以下原则：

- 保持代码简洁清晰
- 添加必要的注释
- 编写相应的测试用例
- 确保代码符合项目规范

### 4. 提交代码

```bash
# 添加修改的文件
git add .

# 提交代码
git commit -m "feat: 添加新的 AI 提供商支持"

# 推送到远程仓库
git push origin feature/your-feature-name
```

### 5. 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型说明

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

#### 示例

```
feat(providers): 添加 ChatGPT 提供商支持

- 实现 ChatGPT API 接口
- 添加配置选项
- 更新文档

Closes #123
```

### 6. 创建 Pull Request

1. 在 GitHub 上点击 "New Pull Request"
2. 选择您的分支
3. 填写 PR 描述
4. 等待代码审查

#### PR 描述模板

```markdown
## 变更描述

简要描述您的修改内容。

## 变更类型

- [ ] Bug 修复
- [ ] 新功能
- [ ] 代码重构
- [ ] 文档更新
- [ ] 性能优化
- [ ] 其他

## 测试

- [ ] 本地测试通过
- [ ] 添加了新的测试用例
- [ ] 现有测试用例通过

## 相关问题

Closes #问题号码

## 截图

如果涉及界面修改，请附上截图。
```

## 代码规范

### Python 代码规范

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 标准：

#### 1. 代码格式

```python
# 使用 4 个空格缩进
def example_function(param1, param2):
    if param1 > param2:
        return param1
    return param2

# 行长度不超过 88 字符
def very_long_function_name(
    parameter_one, parameter_two, parameter_three
):
    pass
```

#### 2. 命名规范

```python
# 类名：PascalCase
class ConfigManager:
    pass

# 函数名：snake_case
def get_current_provider():
    pass

# 常量：UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# 变量：snake_case
user_input = ""
```

#### 3. 导入规范

```python
# 标准库
import os
import sys
from typing import List, Dict, Optional

# 第三方库
import gradio as gr
import requests

# 本地模块
from .config import get_config
from .utils import safe_filename
```

#### 4. 文档字符串

```python
def generate_novel(user_idea: str, chapters: int = 10) -> str:
    """
    生成小说内容
    
    Args:
        user_idea: 用户的创意想法
        chapters: 生成的章节数，默认 10 章
    
    Returns:
        str: 生成的小说内容
    
    Raises:
        ValueError: 当章节数小于 1 时抛出
        APIError: 当 API 调用失败时抛出
    
    Example:
        >>> novel = generate_novel("科幻冒险", 5)
        >>> print(len(novel))
        1000
    """
    pass
```

#### 5. 类型注解

```python
from typing import List, Dict, Optional, Union

def process_messages(
    messages: List[Dict[str, str]], 
    temperature: Optional[float] = None
) -> Union[str, None]:
    """处理消息列表"""
    pass
```

### 代码质量检查

#### 使用 Black 格式化代码

```bash
# 安装 Black
pip install black

# 格式化代码
black .

# 检查格式
black --check .
```

#### 使用 Pylint 检查代码

```bash
# 安装 Pylint
pip install pylint

# 检查代码
pylint *.py
```

#### 使用 MyPy 检查类型

```bash
# 安装 MyPy
pip install mypy

# 检查类型
mypy *.py
```

## 测试指南

### 测试结构

```
tests/
├── test_core/
│   ├── test_aign.py
│   ├── test_config.py
│   └── test_file_manager.py
├── test_providers/
│   ├── test_deepseek.py
│   ├── test_openrouter.py
│   └── test_claude.py
├── test_ui/
│   └── test_web_interface.py
└── conftest.py
```

### 编写测试

#### 单元测试示例

```python
import unittest
from unittest.mock import Mock, patch
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        """每个测试方法前的设置"""
        self.mock_config = {
            'api_key': 'test-key',
            'model_name': 'test-model'
        }
        self.instance = YourClass(self.mock_config)
    
    def test_method_success(self):
        """测试方法成功情况"""
        result = self.instance.method()
        self.assertEqual(result, expected_value)
    
    def test_method_failure(self):
        """测试方法失败情况"""
        with self.assertRaises(ValueError):
            self.instance.method(invalid_param)
    
    @patch('your_module.external_api')
    def test_with_mock(self, mock_api):
        """使用 Mock 测试"""
        mock_api.return_value = {'status': 'success'}
        result = self.instance.call_external_api()
        self.assertTrue(result)
```

#### 集成测试示例

```python
import pytest
from your_module import create_app

class TestIntegration:
    def setup_method(self):
        """每个测试方法前的设置"""
        self.app = create_app(test_config=True)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 设置数据
        user_idea = "测试想法"
        
        # 执行流程
        result = self.app.generate_novel(user_idea)
        
        # 验证结果
        assert result is not None
        assert len(result) > 0
```

### 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_core/test_aign.py

# 运行特定测试方法
python -m pytest tests/test_core/test_aign.py::TestAIGN::test_generate_outline

# 运行测试并生成覆盖率报告
python -m pytest --cov=. --cov-report=html

# 运行测试并显示详细输出
python -m pytest -v
```

### 测试要求

- 新功能必须包含测试用例
- 测试覆盖率应保持在 80% 以上
- 修复 Bug 时应添加回归测试
- 测试应该独立且可重复

## 文档编写

### 文档类型

1. **API 文档**: 详细的接口说明
2. **用户指南**: 面向用户的使用说明
3. **开发文档**: 面向开发者的技术文档
4. **更新日志**: 版本变更记录

### 文档格式

使用 Markdown 格式，遵循以下规范：

#### 1. 标题结构

```markdown
# 一级标题
## 二级标题
### 三级标题
#### 四级标题
```

#### 2. 代码块

```markdown
# 行内代码
使用 `code` 表示行内代码

# 代码块
```python
def example():
    return "Hello, World!"
```
```

#### 3. 链接和图片

```markdown
[链接文本](URL)
![图片描述](图片URL)
```

#### 4. 表格

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 值1 | 值2 | 值3 |
```

### 文档更新

- 新增功能时更新相关文档
- 修改接口时更新 API 文档
- 重大变更时更新 CHANGELOG.md

## 问题反馈

### 如何报告 Bug

1. 在 GitHub Issues 中搜索是否已存在相同问题
2. 如果没有，创建新的 Issue
3. 使用 Bug 报告模板
4. 提供详细的复现步骤

### Bug 报告模板

```markdown
**Bug 描述**
简要描述遇到的问题。

**复现步骤**
1. 点击 '...'
2. 滚动到 '...'
3. 看到错误

**预期行为**
描述您期望发生的行为。

**实际行为**
描述实际发生的行为。

**屏幕截图**
如果适用，添加屏幕截图说明问题。

**环境信息**
- 操作系统: [例如 Windows 10]
- Python 版本: [例如 3.9.0]
- 项目版本: [例如 2.0.0]
- AI 提供商: [例如 DeepSeek]

**附加信息**
任何其他相关信息。
```

## 功能建议

### 如何提出功能建议

1. 检查现有的 Feature Request
2. 创建新的 Issue
3. 使用功能建议模板
4. 详细描述功能需求

### 功能建议模板

```markdown
**功能描述**
简要描述您希望的功能。

**问题背景**
描述当前存在的问题或不便。

**解决方案**
描述您希望的解决方案。

**替代方案**
描述您考虑过的其他解决方案。

**使用场景**
描述具体的使用场景。

**优先级**
- [ ] 高优先级
- [ ] 中优先级
- [ ] 低优先级

**实现难度**
- [ ] 简单
- [ ] 中等
- [ ] 复杂

**附加信息**
任何其他相关信息。
```

## 社区准则

### 行为准则

我们致力于为每个人提供友好、安全和欢迎的环境。请遵守以下准则：

1. **尊重他人**: 尊重不同的观点和经验
2. **建设性交流**: 提供有帮助的反馈和建议
3. **包容友好**: 欢迎新手和不同背景的贡献者
4. **专业态度**: 保持专业和礼貌的沟通方式

### 沟通渠道

- **GitHub Issues**: 报告问题和建议
- **Pull Requests**: 代码审查和讨论
- **Discussions**: 一般性讨论和问答

## 版本发布

### 版本号规范

采用 [语义化版本控制](https://semver.org/lang/zh-CN/)：

- `MAJOR.MINOR.PATCH` (例如 2.1.0)
- `MAJOR`: 不兼容的 API 修改
- `MINOR`: 向后兼容的功能性新增
- `PATCH`: 向后兼容的问题修正

### 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建 Git 标签
4. 发布 GitHub Release

## 许可证

本项目采用 MIT 许可证。贡献代码即表示您同意将您的贡献以相同许可证发布。

## 致谢

感谢所有为项目做出贡献的开发者！您的贡献让这个项目变得更好。

---

*如果您对贡献过程有任何疑问，请随时创建 Issue 或 Discussion 进行讨论。*