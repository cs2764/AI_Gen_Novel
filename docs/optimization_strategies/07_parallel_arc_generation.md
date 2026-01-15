# 基于剧情弧的并行章节生成方案
# Parallel Chapter Generation Based on Story Arcs

**文档版本**: 1.0  
**创建日期**: 2025-12-23  
**状态**: 可行性研究报告

---

## 执行摘要

本方案提出一种创新的并行章节生成方法：**将整部小说按剧情弧（Arc）分割成多个相对独立的部分，然后并行生成不同部分的章节，最后拼接合并**。

### 核心优势

| 指标 | 当前线性生成 | 并行弧生成（预估）|
|-----|------------|------------------|
| 100章生成时间 | ~10小时 | ~2-3小时 |
| API并发度 | 1 | 3-5 |
| 质量风险 | 低 | 中等（需额外设计）|

---

## 方案B：生成-润色分离并行策略（推荐优先实施）

> [!TIP]
> 这是一个**更简单、更低风险**的并行化方案，建议优先考虑实施。

### 核心思想

将每章的**正文生成**和**润色**完全分离成两个独立阶段：

```
当前流程（严格线性）：
章节1(生成→润色) → 章节2(生成→润色) → 章节3(生成→润色) → ...

优化后流程（分离并行）：
┌─────────────────────────────────────────────────────────────────┐
│ 阶段1：并行初稿生成                                              │
│   章节1初稿 ─────→                                               │
│   章节2初稿 ─────→  → 所有初稿完成                               │
│   章节3初稿 ─────→                                               │
│   ...              （可同时生成N章）                             │
├─────────────────────────────────────────────────────────────────┤
│ 阶段2：顺序/智能并行润色                                          │
│   章节1润色 → 章节2润色 → 章节3润色 → ...                        │
│             （考虑上一章结尾与当前章开头的过渡）                   │
└─────────────────────────────────────────────────────────────────┘
```

### 为什么生成可以并行？

分析当前代码后发现，**初稿生成的核心依赖是故事线**（`plot_summary`, `plot_segments`），而非前一章的实际内容：

```python
# aign_chapter_manager.py 中的关键输入
inputs = {
    "本章故事线": str(current_chapter_storyline),  # 主要依赖 ✓
    "前2章故事线": compact_prev_storyline,         # 故事线预知 ✓
    "后2章故事线": compact_next_storyline,         # 故事线预知 ✓
    "大纲": current_outline,                       # 全局信息 ✓
    "前文记忆": writing_memory,                    # 可从故事线推断
}
```

由于故事线是预先生成的，**每章的初稿理论上可以独立生成**。

### 为什么润色需要考虑顺序？

润色时需要确保章节之间的过渡自然：

```python
# 润色需要的上下文
embellish_inputs = {
    "要润色的内容": next_paragraph,        # 本章初稿
    "上一章原文": prev_chapter_content,    # 需要前一章润色后的结果
    # 用于检查：开头是否与上一章结尾衔接
}
```

### 实施方案

