# 方案6: Skill-Based Agent系统
# Strategy 6: Skill-Based Agent System

**优先级**: ⭐⭐⭐ 中 | **实施复杂度**: 高 | **预期Token节省**: 20-35%

---

## 概述

将当前的6个固定Agent升级为可组合的Skill系统，每个Agent具备可动态加载的技能模块，按需激活特定技能，避免每次都使用完整提示词。

```
当前: 固定Agent → 固定提示词 → 固定能力
新架构: 基础Agent + 可插拔Skills → 动态提示词组合 → 灵活能力
```

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **基础对话** | ✅ 必需 | 标准文本生成 |
| **指令遵循** | ✅ 必需 | 理解组合指令 |
| **长上下文** | ⚠️ 推荐 | 多技能时提示词较长 |
| **角色扮演** | ⚠️ 推荐 | 更好地执行特定技能 |

> [!NOTE]
> 此方案主要是提示词组合优化，**对模型能力无特殊要求**，但更强的指令遵循能力效果更好。

---

## 提供商兼容性

| 提供商 | 兼容性 | 指令遵循 | 推荐程度 |
|-------|-------|---------|---------|
| DeepSeek | ✅ 完全兼容 | ⭐⭐⭐⭐⭐ | 🔥 强烈推荐 |
| OpenRouter | ✅ 完全兼容 | ⭐⭐⭐⭐⭐ | 🔥 强烈推荐 |
| Claude | ✅ 完全兼容 | ⭐⭐⭐⭐⭐ | 🔥 强烈推荐 |
| Gemini | ✅ 完全兼容 | ⭐⭐⭐⭐ | 推荐 |
| 智谱AI | ✅ 完全兼容 | ⭐⭐⭐⭐ | 推荐 |
| 阿里云 | ✅ 完全兼容 | ⭐⭐⭐⭐ | 推荐 |
| Fireworks | ✅ 完全兼容 | ⭐⭐⭐⭐ | 推荐 |
| Grok | ✅ 完全兼容 | ⭐⭐⭐ | 一般 |
| Lambda | ✅ 完全兼容 | ⭐⭐⭐⭐ | 推荐 |
| SiliconFlow | ✅ 完全兼容 | ⭐⭐⭐⭐ | 推荐 |
| LM Studio | ✅ 完全兼容 | ⭐⭐⭐-⭐⭐⭐⭐ | 取决于模型 |

**所有11个提供商均兼容此方案。**

---

## 技能定义

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class SkillContext:
    """技能所需的上下文信息"""
    required_fields: List[str]  # 必需的输入字段
    optional_fields: List[str]  # 可选的输入字段

class BaseSkill(ABC):
    """技能基类"""
    
    name: str = "base_skill"
    description: str = "基础技能"
    token_cost: int = 200  # 预估Token消耗
    
    @abstractmethod
    def get_prompt_segment(self) -> str:
        """返回该技能的提示词片段"""
        pass
    
    @abstractmethod
    def get_required_context(self) -> SkillContext:
        """返回该技能需要的上下文信息"""
        pass


class DialogueSkill(BaseSkill):
    """对话增强技能"""
    
    name = "dialogue"
    description = "增强对话表现力和自然度"
    token_cost = 250
    
    def get_prompt_segment(self) -> str:
        return """
## 对话技能
- 对话层次感：语气词+停顿+潜台词
- 动作配合：说话时的微表情和肢体语言
- 个性区分：不同角色有不同说话风格
- 信息密度：对话推进剧情，避免空聊
"""
    
    def get_required_context(self) -> SkillContext:
        return SkillContext(
            required_fields=["character_profiles"],
            optional_fields=["dialogue_history"]
        )


class ActionSkill(BaseSkill):
    """动作场景技能"""
    
    name = "action"
    description = "增强动作场景描写"
    token_cost = 300
    
    def get_prompt_segment(self) -> str:
        return """
## 动作技能
- 节奏控制：短句加速，长句缓冲
- 空间感：清晰的位置关系和移动轨迹
- 力量感：动作的冲击力和后果
- 感官细节：声音、触感、疼痛感
"""
    
    def get_required_context(self) -> SkillContext:
        return SkillContext(
            required_fields=["scene_setting", "character_abilities"],
            optional_fields=["power_system"]
        )


class EmotionSkill(BaseSkill):
    """情感深度技能"""
    
    name = "emotion"
    description = "增强情感表达和心理描写"
    token_cost = 200
    
    def get_prompt_segment(self) -> str:
        return """
## 情感技能
- 内心独白：真实的心理活动
- 情绪层次：复杂情感的细腻表达
- 共情触发：让读者感同身受
- 情感铺垫：情绪变化有迹可循
"""
    
    def get_required_context(self) -> SkillContext:
        return SkillContext(
            required_fields=["character_background"],
            optional_fields=["relationship_map"]
        )


