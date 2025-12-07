# 提示词快速参考指南

## 快速导入

```python
# 导入所有提示词
from AIGN_Prompt_Enhanced import *

# 或者按需导入
from AIGN_Prompt_Enhanced import (
    novel_outline_writer_prompt,      # 大纲生成
    novel_writer_prompt,               # 正文生成（标准）
    novel_writer_compact_prompt,       # 正文生成（精简）
)
```

## 提示词速查表

### 📝 通用提示词

| 提示词变量名 | 用途 | 文件位置 |
|------------|------|---------|
| `novel_outline_writer_prompt` | 生成小说大纲 | `common/outline_prompt.py` |
| `character_generator_prompt` | 生成人物列表 | `common/character_prompt.py` |
| `title_generator_prompt` | 生成标题 | `common/title_prompt.py` |
| `title_generator_json_prompt` | 生成标题(JSON) | `common/title_prompt.py` |
| `storyline_generator_prompt` | 生成故事线 | `common/storyline_prompt.py` |
| `chapter_summary_prompt` | 生成章节总结 | `common/chapter_summary_prompt.py` |
| `memory_maker_prompt` | 管理前文记忆 | `common/memory_prompt.py` |
| `detailed_outline_generator_prompt` | 生成详细大纲 | `common/detailed_outline_prompt.py` |

### 🎯 标准模式提示词

| 提示词变量名 | 用途 | 文件位置 |
|------------|------|---------|
| `novel_beginning_writer_prompt` | 生成开头 | `standard/beginning_prompt.py` |
| `novel_writer_prompt` | 生成正文 | `standard/writer_prompt.py` |
| `novel_embellisher_prompt` | 润色正文 | `standard/embellisher_prompt.py` |
| `ending_prompt` | 生成结尾 | `standard/ending_prompt.py` |
| `ending_embellisher_prompt` | 润色结尾 | `standard/ending_prompt.py` |
| `novel_writer_long_prompt` | 长章节模式 | `standard/long_chapter_prompt.py` |

#### 标准模式 - 分段提示词

| 提示词变量名 | 用途 | 文件位置 |
|------------|------|---------|
| `novel_writer_segment_1_prompt` | 正文第1段 | `standard/segment_prompts.py` |
| `novel_writer_segment_2_prompt` | 正文第2段 | `standard/segment_prompts.py` |
| `novel_writer_segment_3_prompt` | 正文第3段 | `standard/segment_prompts.py` |
| `novel_writer_segment_4_prompt` | 正文第4段 | `standard/segment_prompts.py` |
| `novel_embellisher_segment_1_prompt` | 润色第1段 | `standard/segment_prompts.py` |
| `novel_embellisher_segment_2_prompt` | 润色第2段 | `standard/segment_prompts.py` |
| `novel_embellisher_segment_3_prompt` | 润色第3段 | `standard/segment_prompts.py` |
| `novel_embellisher_segment_4_prompt` | 润色第4段 | `standard/segment_prompts.py` |
| `ending_writer_segment_1_prompt` | 结尾第1段 | `standard/segment_prompts.py` |
| `ending_writer_segment_2_prompt` | 结尾第2段 | `standard/segment_prompts.py` |
| `ending_writer_segment_3_prompt` | 结尾第3段 | `standard/segment_prompts.py` |
| `ending_writer_segment_4_prompt` | 结尾第4段 | `standard/segment_prompts.py` |

### ⚡ 精简模式提示词

| 提示词变量名 | 用途 | 文件位置 |
|------------|------|---------|
| `novel_writer_compact_prompt` | 生成正文（精简） | `compact/writer_prompt.py` |
| `novel_embellisher_compact_prompt` | 润色正文（精简） | `compact/embellisher_prompt.py` |
| `novel_writer_compact_long_prompt` | 长章节模式（精简） | `compact/long_chapter_prompt.py` |

#### 精简模式 - 分段提示词

