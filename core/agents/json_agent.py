"""Agent subsystem (extracted from aign_agents.py)."""

import time
import re
import tiktoken

from core.agents.base_agent import MarkdownAgent

class JSONMarkdownAgent(MarkdownAgent):
    """
    带JSON自动修复功能的MarkdownAgent
    
    功能：
    - 继承MarkdownAgent的所有功能
    - 支持JSON自动修复
    - 提供JSON格式的输入输出接口
    """
    
    def __init__(self, *args, **kwargs):
        """
        初始化JSONMarkdownAgent
        
        Args:
            *args, **kwargs: 传递给MarkdownAgent的参数
        """
        super().__init__(*args, **kwargs)
        
        # 尝试导入JSON修复工具
        try:
            from utils.json_auto_repair import JSONAutoRepair
            self.json_repairer = JSONAutoRepair(debug_mode=False)
        except ImportError:
            self.json_repairer = None
            print("⚠️ json_auto_repair模块未找到，JSON修复功能不可用")
        
    def _is_json_repair_enabled(self) -> bool:
        """
        检查JSON自动修复是否启用
        
        Returns:
            bool: 是否启用JSON修复
        """
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            return config_manager.get_json_auto_repair()
        except Exception:
            return True  # 默认启用
        
    def query_with_json_repair(self, user_input: str, max_attempts: int = 2) -> dict:
        """
        带JSON自动修复的查询方法
        
        Args:
            user_input: 用户输入
            max_attempts: 最大尝试次数（包括重试）
            
        Returns:
            dict: 包含content和total_tokens的响应
        """
        if not self.json_repairer or not self._is_json_repair_enabled():
            # 如果JSON修复不可用或未启用，回退到普通查询
            return self.query(user_input)
        
        for attempt in range(max_attempts):
            if attempt > 0:
                # 重试时增强提示词
                enhanced_prompt = f"""请务必返回严格的、无注释的、符合RFC 8259标准的JSON格式。

{user_input}

重要提醒：
1. 所有键和字符串值必须用双引号包裹
2. 不要包含任何注释（// 或 /* */）
3. 不要在最后一个元素后添加逗号
4. 布尔值使用 true/false，空值使用 null
5. 确保所有括号和方括号正确闭合"""
                
                print(f"🔄 第 {attempt + 1} 次尝试，使用增强提示词")
                response = self.query(enhanced_prompt)
            else:
                # 首次尝试使用原始提示词
                response = self.query(user_input)
            
            raw_content = response.get("content", "")
            # 移除可能存在的思考内容，避免干扰JSON解析
            if hasattr(self, '_remove_thinking_content'):
                raw_content = self._remove_thinking_content(raw_content)
            
            # 尝试修复JSON
            parsed_json, success, error_msg = self.json_repairer.repair_json(raw_content, max_attempts=1)
            
            if success:
                print(f"✅ JSON修复成功 (第 {attempt + 1} 次尝试)")
                # 将修复后的JSON转换回字符串作为content
                import json
                response["content"] = json.dumps(parsed_json, ensure_ascii=False, indent=2)
                response["parsed_json"] = parsed_json  # 添加解析后的JSON对象
                return response
            else:
                print(f"❌ JSON修复失败 (第 {attempt + 1} 次尝试): {error_msg}")
                if attempt < max_attempts - 1:
                    print(f"🔄 准备重试...")
                    time.sleep(1)  # 短暂延迟
        
        # 所有尝试都失败
        print("💥 JSON修复最终失败，返回原始内容")
        return response
    
    def getJSONOutput(self, input_content: str, required_keys: list = None) -> dict:
        """
        获取JSON格式的输出，支持自动修复
        
        Args:
            input_content: 输入内容
            required_keys: 必需的JSON键列表
            
        Returns:
            dict: 解析后的JSON对象
        """
        resp = self.query_with_json_repair(input_content)
        
        if "parsed_json" in resp:
            parsed_json = resp["parsed_json"]
            
            # 验证必需的键
            if required_keys:
                missing_keys = [key for key in required_keys if key not in parsed_json]
                if missing_keys:
                    raise ValueError(f"JSON缺少必需的键: {missing_keys}")
            
            return parsed_json
        else:
            raise ValueError("无法获取有效的JSON输出")
    
    def invokeJSON(self, inputs: dict, required_keys: list = None) -> dict:
        """
        调用JSON输出，支持自动修复
        
        Args:
            inputs: 输入字典
            required_keys: 必需的JSON键列表
            
        Returns:
            dict: 解析后的JSON对象
        """
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"
        
        # 调试信息
        print("📝 构建的JSON输入内容:")
        print("-" * 40)
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                print(f"   {k}: {v}")
        print("-" * 40)
        
        result = Retryer(self.getJSONOutput)(input_content, required_keys)
        return result


# 导出类和函数
__all__ = [
    'Retryer',
    'MarkdownAgent',
    'JSONMarkdownAgent'
]
