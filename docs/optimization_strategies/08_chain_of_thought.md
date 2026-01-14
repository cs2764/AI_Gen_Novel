# 方案8: 链式思考优化
# Strategy 8: Chain-of-Thought Optimization

**优先级**: ⭐⭐ 中低 | **实施复杂度**: 中 | **预期收益**: 合并多步骤，减少API调用

---

## 概述

利用更高效的推理模式，在单次API调用中完成多步任务（写作+润色+记忆提取），减少API往返次数。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **长输出** | ✅ **必需** | 需要8K+ output tokens |
| **复杂指令** | ✅ **必需** | 执行多步骤任务 |
| **结构化输出** | ⚠️ 推荐 | 确保输出格式正确 |
| **推理能力** | ⚠️ 推荐 | 更好的多步骤规划 |

> [!IMPORTANT]
> 此方案**需要模型支持长输出**（至少8000 tokens），部分模型/提供商的输出限制可能不足。

---

## 提供商兼容性

| 提供商 | 最大输出Token | 兼容性 | 说明 |
|-------|-------------|-------|-----|
| Claude | 8192 | ✅ **推荐** | Claude 3.5 Sonnet |
| DeepSeek | 8192 | ✅ **推荐** | DeepSeek V3 |
| OpenRouter | 取决于模型 | ✅ 兼容 | 选择长输出模型 |
| Gemini | 8192 | ✅ 兼容 | Gemini 1.5 Pro |
| 智谱AI | 4096 | ⚠️ 受限 | GLM-4限制较低 |
| 阿里云 | 8192 | ✅ 兼容 | Qwen2.5-Max |
| Fireworks | 取决于模型 | ⚠️ 需验证 | 检查具体模型 |
| Grok | 4096 | ⚠️ 受限 | 输出限制可能不足 |
| Lambda | 取决于模型 | ⚠️ 需验证 | 检查具体模型 |
| SiliconFlow | 8192 | ✅ 兼容 | DeepSeek-V3支持 |
| LM Studio | 取决于模型 | ⚠️ 需验证 | 本地模型限制各异 |

### 推荐模型

| 场景 | 推荐模型 | 最大输出 |
|-----|---------|---------|
| 最佳体验 | Claude 3.5 Sonnet | 8192 |
| 性价比 | DeepSeek V3 | 8192 |
| 超长输出 | Gemini 1.5 Pro | 8192+ |

---

## 实现方案

### 合并输出Schema

```python
# 一次调用完成写作+润色+记忆提取
combined_generation_schema = {
    "type": "object",
    "properties": {
        "thinking": {
            "type": "string",
            "description": "写作思考过程（可选输出）"
        },
        "draft": {
            "type": "string",
            "description": "初稿内容",
            "minLength": 2000
        },
        "polished_content": {
            "type": "string",
            "description": "润色后的最终内容",
            "minLength": 2500
        },
        "key_events": {
            "type": "array",
            "items": {"type": "string"},
            "description": "本章关键事件（用于记忆）",
            "minItems": 2,
            "maxItems": 5
        },
        "character_developments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "character": {"type": "string"},
                    "development": {"type": "string"}
                }
            },
            "description": "角色发展变化"
        },
        "plot_points_advanced": {
            "type": "array",
            "items": {"type": "string"},
            "description": "推进的情节点"
        },
        "cliffhanger": {
            "type": "string",
            "description": "章末悬念"
        },
        "quality_self_assessment": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "自我质量评分"
        }
    },
    "required": ["polished_content", "key_events"]
}
```

### 合并提示词

```python
COMBINED_GENERATION_PROMPT = """
# 任务：完成本章的完整写作流程

你需要在一次输出中完成以下所有步骤：

## 步骤1: 构思与初稿
根据故事线和上下文，写作本章初稿。

## 步骤2: 自我润色
对初稿进行润色：
- 丰富环境描写和细节刻画
- 深化人物心理描写
- 优化语言表达的生动性
- 增强场景的画面感

## 步骤3: 提取记忆
从完成的内容中提取：
- 关键事件（2-5个）
- 角色发展变化
- 推进的情节点
- 章末悬念

## 步骤4: 质量自评
给自己的作品打分（0-10），并确保达到8分以上才输出。

## 输出格式
按指定JSON格式输出全部结果。
"""

class CombinedWriter:
    """合并写作器"""
    
    def __init__(self, chatLLM):
        self.chatLLM = chatLLM
        self.supports_long_output = self._check_output_limit()
    
    def _check_output_limit(self) -> bool:
        """检查是否支持长输出"""
        # 根据provider检查
        provider = getattr(self.chatLLM, 'provider', 'unknown')
        long_output_providers = ['claude', 'deepseek', 'gemini', 'qwen']
        return any(p in provider.lower() for p in long_output_providers)
    
    async def generate_chapter(self, context: dict) -> dict:
        """单次调用生成完整章节"""
        
        if not self.supports_long_output:
            # 降级到传统多步骤流程
            return await self._fallback_generation(context)
        
        messages = [
            {"role": "system", "content": COMBINED_GENERATION_PROMPT},
            {"role": "user", "content": self._build_context(context)}
        ]
        
        response = await self.chatLLM(
            messages=messages,
            max_tokens=8000,
            response_format={"type": "json_object", "schema": combined_generation_schema}
        )
        
        result = json.loads(response.content)
        
        # 质量检查
        if result.get('quality_self_assessment', 0) < 7:
            # 质量不足，触发重试
            return await self._retry_with_feedback(result, context)
        
        return result
    
    async def _fallback_generation(self, context: dict) -> dict:
        """降级到传统流程"""
        # 分步骤执行
        draft = await self.write(context)
        polished = await self.polish(draft)
        memory = await self.extract_memory(polished)
        
        return {
            'polished_content': polished,
            'key_events': memory['events'],
            'character_developments': memory.get('characters', [])
        }
```

---

## 预期效果

| 指标 | 传统流程 | 合并流程 | 改善 |
|-----|---------|---------|-----|
| API调用次数 | 3次 | 1次 | **-67%** |
| 总延迟 | 45-60秒 | 20-30秒 | **-50%** |
| 输入Token | 15000×3 | 15000×1 | **-67%** |
| 输出Token | 12000 | 12000 | 持平 |

---

## 实施步骤

1. **验证模型能力**: 确认各提供商的输出Token限制
2. **设计Schema**: 创建合并输出的JSON Schema
3. **实现Writer**: 创建 `CombinedWriter` 类
4. **添加降级**: 不支持时自动降级到多步骤
5. **质量监控**: 监控合并生成的质量

**预估工作量**: 1周

---

## 注意事项

> [!CAUTION]
> - 单次长生成可能增加失败风险
> - 需要处理部分输出失败的情况
> - 输出Token限制是硬性约束
