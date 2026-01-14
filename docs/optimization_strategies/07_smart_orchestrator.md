# 方案7: 智能Agent协调器
# Strategy 7: Smart Agent Orchestrator

**优先级**: ⭐⭐⭐⭐ 高 | **实施复杂度**: 中 | **预期收益**: 减少30% API调用

---

## 概述

引入Meta-Agent层，智能决策何时调用哪些Agent，避免不必要的API调用。例如，简单章节可能不需要润色，稳定剧情可能不需要频繁更新记忆。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **基础对话** | ✅ 必需 | 所有生成任务 |
| **分析能力** | ⚠️ 推荐 | 用于复杂度评估 |

> [!NOTE]
> 此方案的核心是**代码层面的决策逻辑**，对模型能力无特殊要求。复杂度评估可使用规则或轻量级模型。

---

## 提供商兼容性

| 提供商 | 兼容性 | 说明 |
|-------|-------|-----|
| DeepSeek | ✅ 完全兼容 | 所有功能 |
| OpenRouter | ✅ 完全兼容 | 所有功能 |
| Claude | ✅ 完全兼容 | 所有功能 |
| Gemini | ✅ 完全兼容 | 所有功能 |
| 智谱AI | ✅ 完全兼容 | 所有功能 |
| 阿里云 | ✅ 完全兼容 | 所有功能 |
| Fireworks | ✅ 完全兼容 | 所有功能 |
| Grok | ✅ 完全兼容 | 所有功能 |
| Lambda | ✅ 完全兼容 | 所有功能 |
| SiliconFlow | ✅ 完全兼容 | 所有功能 |
| LM Studio | ✅ 完全兼容 | 所有功能 |

**所有11个提供商均完全兼容。**

---

## 实现方案

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import re

class ChapterComplexity(Enum):
    LOW = "low"          # 简单过渡
    MEDIUM = "medium"    # 普通章节
    HIGH = "high"        # 复杂/高潮

class WorkflowStep(Enum):
    WRITE = "write"
    POLISH = "polish"
    LIGHT_POLISH = "light_polish"
    MEMORY_UPDATE = "memory_update"
    CONSISTENCY_CHECK = "consistency_check"

@dataclass
class ChapterAnalysis:
    """章节分析结果"""
    complexity: ChapterComplexity
    has_major_event: bool
    character_count: int
    dialogue_ratio: float
    action_intensity: float
    emotional_weight: float

