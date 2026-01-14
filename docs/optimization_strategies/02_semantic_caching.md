# 方案2: 语义缓存系统
# Strategy 2: Semantic Caching System

**优先级**: ⭐⭐⭐ 中 | **实施复杂度**: 中等 | **预期Token节省**: 15-25%

---

## 概述

实现基于语义相似度的缓存系统，对于重复传递的大纲、人物设定等静态内容进行缓存复用，避免每次生成都重新构建完整提示词。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **基础对话** | ✅ 必需 | 标准文本生成能力 |
| **Embedding API** | ⚠️ 推荐 | 用于语义相似度计算 |
| **长上下文** | ❌ 可选 | 缓存可减少上下文需求 |

> [!NOTE]
> 此方案需要 **Embedding API** 支持，或使用本地轻量级嵌入模型。

---

## 提供商兼容性

| 提供商 | Embedding支持 | 兼容性 | 说明 |
|-------|-------------|-------|-----|
| DeepSeek | ❌ 无 | ⚠️ 需外部Embedding | 可用OpenAI Embedding替代 |
| OpenRouter | ✅ 有 | ✅ 完全兼容 | 支持多种Embedding模型 |
| Claude | ❌ 无 | ⚠️ 需外部Embedding | 可用Voyage AI替代 |
| Gemini | ✅ 有 | ✅ 完全兼容 | text-embedding-004 |
| 智谱AI | ✅ 有 | ✅ 完全兼容 | embedding-2 |
| 阿里云 | ✅ 有 | ✅ 完全兼容 | text-embedding-v2 |
| Fireworks | ✅ 有 | ✅ 完全兼容 | nomic-embed-text |
| Grok | ❌ 无 | ⚠️ 需外部Embedding | - |
| Lambda | ❌ 无 | ⚠️ 需外部Embedding | - |
| SiliconFlow | ✅ 有 | ✅ 完全兼容 | 多种Embedding模型 |
| LM Studio | ✅ 有 | ✅ 完全兼容 | 本地Embedding模型 |

### 推荐Embedding方案

对于不提供Embedding的提供商，推荐以下替代方案：

1. **OpenAI text-embedding-3-small** - 性价比最高
2. **本地 all-MiniLM-L6-v2** - 免费，通过sentence-transformers
3. **智谱AI embedding-2** - 中文优化

---

## 实现方案

```python
import hashlib
from typing import Dict, Optional
import numpy as np

class SemanticCache:
    """语义缓存系统"""
    
    def __init__(self, embedding_model=None, similarity_threshold=0.85):
        self.cache = {}  # {hash: {'content': str, 'embedding': array, 'timestamp': float}}
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
    
    def _compute_hash(self, text: str) -> str:
        """计算文本的快速哈希"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """计算文本嵌入向量"""
        if self.embedding_model:
            return self.embedding_model.encode(text)
        # 降级方案：使用简单的词频向量
        return self._simple_vectorize(text)
    
    def get_cached_or_compute(self, key: str, content: str) -> str:
        """获取缓存内容或返回原内容"""
        content_hash = self._compute_hash(content)
        
        if content_hash in self.cache:
            return self.cache[content_hash]['content']
        
        # 查找语义相似的缓存
        similar = self._find_semantically_similar(content)
        if similar:
            return similar
        
        # 存入缓存
        self._store_cache(content_hash, content)
        return content
    
    def get_compressed_reference(self, key: str, full_content: str) -> str:
        """
        获取压缩的内容引用
        
        如果内容已经被完整传递过，返回简短引用；
        否则返回完整内容并缓存。
        """
        content_hash = self._compute_hash(full_content)
        
        if content_hash in self.cache:
            # 返回简短引用
            return f"[参考已传递的{key}，ID: {content_hash[:8]}]"
        
        self._store_cache(content_hash, full_content)
        return full_content

# 使用示例
class CachedAgentContext:
    """带缓存的Agent上下文管理"""
    
    def __init__(self):
        self.cache = SemanticCache()
        self.session_transmitted = set()  # 本次会话已传递的内容
    
    def build_context(self, outline, characters, memory, storyline):
        """构建带缓存的上下文"""
        context_parts = []
        
        # 大纲：首次完整传递，后续压缩
        if 'outline' not in self.session_transmitted:
            context_parts.append(f"# 小说大纲\n{outline}")
            self.session_transmitted.add('outline')
        else:
            context_parts.append("# 小说大纲\n[已在会话开始时传递]")
        
        # 人物设定：类似处理
        if 'characters' not in self.session_transmitted:
            context_parts.append(f"# 人物设定\n{characters}")
            self.session_transmitted.add('characters')
        else:
            context_parts.append("# 人物设定\n[已在会话开始时传递]")
        
        # 记忆和故事线：每次都需要最新的
        context_parts.append(f"# 前文记忆\n{memory}")
        context_parts.append(f"# 本章故事线\n{storyline}")
        
        return "\n\n".join(context_parts)
```

---

## 预期效果

| 内容类型 | 首次传递 | 后续传递(缓存后) | 节省 |
|---------|---------|----------------|-----|
| 大纲 | 2000 tokens | 50 tokens | 97.5% |
| 人物设定 | 1500 tokens | 50 tokens | 96.7% |
| 世界观 | 1000 tokens | 50 tokens | 95% |
| **整体效果** | +4500 tokens/章 | +150 tokens/章 | **80%** (静态内容) |

> [!IMPORTANT]
> 此优化仅针对静态内容（大纲、人物、世界观）。记忆和故事线仍需每次传递。

---

## 实施步骤

1. **新增模块**: `semantic_cache.py`
2. **集成位置**: `aign_agents.py` 的上下文构建
3. **配置项**: 添加Embedding模型选择配置
4. **测试**: 验证语义匹配准确性

**预估工作量**: 1周
