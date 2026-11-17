code = '''import os
import time
import requests
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()
load_dotenv('backend/.env')

app = Flask(__name__)
CORS(app)

UPSTREAMS = [
    {
        'name': '书生平台',
        'url': 'https://discovery-api.intern-ai.org.cn/v1/chat/completions',
        'key': os.getenv('API_KEY'),
        'model': 'intern-s2',
        'status': 'active',
        'cooldown_until': 0
    },
    {
        'name': '硅基流动备用',
        'url': 'https://api.siliconflow.cn/v1/chat/completions',
        'key': os.getenv('SILICONFLOW_KEY'),
        'model': 'Qwen/Qwen3-8B',
        'status': 'active',
        'cooldown_until': 0
    }
]

@app.route('/v1/chat/completions', methods=['POST'])
def proxy_chat():
    req_data = request.get_json()
    req_data['stream'] = True
    
    def generate():
        for chosen_upstream in UPSTREAMS:
            if chosen_upstream['status'] != 'active' or time.time() < chosen_upstream['cooldown_until']:
                continue
            print('[INFO] 尝试通道:', chosen_upstream['name'])
            req_data['model'] = chosen_upstream['model']
            headers = {'Authorization': 'Bearer ' + str(chosen_upstream['key']), 'Content-Type': 'application/json'}
            try:
                response = requests.post(chosen_upstream['url'], headers=headers, json=req_data, stream=True, verify=False, timeout=15)
                if response.status_code == 429:
                    print('[WARN]', chosen_upstream['name'], '触发限流，切换备用通道...')
                    chosen_upstream['status'] = 'cooling_down'
                    chosen_upstream['cooldown_until'] = time.time() + 60
                    continue
                if response.status_code != 200:
                    print('[ERROR]', chosen_upstream['name'], '报错:', response.status_code)
                    continue
                print('[INFO] 成功建立连接:', chosen_upstream['name'])
                for chunk in response.iter_content(chunk_size=None):
                    yield chunk
                return
            except Exception as e:
                print('[ERROR]', chosen_upstream['name'], '网络异常:', e)
                continue
        yield 'data: {"error": "所有通道拥堵或异常，请稍后再试"}\\n\\n'
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    print('[INFO] V4.0 多通道网关已启动！')
    app.run(host='0.0.0.0', port=5000)
'''

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('✅ server.py 已成功升级为 V4.0（安全版）！')