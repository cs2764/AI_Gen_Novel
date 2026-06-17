#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG 客户端模块 - 封装与 RAG API 服务的通信

此模块提供与 Style-RAG 服务的 HTTP 接口交互能力，用于：
1. 正文生成阶段：获取风格参考
2. 润色阶段：获取润色参考
3. 从正文提炼关键剧情和修辞手法

所有操作都包含错误处理，确保 RAG 服务问题不会打断文章生成流程。
"""

import requests
from typing import List, Dict, Optional


class RAGClient:
    """RAG HTTP 客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化 RAG 客户端
        
        Args:
            base_url: RAG API 服务地址，如 http://192.168.1.211:8086/
            timeout: 请求超时时间（秒），默认 30 秒
        """
        # 确保 base_url 不以 / 结尾
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def search(self, query: str, top_k: int = 10, min_similarity: float = 0.3) -> List[Dict]:
        """
        语义检索
        
        Args:
            query: 检索查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            
        Returns:
            检索结果列表，每项包含 content, metadata, similarity
        """
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "min_similarity": min_similarity
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ RAG 检索请求失败: {e}")
            return []
        except Exception as e:
            print(f"⚠️ RAG 检索解析失败: {e}")
            return []
    
    def search_by_scene(
        self, 
        scene_description: str, 
        emotion: Optional[str] = None,
        writing_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        按场景检索
        
        Args:
            scene_description: 场景描述
            emotion: 情感标签（可选）
            writing_type: 写作类型（可选）
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        try:
            payload = {
                "scene_description": scene_description,
                "top_k": top_k
            }
            if emotion:
                payload["emotion"] = emotion
            if writing_type:
                payload["writing_type"] = writing_type
                
            response = requests.post(
                f"{self.base_url}/search/scene",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ RAG 场景检索请求失败: {e}")
            return []
        except Exception as e:
            print(f"⚠️ RAG 场景检索解析失败: {e}")
            return []
    
    def get_stats(self) -> Optional[Dict]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典，失败返回 None
        """
        try:
            response = requests.get(
                f"{self.base_url}/stats",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ RAG 统计信息获取失败: {e}")
            return None
    
    def is_available(self, max_retries: int = 2) -> bool:
        """
        检查 RAG 服务是否可用（含重试机制）
        
        Args:
            max_retries: 最大重试次数，默认2次
            
        Returns:
            服务可用返回 True，否则返回 False
        """
        import time as _time
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    f"{self.base_url}/stats",
                    timeout=10  # 健康检查超时
                )
                if response.status_code == 200:
                    return True
                else:
                    print(f"⚠️ RAG 健康检查返回非200状态码: {response.status_code}")
            except requests.exceptions.Timeout:
                print(f"⚠️ RAG 健康检查超时 ({self.base_url}/stats), 尝试 {attempt + 1}/{max_retries + 1}")
            except requests.exceptions.ConnectionError as e:
                print(f"⚠️ RAG 健康检查连接失败: {e}, 尝试 {attempt + 1}/{max_retries + 1}")
            except Exception as e:
                print(f"⚠️ RAG 健康检查异常: {e}, 尝试 {attempt + 1}/{max_retries + 1}")
            
            # 如果还有重试机会，等待后重试
            if attempt < max_retries:
                _time.sleep(1)
        
        return False
    
    def format_references(self, results: List[Dict], max_length: int = 3000) -> str:
        """
        格式化检索结果为提示词格式
        
        Args:
            results: 检索结果列表
            max_length: 最大输出长度
            
        Returns:
            格式化的参考文本
        """
        if not results:
            return ""
        
        formatted_parts = ["## 写作风格参考\n"]
        formatted_parts.append("以下是与当前场景相似的优秀写作片段，请参考其用词和表达手法：\n")
        
        current_length = sum(len(p) for p in formatted_parts)
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            similarity = result.get('similarity', 0)
            metadata = result.get('metadata', {})
            content_type = metadata.get('type', 'unknown')
            
            # 构建单条参考
            ref_text = f"\n### 参考{i} ({content_type}, 相似度: {similarity:.2f})\n"
            ref_text += f"```\n{content}\n```\n"
            
            # 检查长度限制
            if current_length + len(ref_text) > max_length:
                break
            
            formatted_parts.append(ref_text)
            current_length += len(ref_text)
        
        formatted_parts.append("\n> 请学习上述参考的用词习惯、句式结构和表达手法，但要创作全新的内容。\n")
        
        return "".join(formatted_parts)