class WorldbuildingSkill(BaseSkill):
    """世界观塑造技能"""
    
    name = "worldbuilding"
    description = "增强设定融入和世界观表达"
    token_cost = 250
    
    def get_prompt_segment(self) -> str:
        return """
## 世界观技能
- 自然融入：设定通过情节展示而非说明
- 规则一致：遵循已建立的世界法则
- 细节真实：小细节增加世界可信度
- 探索感：保留神秘，逐步揭示
"""
    
    def get_required_context(self) -> SkillContext:
        return SkillContext(
            required_fields=["worldbuilding_doc"],
            optional_fields=["revealed_secrets"]
        )


class ForeshadowingSkill(BaseSkill):
    """伏笔铺垫技能"""
    
    name = "foreshadowing"
    description = "植入和回收伏笔"
    token_cost = 200
    
    def get_prompt_segment(self) -> str:
        return """
## 伏笔技能
- 隐藏线索：看似无关的细节暗藏玄机
- 自然埋设：伏笔不突兀，融入日常
- 适时回收：在合适时机揭示伏笔
- 层次递进：小伏笔引向大揭示
"""
    
    def get_required_context(self) -> SkillContext:
        return SkillContext(
            required_fields=["future_plot_points"],
            optional_fields=["active_foreshadowing"]
        )


class PacingSkill(BaseSkill):
    """节奏控制技能"""
    
    name = "pacing"
    description = "控制故事节奏和张力"
    token_cost = 200
    
    def get_prompt_segment(self) -> str:
        return """
## 节奏技能
- 紧松有度：高潮与喘息交替
- 悬念管理：适时制造和释放悬念
- 信息节奏：关键信息的释放时机
- 场景切换：自然过渡，不拖沓
"""
    
    def get_required_context(self) -> SkillContext:
        return SkillContext(
            required_fields=["chapter_type"],
            optional_fields=["tension_curve"]
        )
```

---

## 技能组合器

```python
class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """注册默认技能"""
        default_skills = [
            DialogueSkill(),
            ActionSkill(),
            EmotionSkill(),
            WorldbuildingSkill(),
            ForeshadowingSkill(),
            PacingSkill(),
        ]
        for skill in default_skills:
            self.skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        return self.skills.get(name)
    
    def list_skills(self) -> List[str]:
        return list(self.skills.keys())


class SkillComposer:
    """技能组合器"""
    
    # 预设的技能组合
    PRESETS = {
        'dialogue_scene': ['dialogue', 'emotion'],
        'action_scene': ['action', 'pacing'],
        'worldbuilding_scene': ['worldbuilding', 'foreshadowing'],
        'climax_scene': ['action', 'emotion', 'pacing', 'foreshadowing'],
        'transition_scene': ['pacing'],
    }
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
    
    def compose_prompt(self, base_prompt: str, skill_names: List[str]) -> str:
        """组合基础提示词和技能提示词"""
        skill_segments = []
        total_token_cost = 0
        
        for name in skill_names:
            skill = self.registry.get_skill(name)
            if skill:
                skill_segments.append(skill.get_prompt_segment())
                total_token_cost += skill.token_cost
        
        if skill_segments:
            skills_text = "\n".join(skill_segments)
            return f"{base_prompt}\n\n# 本次激活的技能\n{skills_text}"
        
        return base_prompt
    
    def auto_select_skills(self, chapter_type: str, 
                           scene_analysis: Dict = None) -> List[str]:
        """根据章节类型自动选择技能"""
        if chapter_type in self.PRESETS:
            return self.PRESETS[chapter_type]
        
        # 基于场景分析动态选择
        if scene_analysis:
            skills = []
            if scene_analysis.get('has_dialogue', False):
                skills.append('dialogue')
            if scene_analysis.get('has_action', False):
                skills.append('action')
            if scene_analysis.get('emotional_weight', 0) > 0.5:
                skills.append('emotion')
            return skills or ['pacing']
        
        return ['dialogue', 'emotion']  # 默认组合
```

---

## 预期效果

| 场景 | 当前Token | 技能组合后 | 节省 |
|-----|----------|----------|-----|
| 对话场景 | 4000 | 1500 (2技能) | 62.5% |
| 动作场景 | 4000 | 1600 (2技能) | 60% |
| 过渡场景 | 4000 | 800 (1技能) | 80% |
| 高潮场景 | 4000 | 3200 (4技能) | 20% |
| **加权平均** | 4000 | 1700 | **57.5%** |

---

## 实施步骤

1. **新增模块**: `skills/` 目录，包含各技能定义
2. **创建注册器**: `skill_registry.py`
3. **修改Agent**: 支持动态技能加载
4. **场景分析器**: 自动识别章节类型
5. **测试**: 验证各技能组合的生成质量

**预估工作量**: 2-3周
