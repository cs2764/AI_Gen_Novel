# 方案9: 原生Function Calling增强
# Strategy 9: Native Function Calling Enhancement

**优先级**: ⭐⭐⭐⭐ 高 | **实施复杂度**: 中 | **预期收益**: 按需获取信息，减少冗余Token

---

## 概述

充分利用现代模型的Function Calling能力，让模型按需调用工具获取信息，而非在每次请求中传递完整上下文。

项目当前仅在 `enhanced_storyline_generator.py` 中使用了Tool Calling，本方案将其扩展到章节生成、润色、记忆等全流程。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **Function Calling** | ✅ **必需** | 核心功能 |
| **Tool Choice** | ⚠️ 推荐 | 控制工具调用行为 |
| **Parallel Tool Calls** | ⚠️ 推荐 | 一次调用多个工具 |
| **Streaming with Tools** | ❌ 可选 | 流式+工具 |

> [!IMPORTANT]
> 此方案**强依赖Function Calling**，不支持的提供商/模型将无法使用。

---

## 提供商兼容性

| 提供商 | Function Calling | Parallel Calls | Tool Choice | 兼容性 |
|-------|-----------------|----------------|-------------|-------|
| OpenRouter | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Claude | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| DeepSeek | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Gemini | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| 智谱AI | ✅ | ⚠️ 部分 | ✅ | ✅ 兼容 |
| 阿里云 | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Fireworks | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| Grok | ✅ | ⚠️ 未知 | ✅ | ⚠️ 需验证 |
| Lambda | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ⚠️ 有限 |
| SiliconFlow | ✅ | ✅ | ✅ | ✅ **完全兼容** |
| LM Studio | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ⚠️ 模型依赖 | ⚠️ 有限 |

### 推荐配置

| 场景 | 推荐 | 说明 |
|-----|-----|-----|
| 最佳体验 | Claude 3.5 / GPT-4 Turbo | 工具调用最稳定 |
| 性价比 | DeepSeek V3 | 功能完整，成本低 |
| 国内首选 | SiliconFlow + DeepSeek | 延迟低 |

---

## 工具集设计

```python
from typing import Any, Dict, List

# 完整的工具定义集
AIGN_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_character_info",
            "description": "获取指定角色的详细信息。用于需要了解角色背景、性格、外貌等时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_name": {
                        "type": "string",
                        "description": "角色名称"
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["background", "personality", "appearance", 
                                    "abilities", "relationships", "all"]
                        },
                        "description": "需要的信息字段，默认全部"
                    }
                },
                "required": ["character_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_previous_chapters",
            "description": "获取指定章节的内容摘要。用于回顾前文情节时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "integer", "description": "起始章节"},
                            "end": {"type": "integer", "description": "结束章节"}
                        },
                        "required": ["start", "end"]
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["brief", "standard", "detailed"],
                        "default": "standard"
                    }
                },
                "required": ["chapter_range"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_plot_points",
            "description": "获取特定情节点的详细信息。用于需要参考伏笔、转折等时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_type": {
                        "type": "string",
                        "enum": ["foreshadowing", "turning_point", "climax", 
                                "resolution", "all"]
                    },
                    "chapter_scope": {
                        "type": "string",
                        "description": "章节范围，如 '1-10' 或 'current_arc'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_worldbuilding",
            "description": "获取世界观设定信息。用于需要参考设定规则时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["power_system", "geography", "factions", 
                                "history", "rules", "culture"]
                    },
                    "specific_item": {
                        "type": "string",
                        "description": "特定条目名称（可选）"
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_consistency",
            "description": "检查内容与已有设定的一致性。用于写作过程中验证细节时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_to_check": {
                        "type": "string",
                        "description": "需要检查的内容片段"
                    },
                    "check_aspects": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["timeline", "character_voice", "power_levels",
                                    "geography", "established_facts"]
                        }
                    }
                },
                "required": ["content_to_check"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_storyline",
            "description": "获取当前章节的故事线详情。",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter_number": {
                        "type": "integer",
                        "description": "章节编号"
                    },
                    "include_segments": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含四分段详情"
                    }
                },
                "required": ["chapter_number"]
            }
        }
    }
]
```

---

## 集成实现

```python
import json
from typing import Callable, Dict, Any

class FunctionCallingAgent:
    """支持函数调用的Agent"""
    
    def __init__(self, chatLLM, tools: list, tool_handlers: Dict[str, Callable]):
        self.chatLLM = chatLLM
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.max_tool_iterations = 5
    
    async def generate_with_functions(self, system_prompt: str, 
                                       user_prompt: str) -> str:
        """带函数调用的生成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        for iteration in range(self.max_tool_iterations):
            response = await self.chatLLM(
                messages=messages,
                tools=self.tools,
                tool_choice="auto"  # 让模型自行决定是否调用
            )
            
            # 检查是否需要调用工具
            if not hasattr(response, 'tool_calls') or not response.tool_calls:
                return response.content
            
            # 处理工具调用
            messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls
            })
            
            for tool_call in response.tool_calls:
                result = await self._execute_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        # 达到最大迭代，强制结束
        return await self._force_completion(messages)
    
    async def _execute_tool(self, tool_call) -> str:
        """执行工具调用"""
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        try:
            result = await handler(**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})


# 工具处理器示例
class AIGNToolHandlers:
    """AIGN工具处理器"""
    
    def __init__(self, aign_instance):
        self.aign = aign_instance
    
    async def get_character_info(self, character_name: str, 
                                  fields: list = None) -> dict:
        """获取角色信息"""
        char_data = self._parse_character_list(self.aign.character_list)
        
        if character_name not in char_data:
            return {"error": f"角色 {character_name} 未找到"}
        
        info = char_data[character_name]
        
        if fields and 'all' not in fields:
            return {k: v for k, v in info.items() if k in fields}
        
        return info
    
    async def get_previous_chapters(self, chapter_range: dict,
                                     detail_level: str = "standard") -> dict:
        """获取前文摘要"""
        start, end = chapter_range['start'], chapter_range['end']
        
        summaries = {}
        for ch in range(start, end + 1):
            if ch in self.aign.chapter_summaries:
                summaries[ch] = self.aign.chapter_summaries[ch]
            elif ch <= len(self.aign.storyline_data):
                # 从故事线获取
                summaries[ch] = self._summarize_from_storyline(ch, detail_level)
        
        return summaries
    
    # ... 其他处理器方法
```

---

## 预期效果

| 指标 | 传统方式 | Function Calling | 改善 |
|-----|---------|-----------------|-----|
| 输入Token/章 | 15000 | 5000-8000 | **47-67%** |
| 信息精确度 | 全量传递 | 按需获取 | 提升 |
| 扩展性 | 有限 | 易于添加新工具 | 提升 |

---

## 实施步骤

1. **定义工具集**: 创建 `function_tools.py`
2. **实现处理器**: 创建 `tool_handlers.py`
3. **修改Agent**: 添加函数调用支持
4. **适配提供商**: 确保各AI适配器支持工具调用
5. **测试**: 验证不同提供商的兼容性

**预估工作量**: 1-2周