def extract_key_elements(content: str, max_length: int = 500) -> str:
    """
    从正文提炼关键剧情和修辞手法
    
    使用简单规则提取：
    - 对话片段
    - 描写片段
    - 情节转折关键词
    
    Args:
        content: 正文内容
        max_length: 最大输出长度
        
    Returns:
        提炼的关键元素文本
    """
    import re
    
    elements = []
    
    # 1. 提取对话（引号内内容）
    dialogues = re.findall(r'[""「」『』]([^""「」『』]{10,100})[""「」『』]', content)
    if dialogues:
        elements.append("【对话片段】")
        for d in dialogues[:3]:  # 最多3条对话
            elements.append(f"- {d}")
    
    # 2. 提取情感关键词
    emotion_keywords = [
        "心中一震", "不禁", "忍不住", "突然", "顿时", "蓦然", "霎时",
        "心头一紧", "眼眶湿润", "热泪盈眶", "怒火中烧", "心如刀绞"
    ]
    found_emotions = []
    for kw in emotion_keywords:
        if kw in content:
            # 找到关键词所在的句子
            pattern = r'[^。！？]*' + re.escape(kw) + r'[^。！？]*[。！？]'
            matches = re.findall(pattern, content)
            if matches:
                found_emotions.append(matches[0].strip())
    
    if found_emotions:
        elements.append("\n【情感描写】")
        for e in found_emotions[:2]:  # 最多2条
            elements.append(f"- {e}")
    
    # 3. 提取场景描写（以景物、环境词开头的句子）
    scene_starters = ["月光", "阳光", "夜色", "风", "雨", "雪", "天空", "大地", "远处", "四周"]
    found_scenes = []
    for starter in scene_starters:
        pattern = starter + r'[^。！？]{10,80}[。！？]'
        matches = re.findall(pattern, content)
        if matches:
            found_scenes.extend(matches[:1])
    
    if found_scenes:
        elements.append("\n【场景描写】")
        for s in found_scenes[:2]:
            elements.append(f"- {s}")
    
    result = "\n".join(elements)
    
    # 限制长度
    if len(result) > max_length:
        result = result[:max_length] + "..."
    
    return result


# 测试代码
if __name__ == "__main__":
    # 测试 RAG 客户端
    client = RAGClient("http://192.168.1.211:8086/")
    
    print("测试 RAG 服务连接...")
    if client.is_available():
        print("✅ RAG 服务可用")
        
        stats = client.get_stats()
        if stats:
            print(f"📊 索引统计: {stats}")
        
        # 测试检索
        results = client.search("月下独行的场景", top_k=3)
        if results:
            print(f"🔍 检索到 {len(results)} 条结果")
            formatted = client.format_references(results)
            print(f"📝 格式化输出:\n{formatted}")
        else:
            print("❌ 未检索到结果")
    else:
        print("❌ RAG 服务不可用")
    
    # 测试关键元素提取
    test_content = """
    "你怎么会在这里？"林雪月惊讶地问道。
    
    陈晨心中一震，没想到会在这里遇到她。月光透过窗帘洒落在地板上，映出两人相对的身影。
    
    "我来找你。"他的声音有些沙哑，"有些话，我必须当面说清楚。"
    
    林雪月顿时红了眼眶，"都过去这么久了，还有什么好说的？"
    """
    
    print("\n测试关键元素提取...")
    elements = extract_key_elements(test_content)
    print(f"📝 提取的关键元素:\n{elements}")