class SmartOrchestrator:
    """智能协调器"""
    
    # 工作流配置
    WORKFLOWS = {
        ChapterComplexity.LOW: [
            WorkflowStep.WRITE,
            # 不润色，不更新记忆
        ],
        ChapterComplexity.MEDIUM: [
            WorkflowStep.WRITE,
            WorkflowStep.LIGHT_POLISH,
            # 条件更新记忆
        ],
        ChapterComplexity.HIGH: [
            WorkflowStep.WRITE,
            WorkflowStep.POLISH,
            WorkflowStep.MEMORY_UPDATE,
            WorkflowStep.CONSISTENCY_CHECK,
        ],
    }
    
    def __init__(self, aign_instance):
        self.aign = aign_instance
        self.chapter_history = []
    
    def analyze_chapter(self, storyline_entry: dict, 
                        chapter_number: int) -> ChapterAnalysis:
        """分析章节复杂度"""
        description = storyline_entry.get('描述', '')
        
        # 检测高潮/关键事件
        climax_keywords = ['高潮', '决战', '真相', '转折', '揭示', '对决', 
                          '告白', '死亡', '突破', '觉醒']
        has_major = any(kw in description for kw in climax_keywords)
        
        # 检测过渡场景
        transition_keywords = ['过渡', '铺垫', '日常', '休息', '准备']
        is_transition = any(kw in description for kw in transition_keywords)
        
        # 估算对话比例
        dialogue_indicators = ['对话', '交流', '讨论', '争论', '聊天']
        dialogue_ratio = sum(1 for kw in dialogue_indicators if kw in description) / 5
        
        # 估算动作强度
        action_indicators = ['战斗', '追逐', '打斗', '逃跑', '对抗']
        action_intensity = sum(1 for kw in action_indicators if kw in description) / 5
        
        # 确定复杂度
        if has_major:
            complexity = ChapterComplexity.HIGH
        elif is_transition:
            complexity = ChapterComplexity.LOW
        else:
            complexity = ChapterComplexity.MEDIUM
        
        return ChapterAnalysis(
            complexity=complexity,
            has_major_event=has_major,
            character_count=len(re.findall(r'[「」""''【】]', description)),
            dialogue_ratio=dialogue_ratio,
            action_intensity=action_intensity,
            emotional_weight=0.5 if has_major else 0.3
        )
    
    def decide_workflow(self, analysis: ChapterAnalysis) -> List[WorkflowStep]:
        """决定工作流"""
        base_workflow = self.WORKFLOWS[analysis.complexity].copy()
        
        # 动态调整
        if analysis.has_major_event and WorkflowStep.MEMORY_UPDATE not in base_workflow:
            base_workflow.append(WorkflowStep.MEMORY_UPDATE)
        
        return base_workflow
    
    def should_update_memory(self, chapter_content: str, 
                             analysis: ChapterAnalysis) -> bool:
        """判断是否需要更新记忆"""
        # 重大事件必须更新
        if analysis.has_major_event:
            return True
        
        # 每5章强制更新一次
        if len(self.chapter_history) % 5 == 0:
            return True
        
        # 内容长度超过阈值
        if len(chapter_content) > 5000:
            return True
        
        return False
    
    def should_polish(self, draft_content: str, 
                      analysis: ChapterAnalysis) -> tuple[bool, str]:
        """
        判断是否需要润色
        
        Returns:
            (是否润色, 润色类型: 'full'/'light'/'none')
        """
        if analysis.complexity == ChapterComplexity.HIGH:
            return True, 'full'
        
        if analysis.complexity == ChapterComplexity.LOW:
            return False, 'none'
        
        # 中等复杂度：检查内容质量
        quality_score = self._quick_quality_check(draft_content)
        
        if quality_score < 0.6:
            return True, 'full'
        elif quality_score < 0.8:
            return True, 'light'
        else:
            return False, 'none'
    
    def _quick_quality_check(self, content: str) -> float:
        """快速质量检查（基于规则）"""
        score = 1.0
        
        # 检查重复
        sentences = content.split('。')
        unique_ratio = len(set(sentences)) / max(len(sentences), 1)
        score *= unique_ratio
        
        # 检查长度
        if len(content) < 2000:
            score *= 0.8
        
        # 检查段落结构
        paragraphs = content.split('\n\n')
        if len(paragraphs) < 3:
            score *= 0.9
        
        return score
    
    async def execute_workflow(self, chapter_number: int, 
                               storyline_entry: dict) -> dict:
        """执行工作流"""
        # 分析章节
        analysis = self.analyze_chapter(storyline_entry, chapter_number)
        workflow = self.decide_workflow(analysis)
        
        result = {
            'analysis': analysis,
            'workflow': workflow,
            'steps_executed': [],
            'api_calls_saved': 0
        }
        
        # 执行写作
        if WorkflowStep.WRITE in workflow:
            draft = await self.aign.novel_writer.write(storyline_entry)
            result['draft'] = draft
            result['steps_executed'].append('write')
        
        # 决定是否润色
        should_polish, polish_type = self.should_polish(draft, analysis)
        if should_polish:
            if polish_type == 'full':
                result['content'] = await self.aign.embellisher.polish(draft)
                result['steps_executed'].append('full_polish')
            else:
                result['content'] = await self.aign.embellisher.light_polish(draft)
                result['steps_executed'].append('light_polish')
        else:
            result['content'] = draft
            result['api_calls_saved'] += 1
        
        # 决定是否更新记忆
        if self.should_update_memory(result['content'], analysis):
            await self.aign.memory_manager.update(result['content'])
            result['steps_executed'].append('memory_update')
        else:
            result['api_calls_saved'] += 1
        
        self.chapter_history.append(analysis)
        return result
```

---

## 预期效果

| 指标 | 当前 | 优化后 | 改善 |
|-----|-----|-------|-----|
| 润色调用率 | 100% | 60% | -40% |
| 记忆更新率 | 100% | 50% | -50% |
| API调用次数/章 | 3次 | 1.8次 | **-40%** |
| Token成本 | 100% | 70% | **-30%** |

---

## 实施步骤

1. **新增模块**: `smart_orchestrator.py`
2. **修改生成流程**: 使用协调器决策替代固定流程
3. **添加轻量润色**: 实现 `light_polish` 方法
4. **监控系统**: 记录决策和节省统计

**预估工作量**: 1周
