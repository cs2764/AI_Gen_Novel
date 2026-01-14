# 方案1: 智能上下文压缩
# Strategy 1: Smart Context Compression

**优先级**: ⭐⭐⭐⭐ 高 | **实施复杂度**: 中等 | **预期Token节省**: 40-60%

---

## 概述

当前系统在 `aign_memory_manager.py` 的 `get_enhanced_context` 方法中，固定获取前5章总结和后5章梗概。本方案实现基于章节类型和情节发展的动态上下文选择。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **基础对话** | ✅ 必需 | 标准文本生成能力 |
| **长上下文** | ⚠️ 推荐 | 8K+ 上下文窗口 |
| **Function Calling** | ❌ 可选 | 可提升智能选择效果 |
| **Structured Output** | ❌ 可选 | 不影响核心功能 |

> [!NOTE]
> 此方案主要是代码层面的优化，**对模型能力无特殊要求**，所有提供商均可使用。

---

## 提供商兼容性

| 提供商 | 兼容性 | 特殊说明 |
|-------|-------|---------|
| DeepSeek | ✅ 完全兼容 | 推荐，性价比高 |
| OpenRouter | ✅ 完全兼容 | 多模型选择 |
| Claude | ✅ 完全兼容 | 长上下文优势 |
| Gemini | ✅ 完全兼容 | 超长上下文 |
| 智谱AI | ✅ 完全兼容 | 中文优化 |
| 阿里云 | ✅ 完全兼容 | Qwen模型 |
| Fireworks | ✅ 完全兼容 | 快速推理 |
| Grok | ✅ 完全兼容 | - |
| Lambda | ✅ 完全兼容 | 低成本 |
| SiliconFlow | ✅ 完全兼容 | 国内GPU |
| LM Studio | ✅ 完全兼容 | 本地部署 |

---

## 实现方案

```python
class SmartContextSelector:
    """根据章节位置和情节发展动态选择上下文"""
    
    CHAPTER_TYPES = {
        'climax': {'context_range': 5, 'include_foreshadowing': True},
        'transition': {'context_range': 2, 'include_foreshadowing': False},
        'development': {'context_range': 3, 'include_foreshadowing': True},
    }
    
    def select_relevant_context(self, chapter_number, storyline_data, chapter_type='development'):
        """
        基于章节类型智能选择上下文
        
        Args:
            chapter_number: 当前章节号
            storyline_data: 故事线数据
            chapter_type: 章节类型
        
        Returns:
            dict: 精选的上下文信息
        """
        config = self.CHAPTER_TYPES.get(chapter_type, self.CHAPTER_TYPES['development'])
        
        context = {
            'previous_chapters': self._get_recent_summaries(
                chapter_number, 
                config['context_range']
            ),
            'upcoming_plot': self._get_next_plot_points(
                chapter_number,
                storyline_data,
                limit=2
            ),
        }
        
        if config['include_foreshadowing']:
            context['foreshadowing'] = self._get_relevant_foreshadowing(
                chapter_number,
                storyline_data
            )
        
        return context
    
    def detect_chapter_type(self, storyline_entry):
        """自动检测章节类型"""
        keywords_climax = ['高潮', '决战', '对决', '真相', 'climax']
        keywords_transition = ['过渡', '铺垫', '准备', 'transition']
        
        content = storyline_entry.get('描述', '')
        
        for kw in keywords_climax:
            if kw in content.lower():
                return 'climax'
        for kw in keywords_transition:
            if kw in content.lower():
                return 'transition'
        
        return 'development'
```

---

## 预期效果

| 指标 | 当前 | 优化后 | 节省 |
|-----|-----|-------|-----|
| 上下文Token (过渡章节) | 8000 | 3000 | 62.5% |
| 上下文Token (普通章节) | 8000 | 5000 | 37.5% |
| 上下文Token (高潮章节) | 8000 | 7000 | 12.5% |
| **加权平均** | 8000 | 4500 | **43.8%** |

---

## 实施步骤

1. **修改文件**: `aign_memory_manager.py`
2. **新增类**: `SmartContextSelector`
3. **修改方法**: `get_enhanced_context()` 调用智能选择器
4. **测试**: 对比不同章节类型的生成质量

**预估工作量**: 1-2周
