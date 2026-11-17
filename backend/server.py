import os
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
        'name': 'ShuSheng',
        'url': 'https://discovery-api.intern-ai.org.cn/v1/chat/completions',
        'key': os.getenv('API_KEY'),
        'model': 'intern-s2',
        'status': 'active',
        'cooldown_until': 0
    },
    {
        'name': 'SiliconFlow',
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
            print('[INFO] Trying:', chosen_upstream['name'])
            req_data['model'] = chosen_upstream['model']
            headers = {'Authorization': 'Bearer ' + str(chosen_upstream['key']), 'Content-Type': 'application/json'}
            try:
                response = requests.post(chosen_upstream['url'], headers=headers, json=req_data, stream=True, verify=False, timeout=15)
                if response.status_code == 429:
                    print('[WARN]', chosen_upstream['name'], 'limit reached, switching...')
                    chosen_upstream['status'] = 'cooling_down'
                    chosen_upstream['cooldown_until'] = time.time() + 60
                    continue
                if response.status_code != 200:
                    print('[ERROR]', chosen_upstream['name'], 'failed:', response.status_code)
                    continue
                print('[INFO] Connected:', chosen_upstream['name'])
                for chunk in response.iter_content(chunk_size=None):
                    yield chunk
                return
            except Exception as e:
                print('[ERROR]', chosen_upstream['name'], 'network error:', e)
                continue
        yield 'data: {"error": "All channels failed"}\n\n'
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    print('[INFO] V4.0 Gateway Started!')
    app.run(host='0.0.0.0', port=5000)