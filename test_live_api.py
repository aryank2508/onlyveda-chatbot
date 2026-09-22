import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

queries = [
    ('what is pain', 'en'),
    ('which are heart dieses', 'en'),
    ('हार्ट की कौन सी बीमारियां होती हैं?', 'hi'),
    ('मुझे हाई ब्लड प्रेशर की शिकायत है', 'hi')
]

for q, lang in queries:
    data = json.dumps({'message': q, 'session_id': 'live_test_session_' + lang, 'language': lang}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/api/chat', data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print('=' * 60)
        print(f"QUERY: {q} [{lang}]")
        print(f"DISEASE PROTOCOL: {res.get('disease_protocol')}")
        prods = [p['name'] for p in res.get('products', [])]
        print(f"PRODUCTS ({len(prods)}): {prods}")
        print("RESPONSE PREVIEW:")
        print(res.get('response', '')[:250].replace('\n', ' ') + "...")
