import os
import json
import re
from openai import OpenAI

# 从各个可能的地方寻找API Key
def get_api_key():
    api_key = os.environ.get("NVIDIA_API_KEY")
    if api_key: return api_key
    try:
        with open("runtime_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("providers", {}).get("nvidia", {}).get("api_key")
    except:
        pass
    return None

def extract_prompt_from_log(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 input_content 部分
    start_marker = "=== 输入提示词 (input_content) ==="
    end_marker = "=== 思维链内容 (reasoning_content) ==="
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("Error: Could not find input content start marker")
        return None
        
    # Skip lines until real content starts (skip header lines)
    lines = content[start_pos:].split('\n')
    real_start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("===") and i > 0: # End of header block
            real_start_idx = i + 1
            break
            
    # Find end position
    end_pos = content.find(end_marker)
    if end_pos == -1:
        print("Warning: Could not find reasoning content start marker, using end of file")
        end_pos = len(content)
        
    prompt_text = content[start_pos:end_pos]
    # Remove the header lines we skipped above more roughly
    # Let's just use a regex to extract between the divider lines
    
    match = re.search(r'=== 输入提示词 \(input_content\) ===\n.*?\n={60}\n(.*?)\n\n={60}\n', content, re.DOTALL)
    if match:
        return match.group(1)
    else:
        print("Regex extraction failed, trying simple slice")
        # Fallback
        header_end = content.find('='*60, start_pos + len(start_marker)) + 60
        return content[header_end:end_pos].strip()

prompt = extract_prompt_from_log(r"F:\AI_Gen_Novel2\output\api_parse_failure.txt")
if not prompt:
    print("Failed to extract prompt")
    exit(1)

print(f"Extracted prompt length: {len(prompt)} chars")

api_key = get_api_key()
if not api_key:
    print("Error: NVIDIA_API_KEY not found")
    exit(1)

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = api_key
)

print("Sending request with extracted prompt...")
try:
    completion = client.chat.completions.create(
      model="deepseek-ai/deepseek-v3.2",
      messages=[{"role":"user","content":prompt}],
      temperature=1,
      top_p=0.95,
      max_tokens=8192,
      extra_body={"chat_template_kwargs": {"thinking":True}},
      stream=True
    )

    print("Receiving stream...")
    reasoning_len = 0
    content_len = 0
    
    has_reasoning = False
    has_content = False
    
    for chunk in completion:
        if not getattr(chunk, "choices", None):
            continue
            
        # Check reasoning
        reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
        if reasoning:
            if not has_reasoning:
                print("\n[Reasoning Started]")
                has_reasoning = True
            print(reasoning, end="", flush=True)
            reasoning_len += len(reasoning)
            
        # Check content
        if chunk.choices and chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            if content:
                if not has_content:
                    print("\n\n[Content Started]")
                    has_content = True
                print(content, end="", flush=True)
                content_len += len(content)

    print(f"\n\nDone. Reasoning: {reasoning_len} chars, Content: {content_len} chars")
    
    if content_len < 10 and reasoning_len > 100:
        print("CONCLUSION: Model output was almost entirely in reasoning channel.")
    elif content_len > 10:
        print("CONCLUSION: Model output contained valid content.")

except Exception as e:
    print(f"\nError: {e}")
