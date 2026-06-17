"""Agent subsystem (extracted from aign_agents.py)."""

import time
import re
import tiktoken

"""
AIGN代理模块 - AI代理类和装饰器工具

本模块包含:
- Retryer装饰器：自动重试机制
- MarkdownAgent类：通用Markdown格式AI代理
- JSONMarkdownAgent类：JSON格式AI代理
- Agent创建和初始化函数
"""

import time
import re
import tiktoken


def _remove_thinking_content(response: str) -> str:
    """从AI响应中剔除思维链内容（Chain of Thought）
    
    某些模型（如NVIDIA的deepseek等）会在主内容中包含<think>标签的思考过程，
    这会影响后续的markdown解析。此函数负责清理这些标签。
    
    Args:
        response: AI模型的原始响应
        
    Returns:
        str: 剔除思维链后的内容
        
    处理的标签:
        - <think>...</think>
        - <thinking>...</thinking>
        - <reasoning>...</reasoning>
        - <reflection>...</reflection>
    """
    if not response:
        return response
    
    # 剔除常见的思维链标签及其内容（支持多行匹配）
    thinking_patterns = [
        r'<think>.*?</think>',
        r'<thinking>.*?</thinking>',
        r'<reasoning>.*?</reasoning>',
        r'<reflection>.*?</reflection>',
    ]
    
    result = response
    for pattern in thinking_patterns:
        result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)
    
    # 剔除残留的孤立思维链标签（开始或结束标签单独出现时）
    orphan_tag_patterns = [
        r'</think>',
        r'</thinking>',
        r'</reasoning>',
        r'</reflection>',
        r'<think>',
        r'<thinking>',
        r'<reasoning>',
        r'<reflection>',
    ]
    for tag in orphan_tag_patterns:
        result = re.sub(tag, '', result, flags=re.IGNORECASE)
    
    # 清理多余的空行
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


class TokenLimitError(Exception):
    """Token超限错误，用于标识响应超过token限制的情况"""
    pass


def Retryer(func=None, max_retries=3):
    """自动重试装饰器，用于处理API调用失败和流式输出问题
    
    当使用 LM Studio 时，连续失败 max_retries 次后会自动卸载模型以清空 KV Cache，
    然后再进行一轮额外重试。
    
    Args:
        func: 要装饰的函数
        max_retries: 最大重试次数，默认3次（连续失败3次后停止并报错）
        
    Returns:
        装饰后的函数
    """
    if func is None:
        def decorator(f):
            return Retryer(f, max_retries=max_retries)
        return decorator

    def wrapper(*args, **kwargs):
        # 是否已经执行过一次卸载重试
        unload_attempted = False
        
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                
                # 检查流式输出结果是否成功
                if isinstance(result, dict) and 'content' in result:
                    content = result['content']
                    # 使用智能重试判断逻辑
                    if hasattr(func, '__self__') and hasattr(func.__self__, 'should_retry_stream_output'):
                        should_retry = func.__self__.should_retry_stream_output(content)
                    else:
                        # 默认检查逻辑
                        should_retry = '流式输出失败' in content or '需要重试' in content
                    
                    if should_retry:
                        print(f"🔄 第{attempt + 1}次尝试失败，检测到流式输出问题: {content[:100]}...")
                        if attempt < max_retries - 1:  # 不是最后一次尝试
                            print(f"⏳ 等待重试... ({attempt + 1}/{max_retries})")
                            time.sleep(2.333)
                            continue
                        else:
                            # 达到最大重试次数，尝试卸载 LM Studio 模型
                            if not unload_attempted:
                                if _try_unload_lmstudio_on_failure():
                                    unload_attempted = True
                                    # 卸载成功后再试一次
                                    print(f"🔄 模型已卸载，进行最后一次重试...")
                                    try:
                                        result = func(*args, **kwargs)
                                        return result
                                    except Exception:
                                        pass
                            print(f"❌ 达到最大重试次数({max_retries})，放弃重试")
                            return result
                
                return result
                
            except TokenLimitError as e:
                # Token超限错误，不重试，直接抛出
                error_msg = str(e)
                print("-" * 30 + f"\n🛑 Token超限错误，停止重试：\n{error_msg}\n" + "-" * 30)
                raise
            except InterruptedError as e:
                # 用户主动中止，直接抛出
                print("-" * 30 + f"\n🛑 检测到中止信号，停止重试\n" + "-" * 30)
                raise
            except Exception as e:
                error_msg = str(e)
                print("-" * 30 + f"\n第{attempt + 1}次尝试失败：\n{error_msg}\n" + "-" * 30)
                
                # 检查是否是严重错误，需要立即重试
                if any(keyword in error_msg.lower() for keyword in ['model unloaded', 'model not found', 'connection', 'timeout']):
                    print(f"🚨 检测到严重错误，需要立即重试: {error_msg}")
                
                if attempt < max_retries - 1:  # 不是最后一次尝试
                    time.sleep(2.333)
                else:
                    # 达到最大重试次数，尝试卸载 LM Studio 模型后再试一次
                    if not unload_attempted:
                        if _try_unload_lmstudio_on_failure():
                            unload_attempted = True
                            print(f"🔄 模型已卸载，进行最后一次重试...")
                            try:
                                result = func(*args, **kwargs)
                                return result
                            except Exception as final_e:
                                print(f"❌ 卸载模型后重试仍然失败: {final_e}")
                                raise ValueError(f"重试{max_retries}次+卸载重试后仍然失败: {str(final_e)}")
                    
                    print(f"❌ 达到最大重试次数({max_retries})，放弃重试")
                    raise ValueError(f"重试{max_retries}次后仍然失败: {error_msg}")
        
        raise ValueError("失败")

    return wrapper


def _try_unload_lmstudio_on_failure() -> bool:
    """尝试在 API 连续失败后卸载 LM Studio 模型
    
    Returns:
        bool: 是否成功执行了卸载操作
    """
    try:
        from providers.lmstudio_model_manager import is_lmstudio_provider, handle_consecutive_failures
        if is_lmstudio_provider():
            return handle_consecutive_failures()
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ 尝试卸载 LM Studio 模型时出错: {e}")
    return False


