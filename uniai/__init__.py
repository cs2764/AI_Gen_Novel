try:
    from .aliAI import aliChatLLM
except ImportError:
    aliChatLLM = None
from .deepseekAI import deepseekChatLLM
# from .zhipuAI import zhipuChatLLM
from .lmstudioAI import lmstudioChatLLM
try:
    from .geminiAI import geminiChatLLM
except ImportError:
    geminiChatLLM = None
from .openrouterAI import openrouterChatLLM
try:
    from .claudeAI import claudeChatLLM
except ImportError:
    claudeChatLLM = None
from .grokAI import grokChatLLM
from .lambdaAI import lambdaChatLLM
from .siliconflowAI import siliconflowChatLLM
from .nvidiaAI import nvidiaChatLLM
