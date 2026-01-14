# 方案5: MCP (Model Context Protocol) 集成
# Strategy 5: MCP Integration

**优先级**: ⭐⭐⭐ 中 | **实施复杂度**: 高 | **预期收益**: 扩展性大幅提升

---

## 概述

MCP (Model Context Protocol) 是Anthropic推出的开放协议，允许AI模型与外部工具和数据源进行标准化交互。通过集成MCP，可以让模型按需获取信息，而非每次传递完整上下文。

---

## 所需模型能力

| 能力 | 是否必需 | 说明 |
|-----|---------|-----|
| **Function Calling** | ✅ **必需** | 核心依赖，用于调用MCP工具 |
| **Tool Use** | ✅ **必需** | 理解和执行工具调用 |
| **多轮对话** | ⚠️ 推荐 | 支持工具返回后继续生成 |
| **JSON输出** | ⚠️ 推荐 | 工具参数格式化 |

> [!IMPORTANT]
> MCP集成**强依赖Function Calling能力**，不支持工具调用的模型/提供商无法使用此功能。

---

## 提供商兼容性

| 提供商 | Function Calling | MCP兼容性 | 说明 |
|-------|-----------------|----------|-----|
| OpenRouter | ✅ 完整支持 | ✅ **推荐** | 多模型支持工具调用 |
| Claude | ✅ 完整支持 | ✅ **推荐** | MCP原生设计 |
| DeepSeek | ✅ 完整支持 | ✅ 兼容 | V3支持函数调用 |
| Gemini | ✅ 完整支持 | ✅ 兼容 | Function Calling成熟 |
| 智谱AI | ✅ 完整支持 | ✅ 兼容 | GLM-4支持工具 |
| 阿里云 | ✅ 完整支持 | ✅ 兼容 | Qwen支持函数调用 |
| Fireworks | ✅ 完整支持 | ✅ 兼容 | - |
| Grok | ✅ 完整支持 | ✅ 兼容 | - |
| Lambda | ⚠️ 部分支持 | ⚠️ 有限 | 取决于具体模型 |
| SiliconFlow | ✅ 完整支持 | ✅ 兼容 | 推荐国内使用 |
| LM Studio | ⚠️ 模型依赖 | ⚠️ 有限 | 需选择支持工具的模型 |

### 推荐配置

- **最佳体验**: Claude 3.5 Sonnet / GPT-4 Turbo (通过OpenRouter)
- **性价比**: DeepSeek V3 / Qwen2.5
- **国内首选**: SiliconFlow + DeepSeek-V3

---

## 可实现的MCP工具

```python
# MCP工具定义
MCP_TOOLS = [
    {
        "name": "query_character",
        "description": "查询指定角色的信息，避免重复传递完整设定",
        "input_schema": {
            "type": "object",
            "properties": {
                "character_name": {
                    "type": "string",
                    "description": "角色名称"
                },
                "info_type": {
                    "type": "string",
                    "enum": ["full", "appearance", "personality", "background", "relationships"],
                    "description": "需要的信息类型"
                }
            },
            "required": ["character_name"]
        }
    },
    {
        "name": "get_chapter_summary",
        "description": "获取指定章节的摘要信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "chapter_numbers": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "章节编号列表"
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["brief", "standard", "detailed"],
                    "default": "standard"
                }
            },
            "required": ["chapter_numbers"]
        }
    },
    {
        "name": "check_consistency",
        "description": "检查内容与已有设定的一致性",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "需要检查的内容"
                },
                "check_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["timeline", "character", "worldbuilding", "plot"]
                    }
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "get_worldbuilding",
        "description": "获取世界观设定的特定部分",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["power_system", "geography", "factions", "history", "rules"],
                    "description": "设定类别"
                }
            },
            "required": ["category"]
        }
    }
]
```

---

## 实现架构

```python
from typing import Dict, Any, List, Callable
import json

class MCPServer:
    """MCP服务器 - 处理工具调用"""
    
    def __init__(self, aign_instance):
        self.aign = aign_instance
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Callable]:
        """注册所有可用工具"""
        return {
            "query_character": self._query_character,
            "get_chapter_summary": self._get_chapter_summary,
            "check_consistency": self._check_consistency,
            "get_worldbuilding": self._get_worldbuilding,
        }
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """处理工具调用请求"""
        if tool_name not in self.tools:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        try:
            result = self.tools[tool_name](**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _query_character(self, character_name: str, info_type: str = "full") -> Dict:
        """查询角色信息"""
        # 从角色列表中提取信息
        char_info = self._extract_character_info(character_name)
        
        if info_type == "full":
            return char_info
        elif info_type in char_info:
            return {info_type: char_info.get(info_type, "未找到")}
        else:
            return {"error": f"Unknown info_type: {info_type}"}
    
    def _get_chapter_summary(self, chapter_numbers: List[int], 
                              detail_level: str = "standard") -> Dict:
        """获取章节摘要"""
        summaries = {}
        for ch in chapter_numbers:
            if ch in self.aign.chapter_summaries:
                summaries[ch] = self.aign.chapter_summaries[ch]
            else:
                # 从故事线生成摘要
                summaries[ch] = self._generate_summary_from_storyline(ch, detail_level)
        return summaries
    
    def _check_consistency(self, content: str, 
                           check_types: List[str] = None) -> Dict:
        """检查一致性"""
        results = {}
        check_types = check_types or ["character", "timeline"]
        
        for check_type in check_types:
            results[check_type] = self._run_consistency_check(content, check_type)
        
        return results


class MCPEnabledAgent:
    """支持MCP的智能体"""
    
    def __init__(self, chatLLM, mcp_server: MCPServer, tools: List[Dict]):
        self.chatLLM = chatLLM
        self.mcp_server = mcp_server
        self.tools = tools
    
    async def generate_with_tools(self, prompt: str, max_tool_calls: int = 5) -> str:
        """带工具支持的生成"""
        messages = [{"role": "user", "content": prompt}]
        
        for _ in range(max_tool_calls):
            response = await self.chatLLM(
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            # 检查是否完成
            if not response.tool_calls:
                return response.content
            
            # 执行工具调用
            for tool_call in response.tool_calls:
                result = self.mcp_server.handle_tool_call(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        # 强制完成
        return await self._force_complete(messages)
```

---

## 预期效果

| 指标 | 当前 | MCP启用后 | 改善 |
|-----|-----|----------|-----|
| 输入Token/章 | 15000 | 6000-10000 | 33-60% |
| 信息精确度 | 通用 | 按需精确 | 提升 |
| 一致性检查 | 无 | 自动 | 新功能 |
| 扩展性 | 有限 | 高 | 显著提升 |

---

## 实施步骤

1. **新增模块**: `mcp_server.py`, `mcp_tools.py`
2. **修改AI适配器**: 各提供商添加工具调用支持
3. **创建数据接口**: 角色、章节、设定的查询接口
4. **集成到Agent**: 修改 `MarkdownAgent` 支持工具
5. **测试**: 验证各提供商的工具调用兼容性

**预估工作量**: 2-3周

---

## 风险与限制

> [!WARNING]
> - 工具调用增加API往返次数，可能增加延迟
> - 部分提供商的工具调用稳定性有待验证
> - 本地模型(LM Studio)的工具支持取决于具体模型
