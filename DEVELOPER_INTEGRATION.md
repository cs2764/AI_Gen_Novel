# Style-RAG 开发者集成文档
# Developer Integration Guide

本文档介绍如何在其他 Python 项目中使用 Style-RAG 系统进行语义检索。

---

## 快速开始

### 1. 安装依赖

```bash
# 进入 Style-RAG 项目目录
cd AI_Gen_Novel_rag

# 激活虚拟环境 (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 或者将 style_rag 包添加到你的项目路径
import sys
sys.path.insert(0, "path/to/AI_Gen_Novel_rag")
```

### 2. 初始化客户端

```python
from style_rag import StyleRAGClient, EmbeddingConfig, EmbeddingProvider

# ==================== 方式一：使用已有索引（推荐）====================
# 只需指定索引路径，即可开始检索
client = StyleRAGClient(
    db_path="./rag_index"  # 已创建好的索引目录
)

# ==================== 方式二：使用 LM Studio 本地模型 ====================
embedding_config = EmbeddingConfig(
    provider=EmbeddingProvider.LM_STUDIO,
    lm_studio_url="http://localhost:1234/v1",
    lm_studio_model="text-embedding-qwen3-embedding-4b"
)

client = StyleRAGClient(
    db_path="./rag_index",
    embedding_config=embedding_config
)

# ==================== 方式三：使用云端 API ====================
# SiliconFlow
embedding_config = EmbeddingConfig(
    provider=EmbeddingProvider.SILICONFLOW,
    api_key="your-api-key",
    api_model="BAAI/bge-m3",
    max_concurrency=20,
    enable_concurrency=True
)

# OpenRouter
embedding_config = EmbeddingConfig(
    provider=EmbeddingProvider.OPENROUTER,
    api_key="your-api-key",
    api_model="baai/bge-m3"
)
```

---

## 检索 API（核心功能）

### 基础语义检索

```python
# 简单检索
results = client.search(
    query="月下独行的场景",
    top_k=5,               # 返回前5条结果
    min_similarity=0.5     # 最小相似度阈值
)

# 带类型过滤的检索
results = client.search(
    query="两人激烈争吵",
    filter_type="dialogue",  # 只检索对话类型
    top_k=3
)

# 处理结果
for r in results:
    print(f"相似度: {r['similarity']:.3f}")
    print(f"内容: {r['content'][:100]}...")
    print(f"来源: {r['metadata'].get('source', 'unknown')}")
    print("---")
```

**filter_type 可选值**:
- `dialogue` - 对话片段
- `description` - 描写片段
- `action` - 动作场景

### 场景检索（创作专用）

```python
# 按场景和情感检索
results = client.search_by_scene(
    scene_description="主角在雨中与敌人对峙",
    emotion="紧张",           # 可选：激动/温馨/紧张/悲伤/神秘/浪漫
    writing_type="action",    # 可选：dialogue/description/action
    top_k=3
)
```

### 写作上下文检索

```python
# 为写作自动构建检索查询
results = client.retrieve_for_writing(
    storyline="李月穿越到古代，发现自己成为了一位公主",
    chapter_summary="公主第一次参加宫廷宴会，遇到神秘的黑衣刺客",
    character_states={
        "李月": "紧张但好奇",
        "刺客": "冷酷而警觉"
    },
    writing_phase="rising_action",  # 可选：intro/rising_action/climax/falling_action
    top_k=3
)
```

---

## 格式化输出

将检索结果格式化为可嵌入 Prompt 的参考文本：

```python
results = client.search("夜色下的城市", top_k=3)

# 生成格式化的参考文本
reference_text = client.format_references(results, max_length=500)

# 将参考文本嵌入到写作 Prompt 中
prompt = f"""
{reference_text}

请根据上述风格参考，撰写一段描述夜色下城市的文字。
"""
```

**输出示例**:
```markdown
## 写作风格参考

以下是与当前场景相似的优秀写作片段，请参考其用词和表达手法：

### 参考1 (description, 相似度: 0.85)
```
夜色如水般倾泻在石板路上，月光穿过摇曳的梧桐叶，投下斑驳的光影...
```

### 参考2 (description, 相似度: 0.78)
```
城市的灯火渐次熄灭，只余下远处高楼顶端的信号灯，在夜空中规律地闪烁...
```

> 请学习上述参考的用词习惯、句式结构和表达手法，但要创作全新的内容。
```

---

## 管理功能

