# -*- coding: utf-8 -*-
"""
测试长章节模式提示词转换的完整性
"""

import os
import sys

def test_embellisher_prompts():
    """测试所有润色提示词能正确加载"""
    print("=" * 60)
    print("测试润色提示词加载")
    print("=" * 60)
    
    long_chapter_dir = "f:/AI_Gen_Novel2/prompts/long_chapter"
    sys.path.insert(0, "f:/AI_Gen_Novel2")
    
    # 所有润色提示词文件
    embellisher_styles = [
        'chuanyue', 'dushi', 'duxin', 'fangxie', 'fanqie', 'guize', 'guyan',
        'huanyuan', 'kehuan', 'linggan', 'moshi', 'naodong', 'nvpin_danmei',
        'nvpin_nue', 'qihuan', 'renqing', 'shengji', 'siheyuan', 'snyder',
        'tianchong', 'tishen', 'tongren', 'wushi', 'xianxia', 'xitong',
        'xuanhuan', 'xuanyi', 'xuehua', 'xuehua_plus', 'yule', 'zhibo',
        'zhihu', 'zhongtian', 'zhuiqi', 'zhutian'
    ]
    
    passed = 0
    failed = 0
    
    for style in embellisher_styles:
        try:
            module_name = f"prompts.long_chapter.embellisher_prompt_{style}"
            module = __import__(module_name, fromlist=[''])
            prompt_var = f"novel_embellisher_{style}_prompt"
            prompt = getattr(module, prompt_var)
            
            # 验证输出格式
            if '# 润色内容' not in prompt:
                print(f"❌ {style}: 缺少 '# 润色内容' 标记")
                failed += 1
                continue
            
            if '# END' not in prompt:
                print(f"❌ {style}: 缺少 '# END' 标记")
                failed += 1
                continue
            
            if '===润色结果===' in prompt:
                print(f"❌ {style}: 仍包含旧的 '===润色结果===' 格式")
                failed += 1
                continue
            
            # 验证长度
            if len(prompt) < 2000:
                print(f"❌ {style}: 提示词过短 ({len(prompt)} 字符)")
                failed += 1
                continue
            
            print(f"✅ {style}: OK ({len(prompt)} 字符)")
            passed += 1
            
        except Exception as e:
            print(f"❌  {style}: 加载失败 - {e}")
            failed += 1
    
    print(f"\n润色提示词测试完成: {passed} 通过, {failed} 失败\n")
    return failed == 0

def test_writer_prompts():
    """测试所有写作提示词能正确加载"""
    print("=" * 60)
    print("测试写作提示词加载")
    print("=" * 60)
    
    sys.path.insert(0, "f:/AI_Gen_Novel2")
    
    # 所有写作提示词文件
    writer_styles = [
        'chuanyue', 'dushi', 'duxin', 'fanqie', 'guize', 'guyan',
        'huanyuan', 'kehuan', 'linggan', 'moshi', 'naodong', 'nvpin_danmei',
        'nvpin_nue', 'qihuan', 'renqing', 'shengji', 'siheyuan', 'snyder',
        'tianchong', 'tishen', 'tongren', 'wushi', 'xianxia', 'xitong',
        'xuanhuan', 'xuanyi', 'xuehua', 'xuehua_plus', 'yule', 'zhibo',
        'zhihu', 'zhongtian', 'zhuiqi', 'zhutian'
    ]
    
    passed = 0
    failed = 0
    
    for style in writer_styles:
        try:
            module_name = f"prompts.long_chapter.writer_prompt_{style}"
            module = __import__(module_name, fromlist=[''])
            prompt_var = f"novel_writer_{style}_prompt"
            prompt = getattr(module, prompt_var)
            
            # 验证输出格式
            if '# 段落' not in prompt:
                print(f" ❌ {style}: 缺少 '# 段落' 标记")
                failed += 1
                continue
            
            if '# 计划' not in prompt:
                print(f"❌ {style}: 缺少 '# 计划' 标记")
                failed += 1
                continue
            
            if '# 临时设定' not in prompt:
                print(f"❌ {style}: 缺少 '# 临时设定' 标记")
                failed += 1
                continue
            
            if '# END' not in prompt:
                print(f"❌ {style}: 缺少 '# END' 标记")
                failed += 1
                continue
            
            # 验证长度
            if len(prompt) < 1500:
                print(f"❌ {style}: 提示词过短 ({len(prompt)} 字符)")
                failed += 1
                continue
            
            print(f"✅ {style}: OK ({len(prompt)} 字符)")
            passed += 1
            
        except Exception as e:
            print(f"❌ {style}: 加载失败 - {e}")
            failed += 1
    
    print(f"\n写作提示词测试完成: {passed} 通过, {failed} 失败\n")
    return failed == 0

if __name__ == "__main__":
    embellisher_ok = test_embellisher_prompts()
    writer_ok = test_writer_prompts()
    
    print("=" * 60)
    if embellisher_ok and writer_ok:
        print("✅ 所有测试通过！")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查上方错误信息")
        print("=" * 60)
        sys.exit(1)
