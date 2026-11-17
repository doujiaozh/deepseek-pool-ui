# coding=gbk
import requests

url = "http://127.0.0.1:5000/v1/chat/completions"
headers = {
    "Authorization": "Bearer fake_key", 
    "Content-Type": "application/json"
}
data = {
    "model": "any", 
    "messages": [{"role": "user", "content": "请用一句话证明你懂底层系统。"}]
}

print("正在通过网关发送请求...")
print("-" * 40)

try:
    response = requests.post(url, headers=headers, json=data, stream=True, timeout=20)
    
    # 检查状态码
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
    else:
        # 流式打印结果
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    # 直接打印原始返回（方便调试）
                    print(data_str)
except Exception as e:
    print(f"发生错误: {e}")