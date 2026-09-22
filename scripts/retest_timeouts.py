import urllib.request, json

BASE = 'http://127.0.0.1:8000/api/chat'

tests = [
    'I have thyroid problem',
    'I have migraine',
    'high blood pressure hai',
    'acne pimples problem'
]

for q in tests:
    body = json.dumps({'message': q, 'session_id': 'retest2'}).encode()
    req = urllib.request.Request(BASE, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            prods = data.get('products', [])
            names = [p['name'] for p in prods]
            print(f'[OK] "{q}" -> {len(prods)} products')
            for n in names:
                print(f'     -> {n}')
    except Exception as e:
        print(f'[ERR] "{q}" -> {e}')
