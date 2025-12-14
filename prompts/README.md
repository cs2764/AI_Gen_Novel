# AI小说生成器提示词模块

## 目录结构

```
prompts/
├── __init__.py                    # 模块初始化文件
├── README.md                      # 本说明文件
├── common/                        # 通用提示词
│   ├── outline_prompt.py         # 大纲生成器
│   ├── character_prompt.py       # 人物列表生成器
│   ├── title_prompt.py           # 标题生成器
│   ├── storyline_prompt.py       # 故事线生成器
│   ├── chapter_summary_prompt.py # 章节总结生成器
│   ├── memory_prompt.py          # 前文记忆管理
│   └── detailed_outline_prompt.py# 详细大纲生成器
├── standard/                      # 标准模式提示词
│   ├── beginning_prompt.py       # 开头生成器
│   ├── writer_prompt.py          # 正文生成器
│   ├── embellisher_prompt.py     # 润色器
│   ├── ending_prompt.py          # 结尾生成器
│   ├── long_chapter_prompt.py    # 长章节模式
│   └── segment_prompts.py        # 分段生成（4段）
└── compact/                       # 精简模式提示词
    ├── writer_prompt.py          # 正文生成器（精简）
    ├── embellisher_prompt.py     # 润色器（精简）
    ├── long_chapter_prompt.py    # 长章节模式（精简）
    └── segment_prompts.py        # 分段生成（4段，精简）
```

## 模式说明

### 通用模式 (common/)
适用于所有生成场景的基础提示词：
- 大纲生成
- 人物设定
- 标题创作
- 故事线规划
- 章节总结
- 记忆管理

### 标准模式 (standard/)
完整的提示词，包含详细的指导和要求：
- 适合高质量生成
- Token消耗较大
- 包含完整的工作流程和示例
- 支持长章节模式
- 支持4段分段生成

### 精简模式 (compact/)
简化的提示词，降低Token消耗：
- 适合快速生成或Token受限场景
- 保留核心功能
- 简化工作流程说明
- 支持长章节模式
- 支持4段分段生成

## 使用方法

### 导入提示词

```python
# 导入通用提示词
from prompts import novel_outline_writer_prompt
from prompts import character_generator_prompt

# 导入标准模式提示词
from prompts.standard.writer_prompt import novel_writer_prompt
from prompts.standard.embellisher_prompt import novel_embellisher_prompt

# 导入精简模式提示词
from prompts.compact.writer_prompt import novel_writer_compact_prompt
from prompts.compact.embellisher_prompt import novel_embellisher_compact_prompt
```

### 选择合适的模式

1. **标准模式**：追求高质量输出，Token充足
2. **精简模式**：需要降低成本，或API有Token限制

## 维护说明

### 添加新提示词
1. 确定提示词类型（通用/标准/精简）
2. 在对应目录创建文件
3. 在 `__init__.py` 中添加导入
4. 更新本README文档

### 修改现有提示词
1. 找到对应的提示词文件
2. 修改提示词内容
3. 如果改变了接口，更新调用代码
4. 测试修改后的效果

## 注意事项

1. **格式一致性**：所有提示词必须保持输出格式的一致性
2. **语言要求**：所有输出必须使用简体中文
3. **禁止事项**：严禁在正文中出现字数统计、元评论等非故事内容
4. **版本管理**：修改提示词时注意版本兼容性

## 版本历史

- v2.0: 重构提示词结构，分离标准模式和精简模式
- v1.0: 初始版本，所有提示词在单一文件中
