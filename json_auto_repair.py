#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON自动修复工具
使用 json_repair 库智能修复大模型返回的不规范JSON结构
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple, Union

try:
    import json_repair as _json_repair
    JSON_REPAIR_LIB_AVAILABLE = True
except ImportError:
    JSON_REPAIR_LIB_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONAutoRepair:
    """JSON自动修复器（基于 json_repair 库）"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.repair_attempts = []
        
    def repair_json(self, raw_content: str, max_attempts: int = 2) -> Tuple[Optional[Dict], bool, str]:
        """
        核心工作流：修复与重试策略
        
        Args:
            raw_content: 原始返回内容
            max_attempts: 最大尝试次数（默认2次：1次初始 + 1次重试）
            
        Returns:
            Tuple[Optional[Dict], bool, str]: (解析结果, 是否成功, 错误信息)
        """
        self.repair_attempts = []
        
        for attempt in range(max_attempts):
            if self.debug_mode:
                logger.info(f"🔄 开始第 {attempt + 1} 次尝试修复JSON")
            
            # 执行完整的修复流程
            result, success, error_msg = self._execute_repair_workflow(raw_content, attempt + 1)
            
            if success:
                if self.debug_mode:
                    logger.info(f"✅ 第 {attempt + 1} 次尝试成功")
                return result, True, ""
            else:
                if self.debug_mode:
                    logger.warning(f"❌ 第 {attempt + 1} 次尝试失败: {error_msg}")
                self.repair_attempts.append({
                    'attempt': attempt + 1,
                    'original_content': raw_content,
                    'error': error_msg
                })
        
        # 所有尝试都失败
        if self.debug_mode:
            logger.error("💥 所有修复尝试均失败，跳过此次任务")
        
        return None, False, f"经过 {max_attempts} 次尝试后仍无法修复JSON格式"
    
    def _execute_repair_workflow(self, content: str, attempt_num: int) -> Tuple[Optional[Dict], bool, str]:
        """
        执行单次修复流程
        
        流水线：直接解析 → json_repair.loads() → 提取JSON内容 + json_repair → 失败
        
        Args:
            content: 待修复的内容
            attempt_num: 尝试次数
            
        Returns:
            Tuple[Optional[Dict], bool, str]: (解析结果, 是否成功, 错误信息)
        """
        # 1. 直接解析
        result, success, error = self._direct_parse(content)
        if success:
            if self.debug_mode:
                logger.info(f"✅ 直接解析成功 (尝试 {attempt_num})")
            return result, True, ""
        
        # 2. 使用 json_repair 库修复（首选方案）
        if JSON_REPAIR_LIB_AVAILABLE:
            try:
                repaired = _json_repair.loads(content)
                if isinstance(repaired, (dict, list)):
                    if self.debug_mode:
                        logger.info(f"✅ json_repair库修复成功 (尝试 {attempt_num})")
                    return repaired, True, ""
                else:
                    if self.debug_mode:
                        logger.warning(f"⚠️ json_repair返回了非dict/list类型: {type(repaired)}")
            except Exception as e:
                if self.debug_mode:
                    logger.warning(f"⚠️ json_repair库修复失败: {e}")
        
        # 3. 提取JSON内容后再用 json_repair 修复
        extracted = self._extract_json_content(content)
        if extracted != content:
            # 先直接解析提取后的内容
            result, success, error = self._direct_parse(extracted)
            if success:
                if self.debug_mode:
                    logger.info(f"✅ 提取JSON内容后直接解析成功 (尝试 {attempt_num})")
                return result, True, ""
            
            # 用 json_repair 修复提取后的内容
            if JSON_REPAIR_LIB_AVAILABLE:
                try:
                    repaired = _json_repair.loads(extracted)
                    if isinstance(repaired, (dict, list)):
                        if self.debug_mode:
                            logger.info(f"✅ 提取+json_repair修复成功 (尝试 {attempt_num})")
                        return repaired, True, ""
                except Exception as e:
                    if self.debug_mode:
                        logger.warning(f"⚠️ 提取+json_repair修复失败: {e}")
        
        # 修复失败
        return None, False, f"修复失败: {error}"
    
    def _direct_parse(self, content: str) -> Tuple[Optional[Dict], bool, str]:
        """直接解析JSON"""
        try:
            result = json.loads(content)
            return result, True, ""
        except json.JSONDecodeError as e:
            return None, False, str(e)
        except Exception as e:
            return None, False, f"解析异常: {str(e)}"
    
    def _extract_json_content(self, content: str) -> str:
        """提取JSON内容，去除无关文本"""
        # 寻找第一个 { 或 [ 和最后一个 } 或 ]
        start_brace = content.find('{')
        start_bracket = content.find('[')
        
        # 确定起始位置
        if start_brace == -1 and start_bracket == -1:
            return content
        elif start_brace == -1:
            start_pos = start_bracket
            end_char = ']'
        elif start_bracket == -1:
            start_pos = start_brace
            end_char = '}'
        else:
            start_pos = min(start_brace, start_bracket)
            end_char = '}' if start_pos == start_brace else ']'
        
        # 寻找对应的结束位置
        end_pos = content.rfind(end_char)
        
        if start_pos != -1 and end_pos != -1 and end_pos > start_pos:
            extracted = content[start_pos:end_pos + 1]
            if self.debug_mode:
                logger.info(f"📋 提取JSON内容: {len(extracted)} 字符")
            return extracted
        
        return content
    
    def get_repair_history(self) -> list:
        """获取修复历史记录"""
        return self.repair_attempts.copy()


# 便捷函数
def repair_json_string(content: str, debug_mode: bool = False) -> Tuple[Optional[Dict], bool, str]:
    """
    便捷函数：修复JSON字符串
    
    Args:
        content: 待修复的JSON字符串
        debug_mode: 是否开启调试模式
        
    Returns:
        Tuple[Optional[Dict], bool, str]: (解析结果, 是否成功, 错误信息)
    """
    repairer = JSONAutoRepair(debug_mode=debug_mode)
    return repairer.repair_json(content)


# 测试函数
def test_json_repair():
    """测试JSON修复功能"""
    test_cases = [
        # 正常JSON
        '{"key": "value"}',
        
        # 包含无关文本
        '这是您要的JSON：\n{"key": "value"}\n好的',
        
        # 结尾逗号
        '{"key": "value",}',
        
        # 包含注释
        '{"key": "value" // 这是注释}',
        
        # 非标准布尔值
        '{"valid": True, "data": None}',
        
        # 单引号
        "{'key': 'value'}",
        
        # 缺少引号的键
        '{key: "value"}',
        
        # 缺失括号
        '{"key": "value"',
        
        # 复杂错误
        '''这是JSON：
        {
            name: "test", // 名称
            valid: True,
            data: None,
            items: [1, 2,],
        ''',
    ]
    
    repairer = JSONAutoRepair(debug_mode=True)
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"测试案例 {i+1}:")
        print(f"原始内容: {repr(test_case)}")
        
        result, success, error = repairer.repair_json(test_case)
        
        if success:
            print(f"✅ 修复成功: {result}")
        else:
            print(f"❌ 修复失败: {error}")


if __name__ == "__main__":
    test_json_repair()