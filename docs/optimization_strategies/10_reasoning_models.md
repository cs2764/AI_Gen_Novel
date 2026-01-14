# 方案10: 推理模型优化
# Strategy 10: Reasoning Model Optimization

**优先级**: ⭐⭐⭐ 中 | **实施复杂度**: 低 | **预期收益**: 复杂任务质量提升，简化提示词

---

## 概述

DeepSeek-R1、OpenAI o1等推理模型提供了内置的"思考"能力，可以在复杂规划任务中提供更优质输出，同时允许使用更简洁的提示词。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **推理/思考** | ✅ **必需** | 核心能力 |
| **长上下文** | ⚠️ 推荐 | 推理过程需要空间 |
| **复杂指令** | ⚠️ 推荐 | 理解多步骤任务 |

> [!NOTE]
> 此方案**仅适用于支持推理模式的模型**。普通模型可使用传统提示词。

---

## 提供商兼容性

| 提供商 | 推理模型 | 兼容性 | 说明 |
|-------|---------|-------|-----|
| DeepSeek | ✅ DeepSeek-R1 | ✅ **推荐** | 性价比最高的推理模型 |
| OpenRouter | ✅ o1, o1-mini, R1 | ✅ **推荐** | 多种推理模型可选 |
| Claude | ❌ 无专用推理模型 | ⚠️ 不适用 | 可用extended thinking替代 |
| Gemini | ⚠️ Gemini 2.0 Flash Thinking | ⚠️ 实验性 | 正在测试 |
| 智谱AI | ❌ 暂无 | ❌ 不适用 | - |
| 阿里云 | ⚠️ QwQ | ⚠️ 有限 | 推理能力待验证 |
| Fireworks | ✅ DeepSeek-R1 | ✅ 兼容 | 托管R1模型 |
| Grok | ❌ 暂无 | ❌ 不适用 | - |
| Lambda | ✅ DeepSeek-R1 | ✅ 兼容 | 托管R1模型 |
| SiliconFlow | ✅ DeepSeek-R1 | ✅ **推荐** | 国内推理模型首选 |
| LM Studio | ⚠️ 取决于本地模型 | ⚠️ 有限 | 需下载推理模型 |

### 推理模型清单

| 模型 | 提供商 | 推理能力 | 推荐场景 |
|-----|-------|---------|---------|
| DeepSeek-R1 | DeepSeek/SiliconFlow/Lambda/Fireworks | ⭐⭐⭐⭐⭐ | 故事规划、一致性分析 |
| o1-preview | OpenRouter | ⭐⭐⭐⭐⭐ | 复杂剧情设计 |
| o1-mini | OpenRouter | ⭐⭐⭐⭐ | 快速推理任务 |
| QwQ | 阿里云 | ⭐⭐⭐ | 中文推理 |

---

## 适用场景分析

```python
class ReasoningModelRouter:
    """推理模型路由器"""
    
    # 任务类型与推理需求映射
    TASK_REASONING_MAP = {
        # 高推理需求（推荐使用推理模型）
        'storyline_generation': {
            'reasoning_benefit': 'high',
            'reason': '需要长期规划，考虑伏笔、节奏、高潮分布'
        },
        'plot_repair': {
            'reasoning_benefit': 'high', 
            'reason': '需要分析逻辑漏洞并提出修复方案'
        },
        'outline_optimization': {
            'reasoning_benefit': 'high',
            'reason': '需要结构重组和剧情平衡分析'
        },
        'consistency_check': {
            'reasoning_benefit': 'high',
            'reason': '需要多点验证和逻辑推理'
        },
        
        # 中等推理需求（推理模型可选）
        'character_development': {
            'reasoning_benefit': 'medium',
            'reason': '需要考虑角色弧线和成长逻辑'
        },
        'complex_scene': {
            'reasoning_benefit': 'medium',
            'reason': '多角色互动需要逻辑协调'
        },
        
        # 低推理需求（普通模型即可）
        'chapter_writing': {
            'reasoning_benefit': 'low',
            'reason': '创意生成，推理可能过度理性化'
        },
        'polishing': {
            'reasoning_benefit': 'low',
            'reason': '语言润色不需要深度推理'
        },
        'memory_extraction': {
            'reasoning_benefit': 'low',
            'reason': '信息提取任务'
        }
    }
    
    def should_use_reasoning_model(self, task_type: str) -> bool:
        """判断是否应该使用推理模型"""
        task_info = self.TASK_REASONING_MAP.get(task_type, {})
        return task_info.get('reasoning_benefit') == 'high'
    
    def get_model_for_task(self, task_type: str, 
                           available_models: dict) -> str:
        """为任务选择最佳模型"""
        if self.should_use_reasoning_model(task_type):
            # 优先选择推理模型
            if 'deepseek-r1' in available_models:
                return 'deepseek-r1'
            if 'o1' in available_models:
                return 'o1'
        
        # 使用默认模型
        return available_models.get('default', 'deepseek-chat')
```