```python
# 获取索引统计
stats = client.get_stats()
print(f"总片段数: {stats['total_chunks']}")
print(f"嵌入模型: {stats['embedding_model']}")
print(f"提供商: {stats['embedding_provider']}")

# 导出索引（备份）
client.export_index("./backup/rag_backup_20260119")

# 导入索引
client.import_index("./backup/rag_backup_20260119")

# 清空索引
client.clear_index()
```

---

## HTTP API 方式

如果不想直接导入 Python 模块，可以启动 HTTP 服务：

### 启动服务

```bash
# 使用 run.py 菜单启动（端口 8086）
python run.py
# 选择 9. 启动服务

# 或直接启动
python -m style_rag.api.server --port 8086
```

### API 端点

| 方法   | 路径            | 说明         |
| ------ | --------------- | ------------ |
| GET    | `/stats`        | 获取索引统计 |
| POST   | `/search`       | 语义检索     |
| POST   | `/search/scene` | 场景检索     |
| POST   | `/index/texts`  | 索引文本     |
| DELETE | `/index`        | 清空索引     |

### 调用示例

```python
import requests

# 语义检索
response = requests.post("http://localhost:8086/search", json={
    "query": "月下相遇的浪漫场景",
    "top_k": 5,
    "min_similarity": 0.5
})

results = response.json()
for r in results:
    print(f"{r['similarity']:.3f}: {r['content'][:50]}...")

# 场景检索
response = requests.post("http://localhost:8086/search/scene", json={
    "scene_description": "雨夜对决",
    "emotion": "紧张",
    "top_k": 3
})
```

### cURL 示例

```bash
# 获取统计
curl http://localhost:8086/stats

# 语义检索
curl -X POST http://localhost:8086/search \
  -H "Content-Type: application/json" \
  -d '{"query": "战斗场景", "top_k": 3}'
```

---

## 完整集成示例

```python
"""
在小说生成系统中集成 Style-RAG
"""
import sys
sys.path.insert(0, "F:/AI_Gen_Novel_rag")

from style_rag import StyleRAGClient, EmbeddingConfig, EmbeddingProvider

class NovelWriter:
    def __init__(self):
        # 初始化 RAG 客户端
        self.rag = StyleRAGClient(
            db_path="F:/AI_Gen_Novel_rag/rag_index",
            embedding_config=EmbeddingConfig(
                provider=EmbeddingProvider.LM_STUDIO,
                lm_studio_url="http://localhost:1234/v1",
                lm_studio_model="text-embedding-qwen3-embedding-4b"
            )
        )
    
    def get_style_references(self, scene_desc: str, emotion: str = None) -> str:
        """获取风格参考文本"""
        results = self.rag.search_by_scene(
            scene_description=scene_desc,
            emotion=emotion,
            top_k=3
        )
        return self.rag.format_references(results)
    
    def generate_chapter(self, storyline: str, chapter_summary: str) -> str:
        """生成章节（示例）"""
        # 1. 获取风格参考
        style_refs = self.rag.retrieve_for_writing(
            storyline=storyline,
            chapter_summary=chapter_summary,
            top_k=3
        )
        reference_text = self.rag.format_references(style_refs)
        
        # 2. 构建 Prompt
        prompt = f"""
{reference_text}

## 当前故事线
{storyline}

## 本章摘要
{chapter_summary}

请根据以上信息，创作本章内容：
"""
        # 3. 调用 LLM 生成...
        # content = call_llm(prompt)
        return prompt  # 示例返回 prompt

# 使用示例
writer = NovelWriter()
refs = writer.get_style_references("两人月下初遇", emotion="浪漫")
print(refs)
```

---

## Embedding 提供商配置参考

| 提供商      | Provider 枚举                   | 必需参数                           |
| ----------- | ------------------------------- | ---------------------------------- |
| LM Studio   | `EmbeddingProvider.LM_STUDIO`   | `lm_studio_url`, `lm_studio_model` |
| SiliconFlow | `EmbeddingProvider.SILICONFLOW` | `api_key`, `api_model`             |
| OpenRouter  | `EmbeddingProvider.OPENROUTER`  | `api_key`, `api_model`             |
| 本地 GGUF   | `EmbeddingProvider.LOCAL_GGUF`  | `gguf_model_path`                  |
| 本地模型    | `EmbeddingProvider.LOCAL`       | `local_model`（可选）              |

---

## 注意事项

1. **确保索引已创建**：使用检索功能前，需要先通过 `run.py` 创建索引
2. **Embedding 模型一致性**：检索时使用的 Embedding 模型必须与创建索引时一致
3. **相似度阈值**：建议根据实际效果调整 `min_similarity`，通常 0.3-0.6 较为合适
4. **内存管理**：处理完毕后建议调用 `del client` 释放资源

