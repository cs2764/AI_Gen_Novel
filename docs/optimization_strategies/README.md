# 优化方案索引
# Optimization Strategies Index

本目录包含AI网络小说生成器的7个优化方案详细文档。

> [!IMPORTANT]
> **首选核心方案**: [方案1: RAG风格学习与创作优化系统](01_rag_style_learning.md)
> 
> RAG系统是所有优化的基础，可同时实现：
> - 🎯 **风格学习**: 学习现有文章的写作风格
> - 💰 **Token优化**: 按需检索替代全量传递，节省40-80% Token
> 
> **建议先完成RAG系统开发，再考虑其他优化方案。**

---

## 📊 方案总览

| # | 方案名称 | 优先级 | 复杂度 | 预期收益 | 模型要求 |
|---|---------|-------|-------|---------|---------|
| **1** | [RAG风格学习与创作优化](01_rag_style_learning.md) | ⭐⭐⭐⭐⭐ | 高 | Token -40-80% + 质量提升 | Embedding API |
| 2 | [提示词精简优化](02_prompt_optimization.md) | ⭐⭐⭐⭐⭐ | 低 | Token -20-30% | 无特殊要求 |
| 3 | [增量式记忆摘要](03_incremental_memory.md) | ⭐⭐⭐⭐ | 低-中 | Token -15-20% | 无特殊要求 |
| 4 | [智能Agent协调器](04_smart_orchestrator.md) | ⭐⭐⭐⭐ | 中 | API调用 -30% | 无特殊要求 |
| 5 | [原生Function Calling](05_function_calling.md) | ⭐⭐⭐⭐ | 中 | Token -47-67% | Function Calling |
| 6 | [Structured Output](06_structured_output.md) | ⭐⭐⭐⭐ | 中 | 解析失败 0% | Structured Output |
| 7 | [并行弧生成](07_parallel_arc_generation.md) | ⭐⭐⭐ | 高 | 生成速度 +200% | 无特殊要求 |

---

## 🔥 推荐实施顺序

### Phase 1: 核心基础 (6周)

> [!TIP]
> RAG系统是其他优化的基础，完成后可大幅减少Token消耗并提升写作质量。

1. **方案1**: RAG风格学习与创作优化系统
   - 用例1: 风格学习RAG（索引现有文章）
   - 用例2: 创作流程RAG（索引大纲、故事线、人物设定）
   - 预期收益: Token -40-80%，写作风格一致性 +30%

### Phase 2: 快速胜利 (RAG完成后, 1-2周)

2. **方案2**: 提示词精简优化
3. **方案3**: 增量式记忆摘要
4. **方案4**: 智能Agent协调器

### Phase 3: 高级功能 (2-4周)

5. **方案5**: 原生Function Calling增强
6. **方案6**: Structured Output全面升级
7. **方案7**: 并行弧生成（可选，用于加速）

---

## 📋 提供商兼容性速查

| 提供商 | 基础功能 | Function Calling | Structured Output | Embedding | 推理模型 |
|-------|---------|-----------------|-------------------|-----------|---------|
| DeepSeek | ✅ | ✅ | ✅ | ❌ 需外部 | ✅ R1 |
| OpenRouter | ✅ | ✅ | ✅ | ✅ | ✅ |
| Claude | ✅ | ✅ | ⚠️ JSON Mode | ❌ 需外部 | ❌ |
| Gemini | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| 智谱AI | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| 阿里云 | ✅ | ✅ | ✅ | ✅ | ⚠️ QwQ |
| SiliconFlow | ✅ | ✅ | ✅ | ✅ | ✅ R1 |
| LM Studio | ✅ | ⚠️ | ⚠️ | ✅ 本地 | ⚠️ |
| Zenmux | ✅ | ✅ | ✅ | ✅ 聚合 | ✅ |

✅ = 完全支持 | ⚠️ = 部分支持/需验证 | ❌ = 不支持
