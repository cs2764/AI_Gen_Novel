# 方案3: 增量式记忆摘要
# Strategy 3: Incremental Memory Summarization

**优先级**: ⭐⭐⭐⭐ 高 | **实施复杂度**: 低-中 | **预期Token节省**: 15-20%

---

## 概述

实现层次化的记忆压缩系统，将章节摘要、阶段摘要、全局主线分层管理，避免记忆无限膨胀。

```
层级1: 章节级摘要 (100-200字/章)
  ↓ 每5章压缩
层级2: 阶段级摘要 (200-400字/5章)
  ↓ 每20章压缩
层级3: 全局主线记忆 (500-800字/全书)
```

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **基础对话** | ✅ 必需 | 用于生成摘要 |
| **摘要能力** | ✅ 必需 | 所有现代模型都支持 |
| **长上下文** | ❌ 可选 | 层次化设计降低了对长上下文的依赖 |

> [!NOTE]
> 此方案**对模型能力无特殊要求**，所有提供商均可使用。

---

## 提供商兼容性

| 提供商 | 兼容性 | 摘要质量 | 说明 |
|-------|-------|---------|-----|
| DeepSeek | ✅ 完全兼容 | ⭐⭐⭐⭐⭐ | 推荐，摘要质量高 |
| OpenRouter | ✅ 完全兼容 | ⭐⭐⭐⭐⭐ | 取决于选择的模型 |
| Claude | ✅ 完全兼容 | ⭐⭐⭐⭐⭐ | 优秀的摘要能力 |
| Gemini | ✅ 完全兼容 | ⭐⭐⭐⭐ | 良好 |
| 智谱AI | ✅ 完全兼容 | ⭐⭐⭐⭐ | 中文摘要优化 |
| 阿里云 | ✅ 完全兼容 | ⭐⭐⭐⭐ | Qwen摘要能力强 |
| Fireworks | ✅ 完全兼容 | ⭐⭐⭐⭐ | 快速 |
| Grok | ✅ 完全兼容 | ⭐⭐⭐ | 一般 |
| Lambda | ✅ 完全兼容 | ⭐⭐⭐⭐ | 低成本 |
| SiliconFlow | ✅ 完全兼容 | ⭐⭐⭐⭐ | 国内推荐 |
| LM Studio | ✅ 完全兼容 | ⭐⭐⭐-⭐⭐⭐⭐ | 取决于本地模型 |

---

## 实现方案

```python
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class HierarchicalMemory:
    """层次化记忆系统"""
    
    # 章节级摘要 (每章100-200字)
    chapter_summaries: Dict[int, str] = field(default_factory=dict)
    
    # 阶段级摘要 (每5章合并为200-400字)
    arc_summaries: Dict[str, str] = field(default_factory=dict)  # "arc_1", "arc_2"...
    
    # 全局主线 (500-800字)
    global_summary: str = ""
    
    # 配置
    chapters_per_arc: int = 5
    arcs_per_global: int = 4
    
    def add_chapter_summary(self, chapter_num: int, content: str, summary_agent):
        """添加章节摘要"""
        # 生成章节摘要
        summary = summary_agent.summarize(content, max_length=200)
        self.chapter_summaries[chapter_num] = summary
        
        # 检查是否需要生成阶段摘要
        arc_num = (chapter_num - 1) // self.chapters_per_arc
        arc_key = f"arc_{arc_num}"
        
        if chapter_num % self.chapters_per_arc == 0:
            self._generate_arc_summary(arc_key, summary_agent)
        
        # 检查是否需要更新全局摘要
        if len(self.arc_summaries) > 0 and len(self.arc_summaries) % self.arcs_per_global == 0:
            self._update_global_summary(summary_agent)
    
    def _generate_arc_summary(self, arc_key: str, summary_agent):
        """生成阶段摘要"""
        arc_num = int(arc_key.split('_')[1])
        start_chapter = arc_num * self.chapters_per_arc + 1
        end_chapter = start_chapter + self.chapters_per_arc
        
        # 收集该阶段的章节摘要
        chapter_contents = []
        for ch in range(start_chapter, end_chapter):
            if ch in self.chapter_summaries:
                chapter_contents.append(f"第{ch}章: {self.chapter_summaries[ch]}")
        
        combined = "\n".join(chapter_contents)
        self.arc_summaries[arc_key] = summary_agent.summarize(combined, max_length=400)
    
    def _update_global_summary(self, summary_agent):
        """更新全局摘要"""
        all_arcs = "\n\n".join([
            f"{k}: {v}" for k, v in sorted(self.arc_summaries.items())
        ])
        self.global_summary = summary_agent.summarize(all_arcs, max_length=800)
    
    def get_memory_for_chapter(self, current_chapter: int) -> str:
        """获取适合当前章节的记忆上下文"""
        memory_parts = []
        
        # 1. 全局主线 (始终包含)
        if self.global_summary:
            memory_parts.append(f"【全局主线】\n{self.global_summary}")
        
        # 2. 当前阶段摘要
        current_arc = (current_chapter - 1) // self.chapters_per_arc
        arc_key = f"arc_{current_arc - 1}"  # 前一个完成的阶段
        if arc_key in self.arc_summaries:
            memory_parts.append(f"【近期剧情】\n{self.arc_summaries[arc_key]}")
        
        # 3. 最近3章的详细摘要
        recent_chapters = []
        for ch in range(max(1, current_chapter - 3), current_chapter):
            if ch in self.chapter_summaries:
                recent_chapters.append(f"第{ch}章: {self.chapter_summaries[ch]}")
        
        if recent_chapters:
            memory_parts.append(f"【最近章节】\n" + "\n".join(recent_chapters))
        
        return "\n\n".join(memory_parts)
    
    def estimate_tokens(self) -> Dict[str, int]:
        """估算当前记忆的Token消耗"""
        return {
            'global': len(self.global_summary) // 2,  # 粗略估算
            'arc': sum(len(v) for v in self.arc_summaries.values()) // 2,
            'chapter': sum(len(v) for v in self.chapter_summaries.values()) // 2,
        }
```

---

## 预期效果

| 章节数 | 当前记忆Token | 层次化后 | 节省 |
|-------|-------------|---------|-----|
| 10章 | 1500 | 800 | 47% |
| 30章 | 2000 | 1000 | 50% |
| 50章 | 2000 | 1100 | 45% |
| 100章 | 2000 | 1200 | 40% |

> [!TIP]
> 层次化记忆的主要优势是**记忆不会无限增长**，始终保持可控的Token消耗。

---

## 实施步骤

1. **修改文件**: `aign_memory_manager.py`
2. **替换类**: `MemoryManager` → `HierarchicalMemory`
3. **修改调用**: 更新 `AIGN.py` 中的记忆获取逻辑
4. **迁移**: 为现有项目提供数据迁移脚本

**预估工作量**: 4-6天
