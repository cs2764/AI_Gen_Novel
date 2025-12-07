#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token监控工具 - 用于分析和优化Token消耗
"""

class TokenMonitor:
    """Token消耗监控器"""
    
    def __init__(self):
        self.stats = {
            'writer': {'count': 0, 'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0},
            'embellisher': {'count': 0, 'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0},
            'memory': {'count': 0, 'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0},
            'other': {'count': 0, 'total_tokens': 0, 'input_tokens': 0, 'output_tokens': 0},
        }
        self.input_breakdown = {}  # 详细的输入参数统计
    
    def estimate_tokens(self, text):
        """
        估算文本的token数量
        中文：约1.5字符/token
        英文：约4字符/token
        """
        if not text:
            return 0
        
        # 简单估算：中文为主的文本
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 中文约1.5字符/token，英文约4字符/token
        estimated_tokens = int(chinese_chars / 1.5 + other_chars / 4)
        return estimated_tokens
    
    def record_writer_call(self, inputs, output):
        """记录正文生成调用"""
        input_tokens = sum(self.estimate_tokens(str(v)) for v in inputs.values())
        output_tokens = self.estimate_tokens(str(output))
        
        self.stats['writer']['count'] += 1
        self.stats['writer']['input_tokens'] += input_tokens
        self.stats['writer']['output_tokens'] += output_tokens
        self.stats['writer']['total_tokens'] += input_tokens + output_tokens
        
        # 记录输入参数详情
        for key, value in inputs.items():
            if key not in self.input_breakdown:
                self.input_breakdown[key] = {'count': 0, 'total_tokens': 0}
            
            tokens = self.estimate_tokens(str(value))
            self.input_breakdown[key]['count'] += 1
            self.input_breakdown[key]['total_tokens'] += tokens
    
    def record_embellisher_call(self, inputs, output):
        """记录润色调用"""
        input_tokens = sum(self.estimate_tokens(str(v)) for v in inputs.values())
        output_tokens = self.estimate_tokens(str(output))
        
        self.stats['embellisher']['count'] += 1
        self.stats['embellisher']['input_tokens'] += input_tokens
        self.stats['embellisher']['output_tokens'] += output_tokens
        self.stats['embellisher']['total_tokens'] += input_tokens + output_tokens
    
    def record_memory_call(self, inputs, output):
        """记录记忆生成调用"""
        input_tokens = sum(self.estimate_tokens(str(v)) for v in inputs.values())
        output_tokens = self.estimate_tokens(str(output))
        
        self.stats['memory']['count'] += 1
        self.stats['memory']['input_tokens'] += input_tokens
        self.stats['memory']['output_tokens'] += output_tokens
        self.stats['memory']['total_tokens'] += input_tokens + output_tokens
    
    def get_report(self):
        """生成统计报告"""
        total_tokens = sum(s['total_tokens'] for s in self.stats.values())
        total_calls = sum(s['count'] for s in self.stats.values())
        
        report = []
        report.append("=" * 60)
        report.append("📊 Token消耗统计报告")
        report.append("=" * 60)
        
        # 总体统计
        report.append(f"\n总调用次数: {total_calls}")
        report.append(f"总Token消耗: {total_tokens:,}")
        report.append(f"平均每次调用: {total_tokens // total_calls if total_calls > 0 else 0:,} tokens")
        
        # 分类统计
        report.append("\n" + "-" * 60)
        report.append("分类统计:")
        report.append("-" * 60)
        
        for category, data in self.stats.items():
            if data['count'] > 0:
                percentage = (data['total_tokens'] / total_tokens * 100) if total_tokens > 0 else 0
                report.append(f"\n{category.upper()}:")
                report.append(f"  调用次数: {data['count']}")
                report.append(f"  输入Token: {data['input_tokens']:,}")
                report.append(f"  输出Token: {data['output_tokens']:,}")
                report.append(f"  总计: {data['total_tokens']:,} ({percentage:.1f}%)")
                report.append(f"  平均每次: {data['total_tokens'] // data['count']:,} tokens")
        
        # 输入参数详细统计（仅正文生成）
        if self.input_breakdown:
            report.append("\n" + "-" * 60)
            report.append("正文生成输入参数详细统计:")
            report.append("-" * 60)
            
            # 按token消耗排序
            sorted_params = sorted(
                self.input_breakdown.items(),
                key=lambda x: x[1]['total_tokens'],
                reverse=True
            )
            
            for param, data in sorted_params:
                if data['total_tokens'] > 0:
                    avg_tokens = data['total_tokens'] // data['count'] if data['count'] > 0 else 0
                    report.append(f"\n  {param}:")
                    report.append(f"    使用次数: {data['count']}")
                    report.append(f"    总Token: {data['total_tokens']:,}")
                    report.append(f"    平均: {avg_tokens:,} tokens/次")
        
        # 优化建议
        report.append("\n" + "=" * 60)
        report.append("💡 优化建议:")
        report.append("=" * 60)
        
        suggestions = self._generate_suggestions()
        for i, suggestion in enumerate(suggestions, 1):
            report.append(f"{i}. {suggestion}")
        
        report.append("=" * 60)
        
        return '\n'.join(report)
    
    def _generate_suggestions(self):
        """生成优化建议"""
        suggestions = []
        
        # 分析正文生成的输入参数
        if self.input_breakdown:
            sorted_params = sorted(
                self.input_breakdown.items(),
                key=lambda x: x[1]['total_tokens'],
                reverse=True
            )
            
            # 找出消耗最大的参数
            top_params = sorted_params[:3]
            for param, data in top_params:
                avg = data['total_tokens'] // data['count'] if data['count'] > 0 else 0
                if avg > 500:  # 如果平均超过500 tokens
                    if param == '大纲':
                        suggestions.append(f"'{param}'平均消耗{avg}tokens，建议使用大纲优化器提取相关片段")
                    elif param == '前文记忆':
                        suggestions.append(f"'{param}'平均消耗{avg}tokens，建议降低记忆长度限制")
                    elif param in ['前五章总结', '后五章梗概']:
                        suggestions.append(f"'{param}'平均消耗{avg}tokens，建议减少到前后2-3章")
                    elif param == '人物列表':
                        suggestions.append(f"'{param}'平均消耗{avg}tokens，建议只发送相关角色信息")
                    else:
                        suggestions.append(f"'{param}'平均消耗{avg}tokens，建议进行压缩或精简")
        
        # 分析正文生成vs润色的比例
        writer_tokens = self.stats['writer']['total_tokens']
        embellisher_tokens = self.stats['embellisher']['total_tokens']
        
        if writer_tokens > 0 and embellisher_tokens > 0:
            ratio = writer_tokens / (writer_tokens + embellisher_tokens)
            if ratio > 0.6:
                suggestions.append(f"正文生成占比{ratio*100:.1f}%，建议优先优化正文生成阶段")
        
        # 如果没有具体建议，给出通用建议
        if not suggestions:
            suggestions.append("当前Token消耗在合理范围内")
            suggestions.append("可以考虑启用精简模式和长章节模式进一步优化")
        
        return suggestions
    
    def save_report(self, filename='token_report.txt'):
        """保存报告到文件"""
        report = self.get_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Token统计报告已保存到: {filename}")


# 全局监控器实例
_global_monitor = None

def get_token_monitor():
    """获取全局Token监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = TokenMonitor()
    return _global_monitor


# 导出
__all__ = ['TokenMonitor', 'get_token_monitor']