---

## 简化提示词策略

推理模型可以使用更简洁的提示词，让模型自行推理细节：

```python
# 传统提示词（适用于普通模型）- ~3000 tokens
TRADITIONAL_STORYLINE_PROMPT = """
# Role: 你是一位专业的故事规划师

## 任务
根据小说大纲，为接下来的10章生成详细故事线。

## 详细要求
1. 每章必须包含标题和描述
2. 描述需要包含：场景、主要事件、角色互动、情感变化
3. 注意情节的起承转合
4. 保持节奏平衡，高潮与过渡交替
5. 埋设适当的伏笔
6. 考虑角色成长弧线
7. 避免情节重复
...（更多细节）
"""

# 推理模型提示词 - ~500 tokens
REASONING_STORYLINE_PROMPT = """
你是故事规划师。根据大纲为接下来10章生成故事线。

要求：每章包含标题和详细描述。考虑节奏、伏笔、角色发展。

请先思考整体结构，然后输出结果。
"""
```

---

## 实现方案

```python
class ReasoningAwareAgent:
    """推理感知Agent"""
    
    REASONING_MODELS = [
        'deepseek-r1', 'deepseek-reasoner',
        'o1', 'o1-preview', 'o1-mini',
        'qwq', 'gemini-2.0-flash-thinking'
    ]
    
    def __init__(self, chatLLM):
        self.chatLLM = chatLLM
        self.is_reasoning_model = self._detect_reasoning_model()
    
    def _detect_reasoning_model(self) -> bool:
        """检测是否为推理模型"""
        model_name = getattr(self.chatLLM, 'model_name', '').lower()
        return any(rm in model_name for rm in self.REASONING_MODELS)
    
    def get_prompt(self, task_type: str, base_context: dict) -> str:
        """根据模型类型获取适当的提示词"""
        if self.is_reasoning_model:
            return self._get_simplified_prompt(task_type, base_context)
        else:
            return self._get_detailed_prompt(task_type, base_context)
    
    def _get_simplified_prompt(self, task_type: str, context: dict) -> str:
        """获取简化提示词（推理模型）"""
        prompts = {
            'storyline': f"""根据以下大纲为第{context['start']}-{context['end']}章生成故事线。
考虑节奏、伏笔、角色发展。先思考整体结构。

大纲：
{context['outline']}""",
            
            'consistency': f"""检查以下内容与已有设定的一致性。
分析可能的矛盾点并提出建议。

待检查内容：
{context['content']}

已有设定：
{context['settings']}""",
        }
        return prompts.get(task_type, "")
    
    def _get_detailed_prompt(self, task_type: str, context: dict) -> str:
        """获取详细提示词（普通模型）"""
        # 返回完整的传统提示词
        pass
```

---

## 预期效果

| 任务 | 普通模型 | 推理模型 | 改善 |
|-----|---------|---------|-----|
| 故事线生成质量 | 良好 | 优秀 | ↑ 质量 |
| 故事线提示词Token | 3000 | 500 | -83% Token |
| 剧情修复准确度 | 70% | 90% | +20% |
| 一致性检查 | 有限 | 全面 | 新能力 |

---

## 实施步骤

1. **模型检测**: 添加推理模型识别逻辑
2. **提示词分支**: 创建简化版和详细版提示词
3. **任务路由**: 为高推理需求任务自动选择推理模型
4. **监控**: 对比推理模型与普通模型的输出质量

**预估工作量**: 3-5天
