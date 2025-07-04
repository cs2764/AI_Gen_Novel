# AI小说生成器 - LLM配置
# 现在通过动态配置管理器管理AI提供商设置

from dynamic_config_manager import get_dynamic_chatllm
from config_manager import get_chatllm

# 尝试从动态配置加载，如果失败则回退到文件配置
try:
    chatLLM = get_dynamic_chatllm()
    print("✅ 使用动态配置管理器")
except:
    try:
        chatLLM = get_chatllm()
        print("✅ 使用文件配置管理器")
    except:
        print("❌ 配置加载失败，请检查配置")
        chatLLM = None

if __name__ == "__main__":

    content = "请用一个成语介绍你自己"
    messages = [{"role": "user", "content": content}]

    resp = chatLLM(messages)
    print(resp)

    for resp in chatLLM(messages, stream=True):
        print(resp)