| 提示词变量名 | 用途 | 文件位置 |
|------------|------|---------|
| `novel_writer_compact_segment_1_prompt` | 正文第1段（精简） | `compact/segment_prompts.py` |
| `novel_writer_compact_segment_2_prompt` | 正文第2段（精简） | `compact/segment_prompts.py` |
| `novel_writer_compact_segment_3_prompt` | 正文第3段（精简） | `compact/segment_prompts.py` |
| `novel_writer_compact_segment_4_prompt` | 正文第4段（精简） | `compact/segment_prompts.py` |
| `novel_embellisher_compact_segment_1_prompt` | 润色第1段（精简） | `compact/segment_prompts.py` |
| `novel_embellisher_compact_segment_2_prompt` | 润色第2段（精简） | `compact/segment_prompts.py` |
| `novel_embellisher_compact_segment_3_prompt` | 润色第3段（精简） | `compact/segment_prompts.py` |
| `novel_embellisher_compact_segment_4_prompt` | 润色第4段（精简） | `compact/segment_prompts.py` |

## 使用场景

### 场景1：生成新小说
```python
from AIGN_Prompt_Enhanced import (
    novel_outline_writer_prompt,      # 1. 生成大纲
    character_generator_prompt,       # 2. 生成人物
    title_generator_prompt,           # 3. 生成标题
    storyline_generator_prompt,       # 4. 生成故事线
)
```

### 场景2：标准模式写作
```python
from AIGN_Prompt_Enhanced import (
    novel_beginning_writer_prompt,    # 开头
    novel_writer_prompt,              # 正文
    novel_embellisher_prompt,         # 润色
    ending_prompt,                    # 结尾
)
```

### 场景3：精简模式写作（降低Token）
```python
from AIGN_Prompt_Enhanced import (
    novel_writer_compact_prompt,           # 正文（精简）
    novel_embellisher_compact_prompt,      # 润色（精简）
)
```

### 场景4：分段生成（每章4段）
```python
from AIGN_Prompt_Enhanced import (
    novel_writer_segment_1_prompt,    # 第1段
    novel_writer_segment_2_prompt,    # 第2段
    novel_writer_segment_3_prompt,    # 第3段
    novel_writer_segment_4_prompt,    # 第4段
)
```

## 模式选择建议

### 标准模式 vs 精简模式

| 特性 | 标准模式 | 精简模式 |
|-----|---------|---------|
| **Token消耗** | 较高 | 较低（约30-50%） |
| **输出质量** | 高质量，详细 | 良好，简洁 |
| **适用场景** | 追求质量，Token充足 | 降低成本，快速生成 |
| **提示词长度** | 完整详细 | 精简核心 |
| **工作流程** | 详细指导 | 简化流程 |

### 何时使用标准模式？
- ✅ 追求高质量输出
- ✅ Token预算充足
- ✅ 需要详细的创作指导
- ✅ 复杂的剧情和人物设定

### 何时使用精简模式？
- ✅ 需要降低API成本
- ✅ Token有限制
- ✅ 快速原型开发
- ✅ 简单的故事结构

## 常见问题

### Q: 如何切换模式？
A: 只需导入对应模式的提示词即可：
```python
# 标准模式
from AIGN_Prompt_Enhanced import novel_writer_prompt

# 精简模式
from AIGN_Prompt_Enhanced import novel_writer_compact_prompt
```

### Q: 分段生成有什么好处？
A: 
- 更好的内容控制
- 降低单次生成的Token消耗
- 可以针对每段进行优化
- 便于并行生成

### Q: 如何修改提示词？
A: 
1. 找到对应的文件（参考上面的表格）
2. 直接编辑文件中的提示词内容
3. 保存后重新导入即可生效

### Q: 原来的代码需要修改吗？
A: 不需要！新版本保持了向后兼容，原来的导入方式仍然有效。

## 更多信息

- 详细说明：查看 `prompts/README.md`
- 重构总结：查看 `PROMPT_REFACTOR_SUMMARY.md`
- 原始备份：`AIGN_Prompt_Enhanced.py.backup`
