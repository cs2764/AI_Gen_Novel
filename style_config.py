#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""风格配置管理模块"""

STYLE_MAPPING = {
    "无": "none",
    "仙侠文": "xianxia",
    "都市爽文": "dushi",
    "悬疑小说": "xuanyi",
    "甜宠爽文": "tianchong",
    "快穿文/穿越文": "chuanyue",
    "玄幻小说": "xuanhuan",
    "科幻小说": "kehuan",
    "系统文": "xitong",
    "古言小说": "guyan",
    "升级流": "shengji",
    "女频虐文": "nvpin_nue",
    "种田文": "zhongtian",
    "人情小说": "renqing",
    "同人文": "tongren",
    "四合院流": "siheyuan",
    "奇幻小说": "qihuan",
    "女频耽美虐文": "nvpin_danmei",
    "娱乐文": "yule",
    "小说仿写": "fangxie",
    "巫师流": "wushi",
    "末世文": "moshi",
    "知乎短篇": "zhihu",
    "番茄过稿": "fanqie",
    "直播流": "zhibo",
    "脑洞文": "naodong",
    "规则怪谈": "guize",
    "诸天无限文": "zhutian",
    "读心术文": "duxin",
    "追妻火葬场": "zhuiqi",
    "替身文": "tishen",
    "雪花写作法": "xuehua",
    "雪花写作法增强版": "xuehua_plus",
    "换元法创作": "huanyuan",
    "斯奈德节拍创作": "snyder",
    "故事灵感": "linggan",
    "幼儿故事": "youer",
    "儿童绘本": "ertong_huiben",
    "儿童童话": "ertong_tonghua",
    "金庸武侠": "jinyong",
}

def get_style_choices():
    return ["无"] + [s for s in STYLE_MAPPING.keys() if s != "无"]

def get_style_code(style_name):
    return STYLE_MAPPING.get(style_name, "none")

def get_style_prompt_paths(style_code, mode="compact"):
    if style_code == "none":
        if mode == "compact":
            return {"writer_prompt": "prompts/compact/writer_prompt.py", "embellisher_prompt": "prompts/compact/embellisher_prompt.py"}
        else:
            return {"writer_prompt": "prompts/long_chapter/writer_prompt.py", "embellisher_prompt": "prompts/long_chapter/embellisher_prompt.py"}
    else:
        if mode == "compact":
            return {"writer_prompt": f"prompts/compact/writer_prompt_{style_code}.py", "embellisher_prompt": f"prompts/compact/embellisher_prompt_{style_code}.py"}
        else:
            return {"writer_prompt": f"prompts/long_chapter/writer_prompt_{style_code}.py", "embellisher_prompt": f"prompts/long_chapter/embellisher_prompt_{style_code}.py"}

def get_style_description(style_name):
    descriptions = {
        "无": "使用默认提示词，不应用特定风格",
        "仙侠文": "融入传统文化、修炼体系、古典韵味",
        "都市爽文": "生活化词汇、情绪性修辞、爽点设置",
        "幼儿故事": "适合0-6岁幼儿，语言简单、温馨有趣、富有教育意义",
        "儿童绘本": "适合3-8岁儿童，文字精炼、画面感强、诗意优美",
        "儿童童话": "适合6-12岁儿童，奇幻想象、善恶分明、寓意深刻",
    }
    return descriptions.get(style_name, "")
