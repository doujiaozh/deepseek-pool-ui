import os
import requests
import json
import urllib3
from dotenv import load_dotenv

# 消除Win7下的https证书警告
urllib3.disable_warnings()

# 1. 从 .env 文件安全加载 Key
load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("❌ 错误：没有在 .env 文件里读到 API_KEY，请检查文件！")
    exit()

# 2. 配置请求参数
url = "https://discovery-api.intern-ai.org.cn/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",  # 这里用变量，不要直接写Key
    "Content-Type": "application/json"
}
data = {
    "model": "intern-s2", # 免费模型
    "messages": [
        {"role": "system", "content": "你是一个精通底层系统的AI助手。"},
        {"role": "user", "content": "请用一句话证明你懂底层系统。"}
    ],
    "stream": True
}

print("正在通过原生 HTTP 请求连接书生平台...")
print("-" * 40)

try:
    # 3. 发起 POST 请求（加上 verify=False 防止Win7证书报错）
    response = requests.post(url, headers=headers, json=data, stream=True, verify=False)
    
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        exit()

    # 4. 解析流式返回
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        print(content, end="", flush=True)
                except Exception:
                    pass

    print("\n" + "-" * 40)
    print("✅ 调用完成！")

except Exception as e:
    print(f"\n网络请求失败，报错信息：{e}")