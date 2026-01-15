# 方案4: 提示词精简优化
# Strategy 4: Prompt Optimization

**优先级**: ⭐⭐⭐⭐⭐ 最高 | **实施复杂度**: 低 | **预期Token节省**: 20-30%

---

## 概述

当前 `AIGN_Prompt.py` 中的系统提示词平均长度约3000-5000 tokens。本方案通过条件加载、提示词压缩和参数化模板显著减少提示词Token消耗。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **基础对话** | ✅ 必需 | 标准文本生成能力 |
| **指令遵循** | ✅ 必需 | 所有现代模型都支持 |

> [!NOTE]
> 此方案是**纯代码层面优化**，**对模型能力无特殊要求**，所有提供商均可使用。

---

## 提供商兼容性

| 提供商 | 兼容性 | 说明 |
|-------|-------|-----|
| DeepSeek | ✅ 完全兼容 | 指令遵循能力强 |
| OpenRouter | ✅ 完全兼容 | 所有模型 |
| Claude | ✅ 完全兼容 | 优秀的指令遵循 |
| Gemini | ✅ 完全兼容 | - |
| 智谱AI | ✅ 完全兼容 | - |
| 阿里云 | ✅ 完全兼容 | - |
| Fireworks | ✅ 完全兼容 | - |
| Grok | ✅ 完全兼容 | - |
| Lambda | ✅ 完全兼容 | - |
| SiliconFlow | ✅ 完全兼容 | - |
| LM Studio | ✅ 完全兼容 | - |

**所有11个提供商均完全兼容此优化方案。**

---

## 实现方案

### 1. 条件加载系统

```python
class AdaptivePromptLoader:
    """自适应提示词加载器"""
    
    # 复杂度级别定义
    COMPLEXITY_LEVELS = {
        'minimal': {
            'max_tokens': 500,
            'sections': ['core_instruction', 'output_format'],
            'use_cases': ['过渡章节', '简单对话场景']
        },
        'standard': {
            'max_tokens': 1500,
            'sections': ['core_instruction', 'writing_guidelines', 'output_format'],
            'use_cases': ['普通章节', '一般剧情发展']
        },
        'detailed': {
            'max_tokens': 3000,
            'sections': ['core_instruction', 'writing_guidelines', 'quality_checklist', 
                        'style_requirements', 'output_format'],
            'use_cases': ['高潮章节', '关键转折', '复杂场景']
        }
    }
    
    def __init__(self, prompts_dir='prompts'):
        self.prompts_dir = prompts_dir
        self.cache = {}
    
    def get_prompt(self, agent_type: str, complexity: str = 'standard', 
                   chapter_type: str = None) -> str:
        """
        获取适当复杂度的提示词
        
        Args:
            agent_type: 'writer', 'embellisher', 'memory_maker' 等
            complexity: 'minimal', 'standard', 'detailed'
            chapter_type: 可选，用于自动推断复杂度
        
        Returns:
            str: 组装后的提示词
        """
        # 自动推断复杂度
        if chapter_type and complexity == 'auto':
            complexity = self._infer_complexity(chapter_type)
        
        config = self.COMPLEXITY_LEVELS[complexity]
        sections = config['sections']
        
        # 加载并组装提示词
        prompt_parts = []
        for section in sections:
            section_content = self._load_section(agent_type, section)
            if section_content:
                prompt_parts.append(section_content)
        
        return "\n\n".join(prompt_parts)
    
    def _infer_complexity(self, chapter_type: str) -> str:
        """根据章节类型推断复杂度"""
        type_mapping = {
            'climax': 'detailed',
            'turning_point': 'detailed',
            'development': 'standard',
            'transition': 'minimal',
            'dialogue': 'minimal',
        }
        return type_mapping.get(chapter_type, 'standard')
```

### 2. 提示词模块化结构

```
prompts/
├── core/
│   ├── writer_core.txt          # 核心写作指令 (~300 tokens)
│   ├── embellisher_core.txt     # 核心润色指令 (~200 tokens)
│   └── memory_core.txt          # 核心记忆指令 (~150 tokens)
├── guidelines/
│   ├── writing_guidelines.txt   # 写作规范 (~400 tokens)
│   ├── quality_checklist.txt    # 质量检查 (~300 tokens)
│   └── style_requirements.txt   # 风格要求 (~300 tokens)
├── formats/
│   ├── output_format_simple.txt # 简单输出格式 (~50 tokens)
│   └── output_format_full.txt   # 完整输出格式 (~150 tokens)
└── styles/
    ├── xianxia/
    ├── urban/
    └── ...
```

### 3. 核心提示词压缩示例

**当前写作提示词** (~3000 tokens):
```
# Role:
您是一位才华横溢的网络小说作家，因打破常规，用不同寻常的剧情和创意著称。
## Background And Goals:
您的任务是根据用户提供的小说大纲、前文记忆和计划，续写小说正文内容。您需要：
1. 理解和提取上下文信息
2. 故事线对照确保遵循剧情
3. 构建心灵图景...
[中间省略大量详细指导]
...
## 质量检查清单
- 是否定义了明确主线目标
- 是否规划关键反转
...
```

**优化后核心提示词** (~800 tokens):
```
# 网络小说续写专家

## 核心任务
续写小说正文，保持剧情连贯，遵循本章故事线。

## 写作要求
1. 场景闭环：目标→冲突→结果→反应
2. 人物一致：行为符合性格设定
3. 对话表现：语气+动作+潜台词
4. 剧情推进：每段有新信息或风险升级

## 输出格式
# 正文
[2500-4000字的章节内容]

# 计划
[下一步发展方向]
```

---

## 预期效果

| 章节类型 | 当前Token | 优化后 | 节省 |
|---------|----------|-------|-----|
| 过渡章节 (40%) | 4000 | 1000 | 75% |
| 普通章节 (45%) | 4000 | 2000 | 50% |
| 高潮章节 (15%) | 4000 | 3500 | 12.5% |
| **加权平均** | 4000 | 1775 | **55.6%** |

---

## 实施步骤

1. **重构提示词文件**: 将现有提示词按模块拆分
2. **新增加载器**: 创建 `adaptive_prompt_loader.py`
3. **修改Agent初始化**: 使用条件加载替代固定提示词
4. **添加章节类型检测**: 自动识别章节复杂度
5. **A/B测试**: 对比优化前后的生成质量

**预估工作量**: 3-5天

---

## 风险缓解

> [!CAUTION]
> 提示词过度简化可能影响生成质量。建议：
> 1. 先在非关键场景测试
> 2. 保留完整提示词作为回退选项
> 3. 建立质量监控指标
