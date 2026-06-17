"""Storyline error handling and statistics."""

from typing import Any, Dict, List, Optional


class StorylineErrorHandlerMixin:
    """Storyline error handling and statistics."""

    def _save_error_data(self, error_type: str, original_messages: List[Dict[str, str]],
                        response_content: str, error_details: str, attempt_number: int = 1):
        """保存错误数据到元数据文件以供分析"""
        try:
            # 创建错误数据目录
            error_dir = "metadata/storyline_errors"
            os.makedirs(error_dir, exist_ok=True)

            # 生成错误文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_filename = f"storyline_error_{timestamp}_{error_type}_attempt{attempt_number}.json"
            error_filepath = os.path.join(error_dir, error_filename)

            # 构建错误数据
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "provider": self.provider_name,
                "error_type": error_type,
                "attempt_number": attempt_number,
                "error_details": error_details,
                "original_messages": original_messages,
                "response_content": response_content,
                "response_length": len(response_content) if response_content else 0,
                "analysis": {
                    "has_json_markers": "```json" in response_content.lower() if response_content else False,
                    "has_braces": "{" in response_content and "}" in response_content if response_content else False,
                    "has_chapters_key": "chapters" in response_content.lower() if response_content else False,
                    "response_preview": response_content[:200] if response_content else "",
                    "response_suffix": response_content[-200:] if response_content and len(response_content) > 200 else ""
                },
                "repair_attempts": {
                    "json_candidates_found": 0,
                    "repair_methods_tried": [],
                    "reconstruction_attempted": False
                }
            }

            # 尝试分析JSON候选
            if response_content:
                candidates = self._extract_json_candidates(response_content)
                error_data["repair_attempts"]["json_candidates_found"] = len(candidates)
                if candidates:
                    error_data["repair_attempts"]["best_candidate"] = candidates[0][:500] if candidates[0] else ""

            # 保存错误数据
            with open(error_filepath, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)

            print(f"💾 错误数据已保存: {error_filepath}")

            # 更新错误统计
            self._update_error_statistics(error_type)

        except Exception as e:
            print(f"⚠️ 保存错误数据失败: {e}")


    def _update_error_statistics(self, error_type: str):
        """更新错误统计信息"""
        try:
            stats_file = "metadata/storyline_error_stats.json"

            # 读取现有统计
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {
                    "total_errors": 0,
                    "error_types": {},
                    "provider_stats": {},
                    "last_updated": None
                }

            # 更新统计
            stats["total_errors"] += 1
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
            stats["provider_stats"][self.provider_name] = stats["provider_stats"].get(self.provider_name, 0) + 1
            stats["last_updated"] = datetime.now().isoformat()

            # 保存统计
            os.makedirs("metadata", exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ 更新错误统计失败: {e}")


    def _log_successful_generation(self, method: str, attempt_number: int, result_data: Dict[str, Any]):
        """记录成功的生成案例以供分析"""
        try:
            success_dir = "metadata/storyline_success"
            os.makedirs(success_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            success_filename = f"storyline_success_{timestamp}_{method}_attempt{attempt_number}.json"
            success_filepath = os.path.join(success_dir, success_filename)

            success_data = {
                "timestamp": datetime.now().isoformat(),
                "provider": self.provider_name,
                "method": method,
                "attempt_number": attempt_number,
                "chapters_generated": len(result_data.get("chapters", [])),
                "result_structure": {
                    "has_batch_info": "batch_info" in result_data,
                    "chapter_fields": list(result_data.get("chapters", [{}])[0].keys()) if result_data.get("chapters") else []
                }
            }

            with open(success_filepath, 'w', encoding='utf-8') as f:
                json.dump(success_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ 记录成功案例失败: {e}")
        

    def get_statistics_report(self) -> str:
        """获取详细的统计报告"""
        stats = self.stats
        total = max(stats["total_attempts"], 1)  # 避免除零错误
        
        success_rate = (stats["successful_generations"] / total) * 100
        truncation_rate = (stats["truncation_detected"] / total) * 100
        repair_rate = (stats["json_repair_success"] / max(stats["truncation_detected"], 1)) * 100
        
        report = f"""
📊 故事线生成统计报告
{'='*50}
📈 总体统计:
   • 总尝试次数: {stats['total_attempts']}
   • 成功生成: {stats['successful_generations']}
   • 成功率: {success_rate:.1f}%

🚨 截断检测:
   • 检测到截断: {stats['truncation_detected']}
   • 截断率: {truncation_rate:.1f}%
   
🔧 修复统计:
   • JSON修复成功: {stats['json_repair_success']}
   • 修复成功率: {repair_rate:.1f}%
   • 渐进式降级使用: {stats['progressive_fallback_used']}
   • 提供商特定修复: {stats['provider_specific_fixes']}

🎯 当前提供商: {self.provider_name.upper()}
⚙️ 截断检测: {'启用' if self.truncation_detection['enabled'] else '禁用'}
{'='*50}
"""
        return report
    

    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_attempts": 0,
            "successful_generations": 0, 
            "truncation_detected": 0,
            "json_repair_success": 0,
            "progressive_fallback_used": 0,
            "provider_specific_fixes": 0
        }
        print("📊 统计信息已重置")
    

    def configure_truncation_detection(self, **kwargs):
        """配置截断检测参数"""
        for key, value in kwargs.items():
            if key in self.truncation_detection:
                old_value = self.truncation_detection[key]
                self.truncation_detection[key] = value
                print(f"🔧 截断检测配置已更新: {key} = {old_value} → {value}")
            else:
                print(f"⚠️ 未知配置项: {key}")
    

    def _record_success(self, method_type: str):
        """记录成功生成"""
        self.stats["successful_generations"] += 1
        
        if method_type in ["enhanced_json_repair", "traditional_repair"]:
            self.stats["json_repair_success"] += 1
        
        if method_type.startswith("progressive_"):
            self.stats["progressive_fallback_used"] += 1
            
        if self.provider_name == "lmstudio" and "truncation" in method_type:
            self.stats["provider_specific_fixes"] += 1
    

    def print_statistics(self):
        """打印统计报告到控制台"""
        print(self.get_statistics_report())
    