```python
class DecoupledParallelGenerator:
    """生成-润色分离的并行生成器"""
    
    def __init__(self, aign_instance, max_concurrent_drafts=5):
        self.aign = aign_instance
        self.max_concurrent = max_concurrent_drafts
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_drafts)
    
    def generate_novel(self, start_chapter, end_chapter):
        """
        两阶段生成整部小说
        """
        # ═══════════════════════════════════════════════════════
        # 阶段1：并行生成所有初稿
        # ═══════════════════════════════════════════════════════
        print("📝 阶段1：并行生成初稿...")
        drafts = self._parallel_draft_generation(start_chapter, end_chapter)
        
        # ═══════════════════════════════════════════════════════
        # 阶段2：顺序润色（或智能并行润色）
        # ═══════════════════════════════════════════════════════
        print("✨ 阶段2：润色处理...")
        polished = self._sequential_polish(drafts)
        
        return polished
    
    def _parallel_draft_generation(self, start, end):
        """并行生成初稿"""
        futures = {}
        
        for chapter_num in range(start, end + 1):
            future = self.executor.submit(
                self._generate_single_draft,
                chapter_num
            )
            futures[chapter_num] = future
        
        # 收集结果
        drafts = {}
        for chapter_num, future in futures.items():
            drafts[chapter_num] = future.result()
            print(f"  ✓ 第{chapter_num}章初稿完成")
        
        return drafts
    
    def _generate_single_draft(self, chapter_num):
        """生成单章初稿（不含润色）"""
        storyline = self.aign.getCurrentChapterStoryline(chapter_num)
        
        # 构建精简上下文（仅基于故事线）
        context = {
            "本章故事线": storyline,
            "前后故事线": self._get_nearby_storylines(chapter_num),
            "大纲": self.aign.getCurrentOutline(),
            "人物列表": self.aign.character_list,
        }
        
        # 调用写作Agent生成初稿
        draft = self.aign.novel_writer.invoke(
            inputs=context,
            output_keys=["段落", "计划", "临时设定"]
        )
        
        return draft
    
    def _sequential_polish(self, drafts):
        """顺序润色，确保章节过渡自然"""
        polished_chapters = {}
        prev_chapter_ending = ""
        
        for chapter_num in sorted(drafts.keys()):
            draft = drafts[chapter_num]
            
            # 润色时传入上一章结尾用于衔接检查
            polish_context = {
                "要润色的内容": draft["段落"],
                "上一章结尾": prev_chapter_ending,  # 关键：过渡检查
                "本章故事线": self.aign.getCurrentChapterStoryline(chapter_num),
            }
            
            polished = self.aign.novel_embellisher.invoke(
                inputs=polish_context,
                output_keys=["润色内容"]
            )
            
            polished_chapters[chapter_num] = polished["润色内容"]
            prev_chapter_ending = polished["润色内容"][-500:]  # 保留结尾用于下一章
            
            print(f"  ✓ 第{chapter_num}章润色完成")
        
        return polished_chapters
```

### 进阶：智能并行润色

对于相隔较远的章节，润色也可以并行（因为它们之间不需要过渡）：

```python
def _smart_parallel_polish(self, drafts):
    """智能并行润色：相邻章节顺序，间隔章节并行"""
    
    # 策略：将章节分组，组内并行，组间有序
    # 例如：[1,4,7,10] 可并行，[2,5,8] 可并行，[3,6,9] 可并行
    # 但 1→2→3 必须顺序（处理过渡）
    
    stride = 3  # 间隔3章以上可并行
    
    for offset in range(stride):
        # 同一批次的章节可以并行
        batch = [ch for ch in sorted(drafts.keys()) if ch % stride == offset]
        
        # 批次内并行润色
        futures = {}
        for chapter_num in batch:
            future = self.executor.submit(
                self._polish_with_boundary,
                chapter_num,
                drafts[chapter_num],
                self._get_prev_polished_ending(chapter_num)
            )
            futures[chapter_num] = future
        
        # 等待批次完成
        for chapter_num, future in futures.items():
            self.polished_cache[chapter_num] = future.result()
```

### 与方案A（弧并行）的对比

| 维度 | 方案A：弧并行 | 方案B：生成-润色分离（推荐）|
|------|-------------|---------------------------|
| 实现复杂度 | 高 | **低** |
| 对故事线的改动 | 大（需要弧边界状态）| **无** |
| 质量风险 | 中（边界衔接）| **低**（顺序润色保证过渡）|
| 并发度 | 3-5弧 | **5-10章**（初稿阶段）|
| 时间节省（100章）| 65% | **50-60%** |
| 开发周期 | 4-8周 | **1-2周** |

### 实施建议

> [!IMPORTANT]
> **建议先实施方案B**，获得快速收益后，再考虑方案A进一步优化。

**Phase 1（1周）**：
1. 修改 `aign_chapter_manager.py`，分离 `generate_draft()` 和 `polish_chapter()`
2. 创建 `decoupled_parallel_generator.py`
3. 实现并行初稿生成

**Phase 2（1周）**：
1. 实现顺序润色流程
2. 添加润色时的过渡检查
3. UI集成和测试

---

## 当前系统分析

### 现有架构

当前的章节生成流程是**严格线性**的：

