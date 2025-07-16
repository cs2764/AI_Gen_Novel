#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""故事线生成错误分析工具"""

import json
import os
import glob
from datetime import datetime
from collections import defaultdict

def analyze_storyline_errors():
    """分析故事线生成错误数据"""
    
    print("=== 故事线生成错误分析报告 ===")
    
    # 检查错误数据目录
    error_dir = "metadata/storyline_errors"
    success_dir = "metadata/storyline_success"
    
    if not os.path.exists(error_dir):
        print("❌ 错误数据目录不存在")
        return
    
    # 读取所有错误文件
    error_files = glob.glob(os.path.join(error_dir, "*.json"))
    success_files = glob.glob(os.path.join(success_dir, "*.json")) if os.path.exists(success_dir) else []
    
    print(f"📊 找到 {len(error_files)} 个错误记录，{len(success_files)} 个成功记录")
    
    if not error_files:
        print("✅ 暂无错误记录")
        return
    
    # 分析错误数据
    error_stats = defaultdict(int)
    provider_stats = defaultdict(int)
    error_details = []
    
    for error_file in error_files:
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                error_data = json.load(f)
            
            error_type = error_data.get('error_type', 'unknown')
            provider = error_data.get('provider', 'unknown')
            
            error_stats[error_type] += 1
            provider_stats[provider] += 1
            
            error_details.append({
                'file': os.path.basename(error_file),
                'timestamp': error_data.get('timestamp'),
                'error_type': error_type,
                'provider': provider,
                'attempt': error_data.get('attempt_number', 1),
                'response_length': error_data.get('response_length', 0),
                'has_json_markers': error_data.get('analysis', {}).get('has_json_markers', False),
                'has_braces': error_data.get('analysis', {}).get('has_braces', False),
                'has_chapters_key': error_data.get('analysis', {}).get('has_chapters_key', False),
                'candidates_found': error_data.get('repair_attempts', {}).get('json_candidates_found', 0),
                'preview': error_data.get('analysis', {}).get('response_preview', '')[:100]
            })
            
        except Exception as e:
            print(f"⚠️ 读取错误文件失败 {error_file}: {e}")
    
    # 打印统计报告
    print(f"\n📈 错误类型统计:")
    for error_type, count in sorted(error_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type}: {count} 次")
    
    print(f"\n🔧 提供商统计:")
    for provider, count in sorted(provider_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {provider}: {count} 次错误")
    
    # 分析最常见的错误
    print(f"\n🔍 详细错误分析:")
    
    # 按错误类型分组
    errors_by_type = defaultdict(list)
    for error in error_details:
        errors_by_type[error['error_type']].append(error)
    
    for error_type, errors in errors_by_type.items():
        print(f"\n--- {error_type} ({len(errors)} 次) ---")
        
        # 分析这类错误的特征
        has_json_markers = sum(1 for e in errors if e['has_json_markers'])
        has_braces = sum(1 for e in errors if e['has_braces'])
        has_chapters = sum(1 for e in errors if e['has_chapters_key'])
        avg_length = sum(e['response_length'] for e in errors) / len(errors) if errors else 0
        avg_candidates = sum(e['candidates_found'] for e in errors) / len(errors) if errors else 0
        
        print(f"  特征分析:")
        print(f"    - 包含JSON标记: {has_json_markers}/{len(errors)} ({has_json_markers/len(errors)*100:.1f}%)")
        print(f"    - 包含大括号: {has_braces}/{len(errors)} ({has_braces/len(errors)*100:.1f}%)")
        print(f"    - 包含chapters关键字: {has_chapters}/{len(errors)} ({has_chapters/len(errors)*100:.1f}%)")
        print(f"    - 平均响应长度: {avg_length:.0f} 字符")
        print(f"    - 平均找到候选: {avg_candidates:.1f} 个")
        
        # 显示最近的几个错误示例
        recent_errors = sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:3]
        print(f"  最近错误示例:")
        for i, error in enumerate(recent_errors, 1):
            print(f"    {i}. {error['timestamp']} - 尝试{error['attempt']} - {error['response_length']}字符")
            if error['preview']:
                print(f"       预览: {error['preview']}...")
    
    # 分析成功案例
    if success_files:
        print(f"\n✅ 成功案例分析:")
        success_stats = defaultdict(int)
        
        for success_file in success_files:
            try:
                with open(success_file, 'r', encoding='utf-8') as f:
                    success_data = json.load(f)
                
                method = success_data.get('method', 'unknown')
                success_stats[method] += 1
                
            except Exception as e:
                print(f"⚠️ 读取成功文件失败 {success_file}: {e}")
        
        print(f"  成功方法统计:")
        for method, count in sorted(success_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"    {method}: {count} 次成功")
    
    # 读取总体统计
    stats_file = "metadata/storyline_error_stats.json"
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                total_stats = json.load(f)
            
            print(f"\n📊 总体统计:")
            print(f"  总错误数: {total_stats.get('total_errors', 0)}")
            print(f"  最后更新: {total_stats.get('last_updated', 'unknown')}")
            
        except Exception as e:
            print(f"⚠️ 读取总体统计失败: {e}")
    
    # 提供改进建议
    print(f"\n💡 改进建议:")
    
    if error_stats.get('json_parse_error', 0) > 0:
        print("  - JSON解析错误较多，考虑改进提示词格式要求")
    
    if error_stats.get('json_repair_failed', 0) > 0:
        print("  - JSON修复失败较多，考虑增强修复算法")
    
    if error_stats.get('no_content_returned', 0) > 0:
        print("  - API无返回内容，检查网络连接和API配置")
    
    # 计算成功率
    total_attempts = len(error_files) + len(success_files)
    if total_attempts > 0:
        success_rate = len(success_files) / total_attempts * 100
        print(f"\n📈 当前成功率: {success_rate:.1f}% ({len(success_files)}/{total_attempts})")

def clean_old_error_data(days_to_keep=30):
    """清理旧的错误数据"""
    print(f"\n🧹 清理 {days_to_keep} 天前的错误数据...")
    
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    for directory in ["metadata/storyline_errors", "metadata/storyline_success"]:
        if not os.path.exists(directory):
            continue
        
        files = glob.glob(os.path.join(directory, "*.json"))
        cleaned_count = 0
        
        for file_path in files:
            try:
                # 从文件名提取日期
                filename = os.path.basename(file_path)
                if "storyline_" in filename:
                    date_part = filename.split("_")[2]  # 格式: storyline_error_20250715_...
                    file_date = datetime.strptime(date_part, "%Y%m%d")
                    
                    if file_date < cutoff_date:
                        os.remove(file_path)
                        cleaned_count += 1
                        
            except Exception as e:
                print(f"⚠️ 清理文件失败 {file_path}: {e}")
        
        print(f"  {directory}: 清理了 {cleaned_count} 个文件")

if __name__ == "__main__":
    analyze_storyline_errors()
    
    # 询问是否清理旧数据
    response = input("\n是否清理30天前的旧错误数据? (y/N): ")
    if response.lower() == 'y':
        clean_old_error_data()
