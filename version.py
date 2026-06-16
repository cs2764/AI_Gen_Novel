#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 版本信息
"""

__version__ = "5.1.0"
__author__ = "AI Novel Generator Team"
__description__ = "AI 网络小说生成器 - GitHub发布版 (2026-06-16)"
__url__ = "https://github.com/cs2764/AI_Gen_Novel"

VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "description": __description__,
    "url": __url__,
    "features": [
        "全局设定系统（GlobalContextUpdater）：全新全局设定智能体，跟踪世界观设定、角色状态、势力关系等全局信息，每章生成后自动更新全局设定上下文",
        "生成防截断机制：大纲、伏笔、人物列表、详细大纲生成均加入===GENERATION_COMPLETE===结束标记检测和自动重试，最多重试2次后保留内容继续（不中断流程）",
        "伏笔重新生成按钮：WebUI新增独立的伏笔重新生成按钮，与标题和人物重新生成按钮功能一致",
        "最后一章优化：最后一章润色完成后直接结束，不再执行多余的记忆和全局设定更新",
        "章节进度修正：修复WebUI章节进度显示偏差（显示的章节号比实际生成的多1）",
        "默认参数优化：默认目标章节数50、默认伏笔数量5、默认高潮数量20",
        "正文/润色提示词增强：结尾正文和结尾润色提示词补齐与正常章节相同的审查、全局设定等新内容",
        "全局设定注入：正文生成和润色流程中自动注入全局设定上下文，增强世界观一致性",
        "记忆提示词增强：记忆生成提示词增加结构化输出格式和质量要求",
        "故事线提示词增强：故事线生成提示词增加详细度和结构要求",
        "自动保存增强：修复自动保存在某些场景下未正确持久化的问题",
        "Token缓存优化：新增输入字段重排序机制，提升DeepSeek等支持KV Cache的模型的缓存命中率",
        "oMLX AI提供商：新增Mac优化本地LLM推理服务器支持，OpenAI兼容API",
        "ZenMux AI提供商：统一AI模型路由服务，支持reasoning_effort思考强度控制和提供商路由",
        "故事线Markdown解析器：新增storyline_markdown_parser.py，支持Markdown↔dict双向转换，YAML front matter元数据",
        "标准模式模板提示词：新增AIGN_Prompt_Enhanced.py，提供更详细的标准模式写手和润色提示词",
        "需求扩展提示词重构：AIGN_Requirements_Expansion_Prompt.py代码精简优化",
        "故事线提示词改进：storyline_prompt和storyline_prompt_simple增强",
        "JSON智能修复增强：集成json_repair库替代手写正则修复，大幅提升JSON解析成功率和鲁棒性",
        "WebUI故事线进度改进：修复假超时问题（批次级进度追踪+15分钟停滞超时），完成后显示章节标题预览和失败统计",
        "LM Studio tool_choice修复：修正tool_choice格式为字符串类型，兼容LM Studio API",
        "【实验性】Fish Audio S2语气标记功能：替代CosyVoice，使用方括号[emotion]标记语法（功能尚未成熟，UI中已隐藏）",
        "【实验性】EPUB Fish Audio S2语气打标器：新增epub_fishaudio_tagger.py（功能尚未成熟，UI中已隐藏）",
        "【实验性】Fish Audio文本清理工具：新增fishaudio_cleaner.py（功能尚未成熟）",
        "润色截断检测与重试系统：全新embellish_truncation_detector模块，通过===EMBELLISH_COMPLETE===完成标识、句子完整性和长度比率三重检测润色内容是否被截断，支持3次自动重试",
        "标题长度严格限制：标题字数从不超过15字收紧为严格不超过10字，最佳长度4-8字",
        "发送长度检测移除：清理冗余的overlength content检测代码，简化状态显示",
        "伏笔/反转生成系统：全新伏笔设计专家智能体，根据大纲自动生成伏笔和反转，支持0-10个伏笔数量调节，伏笔上下文注入到人物、详细大纲和故事线生成中",
        "实时文本框同步：写作想法、写作要求、润色要求每次API调用都从WebUI文本框实时读取，支持生成过程中随时调整参数",
        "目标章节数引导大纲：目标章节数滑块移至创意输入面板，AI生成大纲时参考目标章节数合理安排剧情节奏",
        "Humanizer去AI味规则增强：基于Humanizer项目最新模式更新去AI写作痕迹规则，提升文本自然度",
        "TTS Markdown清理优化：内置strip_markdown功能，从生成流和批处理中移除Markdown格式(如**, *, #, _, ~等)，提升生成的文本在CosyVoice等TTS引擎中的语音朗读效果",
        "流式输出修正与章节控制：修复流式输出可能导致未完成残余文本与下一段被错误合并的问题；停止生成操作后自动关闭连接并丢弃不完整的块",
        "默认章节数调整：生成时默认章节数和对应的控制选项已优化",
        "LM Studio KV Cache自动重载：定期重载模型清空KV Cache，防止长篇生成输出异常",
        "LM Studio连续失败自动恢复：API连续失败时自动卸载重载模型后重试",
        "提供商配置标题栏实时更新：保存配置后顶部标题栏立即显示新配置",
        "大纲RAG集成：大纲、详细大纲、人物、标题生成均支持RAG参考",
        "LM Studio修复：修复API兼容性问题，移除遗留Completions接口",
        "Humanizer规则优化：集成到润色流程，适用于标题、小说内容和润色提示词",
        "思维链提取修复：确保思维链标签不包含在最终提取文本中",
        "Lambda3提供商：新增第三个OpenAI兼容提供商选项",
        "WebUI独立重新生成按钮：大纲、人物列表、标题可独立重新生成",
        "故事线生成流式控制台输出：实时显示生成进度",
        "WebUI数据集成：大纲、人物列表、标题从WebUI读取和编辑",
        "用户可在生成前自定义修改大纲、人物设定、标题",
        "NVIDIA思维链内容过滤功能",
        "小说生成断点续传功能",
        "生成进度自动保存与恢复",
        "存档文件管理系统",
        "RAG风格学习与智能参考系统",
        "Humanizer-zh去AI味功能",
        "Gradio 5.38.0 现代化界面",
        "完整的小说生成流程",
        "实时状态显示和进度跟踪",
        "用户确认机制防止误操作",
        "本地数据自动保存和加载",
        "统一的配置管理系统",
        "12个主流AI提供商支持",
        "智能错误处理和恢复",
        "分阶段生成状态显示",
        "故事线智能格式化",
        "自动生成和停止控制",
        "完善的参数验证",
        "类型安全的组件绑定",
        "简洁优化的用户界面",
        "API超时扩展至30分钟",
        "自动刷新功能默认开启",
        "生成按钮智能状态管理",
        "完善的安全措施和隐私保护",
        "详细的文档和安装指南",
        "开源友好的项目结构",
        "GitHub上传准备自动化",
        "文件清理和版本管理",
        "日期更新和系统文档",
        "测试文件组织和管理",
        "安全检查和隐私保护",
        "双语文档支持",
        "40+写作风格提示词系统",
        "精简模式提示词结构优化",
        "RAG风格学习与创作优化系统规划",
        "优化策略文档重组与精简",
        "NVIDIA AI提供商支持",
        "非精简模式上下文优化",
        "SiliconFlow详细Token统计",
        "流式输出与控制台显示优化",
        "Markdown故事线解析器双向转换"
    ],
    "ai_providers": [
        "OpenRouter",
        "Claude (Anthropic)",
        "Gemini (Google)",
        "DeepSeek",
        "LM Studio",
        "智谱 AI (GLM)",
        "阿里云通义千问",
        "Fireworks AI",
        "Grok (xAI)",
        "Lambda Labs",
        "SiliconFlow",
        "NVIDIA",
        "oMLX",
        "ZenMux"
    ]
}

def get_version():
    """获取版本信息"""
    return __version__

def get_full_version_info():
    """获取完整版本信息"""
    return VERSION_INFO

def print_version_info():
    """打印版本信息"""
    print(f"AI 网络小说生成器 v{__version__}")
    print(f"作者: {__author__}")
    print(f"描述: {__description__}")
    print(f"项目地址: {__url__}")
    print("\n主要功能:")
    for feature in VERSION_INFO["features"]:
        print(f"  - {feature}")
    print("\n支持的 AI 提供商:")
    for provider in VERSION_INFO["ai_providers"]:
        print(f"  - {provider}")

if __name__ == "__main__":
    print_version_info()