```
章节1 → 章节2 → 章节3 → ... → 章节N
   ↓        ↓        ↓
 （依赖上一章内容，前5章总结，后5章梗概）
```

#### 关键文件

| 文件 | 职责 | 关键依赖 |
|------|------|----------|
| [aign_chapter_manager.py](file:///f:/AI_Gen_Novel2/aign_chapter_manager.py) | 章节生成 | 依赖前5章总结、上一章原文 |
| [aign_storyline_manager.py](file:///f:/AI_Gen_Novel2/aign_storyline_manager.py) | 故事线生成 | 前置章节故事线上下文 |
| [dynamic_plot_structure.py](file:///f:/AI_Gen_Novel2/dynamic_plot_structure.py) | 剧情结构计算 | **已支持多段式/多高潮结构** |

### 章节依赖分析

当前每章生成时需要的上下文（来自 `get_enhanced_context` 方法）：

```python
context = {
    "prev_chapters_summary": "",    # 前5章总结
    "next_chapters_outline": "",    # 后5章梗概  
    "last_chapter_content": ""      # 上一章原文
}
```

**关键发现**：这些依赖是跨章节的，但如果重新设计故事线，可以在**弧边界处减少依赖**。

### 现有剧情结构

`dynamic_plot_structure.py` 已经实现了剧情弧分割：

```python
# 超长篇（60章以上）的结构示例
{
    "type": "多高潮史诗结构（5个发展阶段 + 5个高潮）",
    "stages": [
        {"name": "史诗开篇", "range": "第1-7章"},
        {"name": "发展阶段1", "range": "第8-17章"},
        {"name": "第1高潮", "range": "第18-21章"},
        {"name": "发展阶段2", "range": "第22-31章"},
        {"name": "第2高潮", "range": "第32-35章"},
        # ... 更多阶段
        {"name": "史诗收官", "range": "第96-100章"}
    ]
}
```

---

## 并行弧生成方案设计

### 核心思路

```
传统方式：
  弧1 ──────────────────→ 弧2 ──────────────────→ 弧3

并行方式：
  弧1 (章节1-25) ─────→
  弧2 (章节26-50) ────→  → 合并 → 最终小说
  弧3 (章节51-75) ────→
  弧4 (章节76-100) ───→
```

### 阶段一：增强故事线生成

为支持并行生成，需要升级故事线结构，使其包含**弧边界信息**和**跨弧上下文**：

```python
enhanced_storyline = {
    "arcs": [
        {
            "arc_id": 1,
            "arc_name": "史诗开篇 + 发展阶段1 + 第1高潮",
            "chapter_range": [1, 25],
            "arc_summary": "主角觉醒，初步成长，完成第一个重大目标",
            "entry_state": None,  # 第一弧无前置状态
            "exit_state": {
                "character_states": {"主角": "觉醒完成，实力初显"},
                "world_state": "第一个敌人被击败",
                "active_plotlines": ["主线1进行中", "暗线A埋下伏笔"],
                "last_chapter_summary": "第25章结尾摘要..."
            },
            "chapters": [
                {"chapter_number": 1, "plot_summary": "...", ...},
                # ... 章节1-25的详细故事线
            ]
        },
        {
            "arc_id": 2,
            "arc_name": "发展阶段2 + 第2高潮",
            "chapter_range": [26, 50],
            "arc_summary": "进入更大舞台，面对更强对手",
            "entry_state": {
                # 从弧1的exit_state自动继承
                "character_states": {"主角": "觉醒完成，实力初显"},
                "world_state": "第一个敌人被击败",
                "active_plotlines": ["主线1进行中", "暗线A需要承接"]
            },
            "exit_state": {...},
            "chapters": [...]
        }
    ],
    "global_context": {
        "world_setting": "世界观核心设定",
        "character_registry": "主要角色档案",
        "timeline": "时间线关键点"
    }
}
```

### 阶段二：并行生成引擎

```python
class ParallelArcGenerator:
    """并行弧生成器"""
    
    def __init__(self, aign_instance, max_concurrent_arcs=3):
        self.aign = aign_instance
        self.max_concurrent = max_concurrent_arcs
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_arcs)
    
    async def generate_novel_parallel(self, enhanced_storyline):
        """
        并行生成整部小说
        
        策略：
        1. 同时启动多个弧的生成
        2. 每个弧的第一章使用 entry_state 作为上下文
        3. 弧内部保持线性生成
        4. 所有弧完成后进行合并和边界润色
        """
        arcs = enhanced_storyline["arcs"]
        global_context = enhanced_storyline["global_context"]
        
        # 并行生成各个弧
        tasks = []
        for arc in arcs:
            task = self.executor.submit(
                self._generate_arc,
                arc,
                global_context
            )
            tasks.append((arc["arc_id"], task))
        
        # 收集结果
        arc_results = {}
        for arc_id, task in tasks:
            arc_results[arc_id] = task.result()
        
        # 合并并处理边界
        return self._merge_arcs(arc_results)
    
    def _generate_arc(self, arc, global_context):
        """生成单个弧的所有章节"""
        arc_content = []
        
        for chapter_data in arc["chapters"]:
            chapter_num = chapter_data["chapter_number"]
            
            # 构建上下文
            if chapter_num == arc["chapter_range"][0]:
                # 弧的第一章：使用 entry_state
                context = self._build_entry_context(arc, global_context)
            else:
                # 弧内部章节：使用前几章的内容
                context = self._build_internal_context(arc_content, chapter_data)
            
            # 生成章节
            chapter_content = self._generate_chapter(chapter_data, context)
            arc_content.append(chapter_content)
        
        return arc_content
    
    def _merge_arcs(self, arc_results):
        """合并各弧内容，处理边界衔接"""
        merged_content = []
        
        # 按弧ID顺序合并
        for arc_id in sorted(arc_results.keys()):
            arc_chapters = arc_results[arc_id]
            
            # 边界处理（可选：对弧边界的章节进行额外润色）
            if arc_id > 1:
                # 获取前一弧的最后一章和当前弧的第一章
                prev_last = merged_content[-1] if merged_content else None
                curr_first = arc_chapters[0]
                
                # 边界润色（确保衔接自然）
                if prev_last:
                    arc_chapters[0] = self._polish_arc_boundary(
                        prev_last, curr_first
                    )
            
            merged_content.extend(arc_chapters)
        
        return merged_content
```

### 阶段三：边界衔接处理

弧边界是并行生成的关键挑战。需要专门的边界处理机制：

```python
class ArcBoundaryHandler:
    """弧边界处理器"""
    
    def polish_boundary(self, prev_chapter, next_chapter, connection_hints):
        """
        润色弧边界，确保衔接自然
        
        Args:
            prev_chapter: 前一弧的最后一章
            next_chapter: 当前弧的第一章
            connection_hints: 故事线中的衔接提示
        """
        prompt = f"""
        你是一位专业的小说编辑，负责检查和润色章节衔接。
        
        ## 前一章结尾：
        {prev_chapter[-500:]}
        
        ## 当前章开头：
        {next_chapter[:500]}
        
        ## 衔接要求：
        {connection_hints}
        
        请检查衔接是否自然，如需调整请输出调整后的开头段落。
        如果衔接已经自然，请直接输出"衔接自然，无需调整"。
        """
        
        return self._call_llm(prompt)
```

---

## 技术挑战与解决方案

### 挑战1：章节间一致性

**问题**：并行生成的不同弧可能产生角色行为、时间线不一致。

**解决方案**：
1. **全局上下文注入**：每个弧生成时都注入完整的角色档案和世界设定
2. **预定义状态转换**：在故事线中明确定义每个弧的入口/出口状态
3. **后处理一致性检查**：生成完成后运行一致性检查Agent

```python
class ConsistencyChecker:
    def check_cross_arc_consistency(self, all_chapters):
        """检查跨弧一致性"""
        issues = []
        
        for arc_boundary in self._find_arc_boundaries(all_chapters):
            # 检查角色状态连续性
            issues.extend(self._check_character_continuity(arc_boundary))
            # 检查时间线连续性
            issues.extend(self._check_timeline_continuity(arc_boundary))
            # 检查伏笔/呼应
            issues.extend(self._check_foreshadowing(arc_boundary))
        
        return issues
```

### 挑战2：弧边界的自然衔接

**问题**：不同弧独立生成，边界处可能出现突兀的转折或重复内容。

**解决方案**：
1. **边界润色Pass**：生成后对边界章节进行专门润色
2. **过渡章节设计**：在故事线中预留过渡缓冲（每个弧的首尾章节）
3. **显式衔接指令**：故事线包含明确的衔接要点

### 挑战3：API并发限制

**问题**：多数AI提供商有并发请求限制。

**解决方案**：
1. **智能并发控制**：根据提供商设置并发数
2. **请求队列**：实现请求排队和限流
3. **多提供商分发**：可选择将不同弧分发到不同提供商

```python
PROVIDER_CONCURRENCY = {
    "openrouter": 5,
    "deepseek": 3,
    "claude": 2,
    "lmstudio": 1,  # 本地模型建议单并发
}
```

---

## 实施路线图

### Phase 1：增强故事线生成（1-2周）

1. 扩展 `dynamic_plot_structure.py`，生成弧级别的结构
2. 修改 `aign_storyline_manager.py`，支持弧边界状态定义
3. 更新故事线JSON schema，包含 entry_state/exit_state

### Phase 2：并行生成引擎（2-3周）

1. 创建 `parallel_arc_generator.py`
2. 实现弧级别的上下文构建
3. 实现线程池并发控制
4. 集成到现有 AIGN 系统

### Phase 3：边界处理与质量保证（1-2周）

1. 实现弧边界润色器
2. 实现跨弧一致性检查
3. 添加生成后的校验流程

### Phase 4：UI集成与测试（1周）

1. Gradio UI 添加并行生成选项
2. 进度显示支持多弧并行状态
3. 完整的端到端测试

---

## 预期效果

### 时间节省

| 章节数 | 线性生成（预估）| 并行生成（3弧并发）| 节省 |
|--------|---------------|-------------------|------|
| 30章 | 3小时 | 1.2小时 | 60% |
| 60章 | 6小时 | 2.5小时 | 58% |
| 100章 | 10小时 | 3.5小时 | 65% |
| 200章 | 20小时 | 6小时 | 70% |

### 质量风险

| 风险类型 | 概率 | 缓解措施 |
|---------|------|---------|
| 弧边界衔接不自然 | 中 | 边界润色Pass |
| 角色行为不一致 | 低-中 | 全局上下文 + 一致性检查 |
| 时间线错乱 | 低 | 故事线预定义状态 |
| 伏笔/呼应断裂 | 中 | 跨弧引用机制 |

---

## 结论与建议

### 可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 技术可行性 | ⭐⭐⭐⭐☆ | 现有架构支持扩展，核心改动可控 |
| 质量保证 | ⭐⭐⭐☆☆ | 需要额外的边界处理和一致性检查 |
| 开发成本 | ⭐⭐⭐☆☆ | 预计4-8周开发时间 |
| 效果收益 | ⭐⭐⭐⭐⭐ | 显著缩短生成时间（50-70%）|

### 建议

1. **推荐实施**：对于长篇小说（60章以上），该方案收益明显
2. **渐进式开发**：建议先实现Phase 1和2，验证基本功能后再完善边界处理
3. **可选功能**：作为高级功能提供，用户可选择线性或并行模式
4. **质量兜底**：保留后处理一致性检查，必要时人工介入

---

## 附录：与现有代码的集成点

### 需要修改的文件

1. **dynamic_plot_structure.py** - 添加弧级别的详细信息
2. **aign_storyline_manager.py** - 支持增强故事线生成
3. **aign_chapter_manager.py** - 支持弧上下文模式
4. **AIGN.py** - 添加并行生成入口方法

### 新增文件

1. `parallel_arc_generator.py` - 并行生成引擎
2. `arc_boundary_handler.py` - 边界处理
3. `cross_arc_consistency_checker.py` - 一致性检查

### 配置项

```python
PARALLEL_GENERATION_CONFIG = {
    "enabled": False,  # 默认关闭
    "max_concurrent_arcs": 3,
    "boundary_polish": True,
    "consistency_check": True,
    "min_chapters_for_parallel": 30,  # 低于此章节数使用线性生成
}
```
