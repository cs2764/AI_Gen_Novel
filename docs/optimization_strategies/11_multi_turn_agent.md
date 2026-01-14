# 方案11: Multi-Turn Agent对话
# Strategy 11: Multi-Turn Agent Conversation

**优先级**: ⭐⭐⭐⭐ 高 | **实施复杂度**: 中-高 | **预期Token节省**: 30-50%

---

## 概述

利用模型的多轮对话能力，将复杂任务分解为交互式Agent会话。模型可以按需请求信息，而非一次性接收全部上下文。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **多轮对话** | ✅ **必需** | 保持会话上下文 |
| **Function Calling** | ✅ **必需** | 调用工具获取信息 |
| **会话记忆** | ⚠️ 推荐 | API需支持会话状态 |
| **Tool Use回环** | ✅ **必需** | 工具返回后继续生成 |

> [!IMPORTANT]
> 此方案需要模型和API同时支持**多轮对话+工具调用**。

---

## 提供商兼容性

| 提供商 | 多轮对话 | 工具回环 | 会话状态 | 兼容性 |
|-------|---------|---------|---------|-------|
| OpenRouter | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Claude | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| DeepSeek | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Gemini | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| 智谱AI | ✅ | ✅ | ⚠️ 部分 | ✅ 兼容 |
| 阿里云 | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Fireworks | ✅ | ✅ | ✅ | ✅ 兼容 |
| Grok | ✅ | ✅ | ⚠️ 未知 | ⚠️ 需验证 |
| Lambda | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ⚠️ 有限 |
| SiliconFlow | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| LM Studio | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ✅ 本地管理 | ⚠️ 有限 |

---

## 对话流程设计

### 传统单次调用 vs Multi-Turn

```
=== 传统模式 ===
┌─────────────────────────────────────────────────────────────────┐
│ 单次请求包含：                                                    │
│ • 系统提示词 (3000 tokens)                                       │
│ • 完整大纲 (2000 tokens)                                         │
│ • 全部人物设定 (1500 tokens)                                     │
│ • 前文记忆 (1500 tokens)                                         │
│ • 前5章总结 (2500 tokens)                                        │
│ • 后5章梗概 (2500 tokens)                                        │
│ • 本章故事线 (500 tokens)                                        │
│ ───────────────────────────────────────────────────────────────│
│ 总计: ~13500 tokens                                              │
└─────────────────────────────────────────────────────────────────┘

=== Multi-Turn模式 ===
┌─────────────────────────────────────────────────────────────────┐
│ Turn 1: 初始请求 (3500 tokens)                                   │
│ • 系统提示词 (精简版 1000 tokens)                                 │
│ • 本章故事线 (500 tokens)                                        │
│ • 基础上下文 (2000 tokens)                                       │
│                                                                 │
│ Agent: "我需要查看主角的人物设定和上一章的内容"                    │
│        → 调用 get_character("主角") + get_chapter(N-1)           │
│                                                                 │
│ Turn 2: 工具返回 (+1500 tokens)                                  │
│ • 主角设定 (800 tokens)                                          │
│ • 上一章摘要 (700 tokens)                                        │
│                                                                 │
│ Agent: 开始写作... → 输出章节内容                                 │
│ ───────────────────────────────────────────────────────────────│
│ 总计: ~5000 tokens (多轮累计)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 实现方案

```python
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TurnType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"

@dataclass
class ConversationTurn:
    """会话轮次"""
    role: TurnType
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None

class MultiTurnAgentSession:
    """多轮Agent会话管理器"""
    
    def __init__(self, chatLLM, tools: List[Dict], tool_handlers: Dict):
        self.chatLLM = chatLLM
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.conversation: List[Dict] = []
        self.total_tokens_used = 0
        
    def _build_initial_context(self, storyline: dict, chapter_num: int) -> str:
        """构建精简的初始上下文"""
        return f"""# 当前任务
写作第{chapter_num}章的内容。

# 本章故事线
{storyline.get('描述', '')}

# 可用工具说明
你可以通过以下工具获取需要的信息：
- get_character(name): 获取角色详细信息
- get_chapters(range): 获取指定章节摘要
- get_worldbuilding(category): 获取世界观设定
- check_consistency(content): 检查内容一致性

请在需要时调用这些工具，不要猜测信息。

# 输出要求
直接输出章节正文，2500-4000字。
"""
    
    async def run_session(self, storyline: dict, chapter_num: int,
                          max_turns: int = 5) -> Dict[str, Any]:
        """运行多轮会话"""
        # 初始化会话
        initial_context = self._build_initial_context(storyline, chapter_num)
        self.conversation = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": initial_context}
        ]
        
        result = {
            'content': '',
            'turns': 0,
            'tool_calls': [],
            'tokens_used': 0
        }
        
        for turn in range(max_turns):
            # 调用模型
            response = await self.chatLLM(
                messages=self.conversation,
                tools=self.tools,
                tool_choice="auto"
            )
            
            result['turns'] = turn + 1
            
            # 检查是否有工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # 记录助手消息
                self.conversation.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [tc.model_dump() for tc in response.tool_calls]
                })
                
                # 执行所有工具调用
                for tool_call in response.tool_calls:
                    tool_result = await self._execute_tool(tool_call)
                    result['tool_calls'].append({
                        'name': tool_call.function.name,
                        'result_length': len(tool_result)
                    })
                    
                    self.conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
            else:
                # 没有工具调用，生成完成
                result['content'] = response.content
                result['tokens_used'] = self._estimate_tokens()
                return result
        
        # 达到最大轮数，强制完成
        result['content'] = await self._force_completion()
        result['tokens_used'] = self._estimate_tokens()
        return result
    
    async def _execute_tool(self, tool_call) -> str:
        """执行工具调用"""
        import json
        
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"未知工具: {tool_name}"})
        
        try:
            result = await handler(**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    async def _force_completion(self) -> str:
        """强制完成生成"""
        self.conversation.append({
            "role": "user",
            "content": "请现在直接输出完整的章节内容，不要再调用任何工具。"
        })
        
        response = await self.chatLLM(
            messages=self.conversation,
            tools=None  # 禁用工具
        )
        return response.content
    
    def _estimate_tokens(self) -> int:
        """估算总Token消耗"""
        total = 0
        for msg in self.conversation:
            content = msg.get('content', '')
            total += len(content) // 2  # 粗略估算
        return total
    
    def _get_system_prompt(self) -> str:
        return """你是专业的网络小说写手。

核心能力：
- 引人入胜的情节展开
- 生动的人物刻画
- 流畅的对话设计
- 适当的环境描写

工作方式：
1. 先分析本章任务
2. 若需要额外信息，调用相应工具获取
3. 获取所需信息后，开始写作
4. 直接输出章节正文

注意：只在必要时调用工具，避免不必要的信息获取。"""
```

---

## 预期效果

| 场景 | 传统Token | Multi-Turn Token | 节省 | 轮数 |
|-----|----------|-----------------|-----|-----|
| 简单章节 | 13500 | 4000 | **70%** | 2 |
| 普通章节 | 13500 | 6000 | **56%** | 3 |
| 复杂章节 | 13500 | 10000 | **26%** | 4-5 |
| **加权平均** | 13500 | 6500 | **52%** | ~3 |

---

## 实施步骤

1. **会话管理器**: 创建 `multi_turn_session.py`
2. **工具集成**: 复用Function Calling工具
3. **提供商适配**: 确保各适配器支持多轮工具调用
4. **回退机制**: 不支持时降级到传统模式
5. **测试优化**: 调整最大轮数和工具策略

**预估工作量**: 1-2周
