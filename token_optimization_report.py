#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token优化效果对比报告生成器
"""

from token_optimization_config import TokenOptimizationConfig


class OptimizationReport:
    """优化效果对比报告"""
    
    @staticmethod
    def estimate_tokens(text_length):
        """估算token数量（中文为主）"""
        return int(text_length / 1.5)
    
    @classmethod
    def generate_comparison_report(cls):
        """生成优化前后对比报告"""
        
        print("=" * 80)
        print("📊 Token优化效果预估报告")
        print("=" * 80)
        
        # 假设的原始数据（基于用户提供的统计）
        original_stats = {
            'total_calls': 2753,  # 正文生成调用次数
            'total_tokens': 24933007,  # 正文生成总token
            'avg_per_call': 9056,  # 平均每次调用
        }
        
        print("\n📈 原始数据（优化前）:")
        print(f"  • 正文生成调用次数: {original_stats['total_calls']:,}")
        print(f"  • 正文生成总Token: {original_stats['total_tokens']:,}")
        print(f"  • 平均每次调用: {original_stats['avg_per_call']:,} tokens")
        
        # 估算各部分的token消耗（基于典型场景）
        print("\n" + "-" * 80)
        print("📊 各部分Token消耗估算（优化前）:")
        print("-" * 80)
        
        # 标准模式的典型输入
        standard_inputs = {
            '大纲': 2000,  # 字符
            '前文记忆': 1800,
            '临时设定': 800,
            '人物列表': 1500,
            '前五章总结': 2000,
            '后五章梗概': 2000,
            '上一章原文': 3000,
            '其他': 1000,
        }
        
        total_input_chars = sum(standard_inputs.values())
        total_input_tokens = cls.estimate_tokens(total_input_chars)
        
        for key, chars in standard_inputs.items():
            tokens = cls.estimate_tokens(chars)
            percentage = (tokens / total_input_tokens * 100)
            print(f"  • {key}: {chars} 字符 ≈ {tokens:,} tokens ({percentage:.1f}%)")
        
        print(f"\n  总计: {total_input_chars} 字符 ≈ {total_input_tokens:,} tokens/次")
        
        # 优化后的估算
        print("\n" + "=" * 80)
        print("✨ 优化后估算（长章节精简模式）:")
        print("=" * 80)
        
        optimized_inputs = {
            '大纲（优化）': 500,  # 使用超精简大纲
            '前文记忆（优化）': 400,  # 长章节模式500字限制
            '临时设定（优化）': 400,  # 长章节模式400字限制
            '前2章故事线': 600,  # 替代前5章总结
            '后2章故事线': 600,  # 替代后5章梗概
            '其他': 500,
        }
        
        optimized_total_chars = sum(optimized_inputs.values())
        optimized_total_tokens = cls.estimate_tokens(optimized_total_chars)
        
        for key, chars in optimized_inputs.items():
            tokens = cls.estimate_tokens(chars)
            percentage = (tokens / optimized_total_tokens * 100)
            print(f"  • {key}: {chars} 字符 ≈ {tokens:,} tokens ({percentage:.1f}%)")
        
        print(f"\n  总计: {optimized_total_chars} 字符 ≈ {optimized_total_tokens:,} tokens/次")
        
        # 计算优化效果
        print("\n" + "=" * 80)
        print("💡 优化效果分析:")
        print("=" * 80)
        
        tokens_saved_per_call = total_input_tokens - optimized_total_tokens
        percentage_saved = (tokens_saved_per_call / total_input_tokens * 100)
        
        print(f"\n单次调用优化:")
        print(f"  • 优化前: {total_input_tokens:,} tokens")
        print(f"  • 优化后: {optimized_total_tokens:,} tokens")
        print(f"  • 节省: {tokens_saved_per_call:,} tokens ({percentage_saved:.1f}%)")
        
        # 基于实际调用次数估算总节省
        total_saved = tokens_saved_per_call * original_stats['total_calls']
        new_total = original_stats['total_tokens'] - total_saved
        
        print(f"\n总体优化效果（基于{original_stats['total_calls']}次调用）:")
        print(f"  • 优化前总Token: {original_stats['total_tokens']:,}")
        print(f"  • 预计优化后: {new_total:,}")
        print(f"  • 预计节省: {total_saved:,} tokens ({percentage_saved:.1f}%)")
        
        # 详细分析各项优化
        print("\n" + "-" * 80)
        print("📋 各项优化详情:")
        print("-" * 80)
        
        optimizations = [
            ('大纲优化', 2000, 500, '使用章节相关片段'),
            ('前文记忆压缩', 1800, 400, '长章节模式≤500字'),
            ('临时设定优化', 800, 400, '智能压缩和清理'),
            ('章节上下文减少', 4000, 1200, '前后5章→前后2章'),
            ('移除冗余信息', 3000, 0, '移除上一章原文等'),
        ]
        
        print(f"\n{'优化项':<20} {'优化前':<12} {'优化后':<12} {'节省':<12} {'说明'}")
        print("-" * 80)
        
        for name, before, after, desc in optimizations:
            saved = before - after
            saved_tokens = cls.estimate_tokens(saved)
            print(f"{name:<20} {before:>10}字 {after:>10}字 {saved_tokens:>10}t {desc}")
        
        # 成本估算（假设）
        print("\n" + "=" * 80)
        print("💰 成本节省估算（假设价格）:")
        print("=" * 80)
        
        # 假设价格：每1M tokens = $2（示例价格）
        price_per_million = 2.0
        
        original_cost = (original_stats['total_tokens'] / 1_000_000) * price_per_million
        optimized_cost = (new_total / 1_000_000) * price_per_million
        cost_saved = original_cost - optimized_cost
        
        print(f"\n  • 优化前成本: ${original_cost:.2f}")
        print(f"  • 优化后成本: ${optimized_cost:.2f}")
        print(f"  • 节省成本: ${cost_saved:.2f} ({percentage_saved:.1f}%)")
        
        print("\n" + "=" * 80)
        print("✅ 优化建议:")
        print("=" * 80)
        print("""
1. ✅ 已启用精简模式 + 长章节模式
2. ✅ 前文记忆压缩至500字（长章节）/ 300字（普通）
3. ✅ 大纲智能优化，只发送相关片段
4. ✅ 临时设定自动压缩和清理
5. ✅ 章节上下文从5章减少到2章

预计可减少正文生成Token消耗约 {:.1f}%
        """.format(percentage_saved))
        
        print("=" * 80)
    
    @classmethod
    def save_report(cls, filename='token_optimization_report.txt'):
        """保存报告到文件"""
        import sys
        from io import StringIO
        
        # 捕获print输出
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        cls.generate_comparison_report()
        
        report_content = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 优化报告已保存到: {filename}")
        
        # 同时打印到控制台
        print(report_content)


# 导出
__all__ = ['OptimizationReport']


# 使用示例
if __name__ == '__main__':
    OptimizationReport.generate_comparison_report()
