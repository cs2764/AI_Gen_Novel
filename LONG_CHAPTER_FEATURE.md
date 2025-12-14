# Long Chapter Feature - Technical Documentation
# 长章节功能 - 技术文档

[English](#english-documentation) | [中文文档](#中文文档)

---

## English Documentation

### Overview

The **Long Chapter Feature** is a major enhancement in v3.5.0 that improves the quality and coherence of generated chapters by splitting them into 4 narrative segments, generating each segment independently, and then merging them into a complete chapter.

### Problem Statement

**Before v3.5.0:**
- Generating long chapters (10,000+ characters) in one pass often resulted in:
  - Loss of narrative coherence in the middle/end sections
  - Repetitive content and phrasing
  - Inconsistent quality across the chapter
  - Difficulty generating very long chapters (15,000+ characters)

### Solution: Segment-Based Generation

**The 4-Segment Approach:**

```
Chapter → [Segment 1] → [Segment 2] → [Segment 3] → [Segment 4] → Merged Chapter
           ↓              ↓              ↓              ↓
        Generate       Generate       Generate       Generate
           ↓              ↓              ↓              ↓
        Polish         Polish         Polish         Polish
```

### How It Works

#### 1. Storyline Preparation

When generating storylines, the system creates 4 plot segments for each chapter:

```python
{
  "chapter_number": 5,
  "chapter_title": "The Awakening",
  "plot_segments": [
    {
      "index": 1,
      "segment_title": "Morning Discovery",
      "segment_summary": "Protagonist discovers mysterious artifact..."
    },
    {
      "index": 2,
      "segment_title": "Investigation Begins",
      "segment_summary": "Research into artifact's origins..."
    },
    {
      "index": 3,
      "segment_title": "Unexpected Visitor",
      "segment_summary": "Stranger arrives with warnings..."
    },
    {
      "index": 4,
      "segment_title": "Decision Point",
      "segment_summary": "Protagonist must choose path forward..."
    }
  ]
}
```

#### 2. Segment Generation Process

For each of the 4 segments:

**Step 1: Context Preparation**
- Current segment details (title + summary)
- Reference to other 3 segments (for coherence)
- Previous 2 chapters' summaries (not full text)
- Next 2 chapters' outlines
- Writing memory, temporary settings, and plans

**Step 2: Content Generation**
```python
# Specialized agent for each segment
writer_agent = novel_writer_compact_seg{1-4}

inputs = {
    "大纲": current_outline,
    "写作要求": user_requirements,
    "前文记忆": writing_memory,
    "临时设定": temp_setting,
    "计划": writing_plan,
    "本章故事线": current_chapter_storyline,
    "本章分段（参考）": other_segments_summary,
    "当前分段": current_segment_details,
    "前2章故事线": prev_2_chapters_summary,
    "后2章故事线": next_2_chapters_outline
}

segment_text = writer_agent.invoke(inputs)
```

**Step 3: Segment Polishing**
```python
# Specialized embellisher for each segment
embellisher_agent = novel_embellisher_compact_seg{1-4}

polished_segment = embellisher_agent.invoke({
    "原始内容": segment_text,
    "详细大纲": detailed_outline,
    "润色要求": embellishment_requirements,
    "前2章故事线": prev_2_chapters_summary,
    "后2章故事线": next_2_chapters_outline
})
```

**Step 4: Merge Segments**
```python
complete_chapter = "\n\n".join([
    polished_segment_1,
    polished_segment_2,
    polished_segment_3,
    polished_segment_4
])
```

#### 3. Token Optimization

**Key Optimization: Summary-Only Context**

Instead of sending full chapter text (which can be 10,000+ characters each), the system only sends:
- **Previous 2 chapters**: Summaries only (~500 characters each)
- **Next 2 chapters**: Outlines only (~300 characters each)

**Context Optimization:**
```
Traditional approach:
- Previous 5 chapters full text: ~50,000 characters
- Next 5 chapters outlines: ~1,500 characters
- Total context: ~51,500 characters

Long Chapter Mode:
- Previous 2 chapters summaries: ~1,000 characters
- Next 2 chapters outlines: ~600 characters
- Total context: ~1,600 characters

Result: More manageable context size, enabling longer chapter generation
```

### Implementation Details

#### Core Components

**1. Mode Flag**
```python
# AIGN.py
self.long_chapter_mode = True  # Default enabled
```

**2. UI Control**
```python
# app.py / app_ui_components.py
long_chapter_feature_checkbox = gr.Checkbox(
    label="长章节功能（分4段生成并合并）",
    value=True,
    info="开启后：每章拆分为4个剧情段，逐段生成与润色，最后自动合并为完整一章"
)
```

**3. Segment Detection**
```python
# AIGN.py - genNextParagraph()
enable_segment_mode = bool(getattr(self, 'long_chapter_mode', True))
current_story = self.getCurrentChapterStoryline(self.chapter_count + 1)
story_segments = current_story.get('plot_segments', [])

if enable_segment_mode and len(story_segments) >= 4:
    # Use segment-based generation
    for seg_index in range(1, 5):
        # Generate each segment
        pass
else:
    # Fall back to traditional single-pass generation
    pass
```

**4. Specialized Agents**

The system uses specialized agents for each segment:
- `novel_writer_compact_seg1` through `novel_writer_compact_seg4`
- `novel_embellisher_compact_seg1` through `novel_embellisher_compact_seg4`

These agents have the same prompts but are tracked separately for better debugging and token statistics.

#### Batch Size Adjustment

When long chapter mode is enabled, the storyline generator automatically reduces batch size:

```python
# aign_storyline_manager.py
if getattr(self.aign, 'long_chapter_mode', True) and chapters_per_batch == 10:
    chapters_per_batch = 5
    print("📦 长章节模式启用：将每批章节数调整为 5")
```

**Reason:** Generating 4-segment storylines requires more tokens per chapter, so processing fewer chapters per batch prevents API timeouts.

### Benefits

#### 1. Quality Improvements
- ✅ **Better Coherence**: Each segment maintains focus on its specific plot point
- ✅ **Reduced Repetition**: Shorter generation contexts reduce repetitive patterns
- ✅ **Consistent Quality**: Each segment receives equal attention and polishing
- ✅ **Smoother Transitions**: Segments are aware of each other through reference summaries

#### 2. Performance Optimization
- ✅ **Longer Chapters**: Enables generation of much longer chapters (15,000+ characters)
- ✅ **Better Context Management**: Summary-only context keeps requests manageable
- ✅ **Improved Reliability**: Smaller per-segment requests less likely to timeout
- ✅ **Efficient Processing**: Parallel-ready architecture for future optimization

#### 3. Flexibility
- ✅ **Toggleable**: Can be enabled/disabled per generation
- ✅ **Persistent**: Setting saved with project data
- ✅ **Backward Compatible**: Falls back to traditional mode if storyline lacks segments

### Usage

#### Enable/Disable

**In UI:**
1. Check/uncheck "长章节功能（分4段生成并合并）" checkbox
2. Setting applies to current and future generations

**In Code:**
```python
aign.long_chapter_mode = True  # Enable
aign.long_chapter_mode = False  # Disable
```

#### Requirements

For segment-based generation to activate:
1. `long_chapter_mode` must be `True`
2. Current chapter must have a storyline with 4+ segments
3. Segments must have `index`, `segment_title`, and `segment_summary` fields

If requirements aren't met, system automatically falls back to traditional single-pass generation.

### Technical Considerations

#### Memory Management

Each segment generation updates:
- `writing_plan`: Carried forward to next segment
- `temp_setting`: Accumulated across segments
- `writing_memory`: Updated after chapter completion

#### Error Handling

If a segment fails:
- Error is logged with segment index
- Generation continues with next segment (if possible)
- Partial results are preserved

#### Token Statistics

Token usage is tracked separately for each segment:
```
📊 Token统计 - 第5章
  分段1生成: 发送 2,500 tokens, 接收 3,200 tokens
  分段1润色: 发送 3,500 tokens, 接收 3,400 tokens
  分段2生成: 发送 2,600 tokens, 接收 3,100 tokens
  ...
```

---

## 中文文档

### 概述

**长章节功能**是v3.5.0的重大增强，通过将章节拆分为4个叙事段落，独立生成每个段落，然后合并为完整章节，从而提升生成章节的质量和连贯性。

### 问题背景

**v3.5.0之前：**
- 一次性生成长章节（10,000+字符）经常导致：
  - 中后段叙事连贯性丧失
  - 内容和措辞重复
  - 章节质量不一致
  - 难以生成超长章节（15,000+字符）

### 解决方案：基于分段的生成

**4段式方法：**

```
章节 → [分段1] → [分段2] → [分段3] → [分段4] → 合并章节
        ↓         ↓         ↓         ↓
      生成      生成      生成      生成
        ↓         ↓         ↓         ↓
      润色      润色      润色      润色
```

### 工作原理

#### 1. 故事线准备

生成故事线时，系统为每章创建4个剧情分段：

```python
{
  "chapter_number": 5,
  "chapter_title": "觉醒",
  "plot_segments": [
    {
      "index": 1,
      "segment_title": "清晨发现",
      "segment_summary": "主角发现神秘文物..."
    },
    {
      "index": 2,
      "segment_title": "调查开始",
      "segment_summary": "研究文物来源..."
    },
    {
      "index": 3,
      "segment_title": "不速之客",
      "segment_summary": "陌生人带来警告..."
    },
    {
      "index": 4,
      "segment_title": "抉择时刻",
      "segment_summary": "主角必须选择前进道路..."
    }
  ]
}
```

#### 2. 分段生成流程

对于4个分段中的每一个：

**步骤1：上下文准备**
- 当前分段详情（标题+摘要）
- 其他3个分段的参考（保持连贯性）
- 前2章的摘要（非全文）
- 后2章的大纲
- 写作记忆、临时设定和计划

**步骤2：内容生成**
```python
# 每个分段使用专门的智能体
writer_agent = novel_writer_compact_seg{1-4}

inputs = {
    "大纲": 当前大纲,
    "写作要求": 用户要求,
    "前文记忆": 写作记忆,
    "临时设定": 临时设定,
    "计划": 写作计划,
    "本章故事线": 本章故事线,
    "本章分段（参考）": 其他分段摘要,
    "当前分段": 当前分段详情,
    "前2章故事线": 前2章摘要,
    "后2章故事线": 后2章大纲
}

segment_text = writer_agent.invoke(inputs)
```

**步骤3：分段润色**
```python
# 每个分段使用专门的润色器
embellisher_agent = novel_embellisher_compact_seg{1-4}

polished_segment = embellisher_agent.invoke({
    "原始内容": segment_text,
    "详细大纲": 详细大纲,
    "润色要求": 润色要求,
    "前2章故事线": 前2章摘要,
    "后2章故事线": 后2章大纲
})
```

**步骤4：合并分段**
```python
complete_chapter = "\n\n".join([
    polished_segment_1,
    polished_segment_2,
    polished_segment_3,
    polished_segment_4
])
```

#### 3. Token优化

**关键优化：仅使用摘要上下文**

不发送完整章节文本（每章可能10,000+字符），系统仅发送：
- **前2章**：仅摘要（每章约500字符）
- **后2章**：仅大纲（每章约300字符）

**上下文优化：**
```
传统方法：
- 前5章全文：约50,000字符
- 后5章大纲：约1,500字符
- 总上下文：约51,500字符

长章节模式：
- 前2章摘要：约1,000字符
- 后2章大纲：约600字符
- 总上下文：约1,600字符

结果：更可控的上下文大小，支持生成更长章节
```

### 实现细节

#### 核心组件

**1. 模式标志**
```python
# AIGN.py
self.long_chapter_mode = True  # 默认启用
```

**2. UI控制**
```python
# app.py / app_ui_components.py
long_chapter_feature_checkbox = gr.Checkbox(
    label="长章节功能（分4段生成并合并）",
    value=True,
    info="开启后：每章拆分为4个剧情段，逐段生成与润色，最后自动合并为完整一章"
)
```

**3. 分段检测**
```python
# AIGN.py - genNextParagraph()
enable_segment_mode = bool(getattr(self, 'long_chapter_mode', True))
current_story = self.getCurrentChapterStoryline(self.chapter_count + 1)
story_segments = current_story.get('plot_segments', [])

if enable_segment_mode and len(story_segments) >= 4:
    # 使用分段生成
    for seg_index in range(1, 5):
        # 生成每个分段
        pass
else:
    # 回退到传统单次生成
    pass
```

**4. 专门智能体**

系统为每个分段使用专门的智能体：
- `novel_writer_compact_seg1` 到 `novel_writer_compact_seg4`
- `novel_embellisher_compact_seg1` 到 `novel_embellisher_compact_seg4`

这些智能体使用相同的提示词，但分别追踪以便更好地调试和统计Token。

#### 批次大小调整

启用长章节模式时，故事线生成器自动减少批次大小：

```python
# aign_storyline_manager.py
if getattr(self.aign, 'long_chapter_mode', True) and chapters_per_batch == 10:
    chapters_per_batch = 5
    print("📦 长章节模式启用：将每批章节数调整为 5")
```

**原因：**生成4段式故事线每章需要更多Token，处理更少章节可防止API超时。

### 优势

#### 1. 质量提升
- ✅ **更好的连贯性**：每个分段专注于特定情节点
- ✅ **减少重复**：更短的生成上下文减少重复模式
- ✅ **质量一致**：每个分段获得同等关注和润色
- ✅ **过渡流畅**：分段通过参考摘要相互感知

#### 2. 性能优化
- ✅ **更长章节**：支持生成更长的章节（15,000+字符）
- ✅ **更好的上下文管理**：仅摘要上下文保持请求可控
- ✅ **更高可靠性**：更小的分段请求不易超时
- ✅ **高效处理**：为未来并行优化做好准备的架构

#### 3. 灵活性
- ✅ **可切换**：每次生成可启用/禁用
- ✅ **持久化**：设置随项目数据保存
- ✅ **向后兼容**：故事线缺少分段时回退到传统模式

### 使用方法

#### 启用/禁用

**在UI中：**
1. 勾选/取消勾选"长章节功能（分4段生成并合并）"复选框
2. 设置应用于当前和未来的生成

**在代码中：**
```python
aign.long_chapter_mode = True  # 启用
aign.long_chapter_mode = False  # 禁用
```

#### 要求

分段生成激活的条件：
1. `long_chapter_mode` 必须为 `True`
2. 当前章节必须有包含4+分段的故事线
3. 分段必须有 `index`、`segment_title` 和 `segment_summary` 字段

如果不满足要求，系统自动回退到传统单次生成。

### 技术考虑

#### 内存管理

每个分段生成更新：
- `writing_plan`：传递到下一分段
- `temp_setting`：跨分段累积
- `writing_memory`：章节完成后更新

#### 错误处理

如果分段失败：
- 记录带分段索引的错误
- 继续生成下一分段（如可能）
- 保留部分结果

#### Token统计

每个分段的Token使用单独追踪：
```
📊 Token统计 - 第5章
  分段1生成: 发送 2,500 tokens, 接收 3,200 tokens
  分段1润色: 发送 3,500 tokens, 接收 3,400 tokens
  分段2生成: 发送 2,600 tokens, 接收 3,100 tokens
  ...
```

---

**Last Updated**: 2025-11-05  
**Version**: 3.5.0
