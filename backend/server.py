import os
import time
import requests
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import urllib3

# 消除Win7下的证书警告
urllib3.disable_warnings()

load_dotenv('backend/.env') # 注意这里加上了路径，因为现在是在根目录跑
api_key = os.getenv("API_KEY")

app = Flask(__name__)
CORS(app)

# 定义上游通道池
UPSTREAMS = [
    {
        "name": "书生平台",
        "url": "https://discovery-api.intern-ai.org.cn/v1/chat/completions",
        "key": api_key,
        "model": "intern-s2",
        "status": "active",
        "cooldown_until": 0
    }
]

@app.route('/v1/chat/completions', methods=['POST'])
def proxy_chat():
    req_data = request.get_json()
    req_data["stream"] = True
    
    # 调度器逻辑：寻找可用且不在冷却期的通道
    chosen_upstream = None
    for upstream in UPSTREAMS:
        if upstream["status"] == "active" and time.time() > upstream["cooldown_until"]:
            chosen_upstream = upstream
            break
            
    if not chosen_upstream:
        return Response("data: {\"error\": \"所有通道都在冷却中，请稍后再试\"}\n\n", mimetype='text/event-stream')

    req_data["model"] = chosen_upstream["model"]

    headers = {
        "Authorization": f"Bearer {chosen_upstream['key']}",
        "Content-Type": "application/json"
    }

    print(f"-> 正在使用通道: {chosen_upstream['name']}")

    def generate():
        try:
            response = requests.post(chosen_upstream["url"], headers=headers, json=req_data, stream=True, verify=False, timeout=30)
            
            # 核心逻辑：遇到 429（限流）触发冷却机制
            if response.status_code == 429:
                print(f"[WARN] {chosen_upstream['name']} 触发限流 (429)，进入 60 秒冷却")
                chosen_upstream["status"] = "cooling_down"
                chosen_upstream["cooldown_until"] = time.time() + 60 
                yield f"data: {{\"error\": \"当前通道繁忙，已触发冷却重试机制，请稍后重试\"}}\n\n"
                return

            if response.status_code != 200:
                yield f"data: {{\"error\": \"Upstream error: {response.status_code}\"}}\n\n"
                return

            for chunk in response.iter_content(chunk_size=None):
                yield chunk

        except Exception as e:
            yield f"data: {{\"error\": \"Proxy Error: {str(e)}\"}}\n\n"
        finally:
            # 冷却时间结束后，恢复通道状态
            if chosen_upstream["status"] == "cooling_down" and time.time() > chosen_upstream["cooldown_until"]:
                chosen_upstream["status"] = "active"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    print("=====================================")
    print("[INFO] V2.0 网关已启动！")
    print("监听端口: 5000")
    print("=====================================")
    app.run(host='0.0.0.0', port=5000, debug=True)