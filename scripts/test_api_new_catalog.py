import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/chat',
    data=json.dumps({
        'message': 'I have joint pain and high blood pressure, what products do you recommend?',
        'session_id': 'verify_test'
    }).encode(),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req, timeout=40) as resp:
    res = json.loads(resp.read())
    print("API Response OK!")
    print(f"Products recommended: {len(res.get('products', []))}")
    for p in res.get('products', []):
        print(f"  • {p.get('name')} | Category: {p.get('category')} | Price: Rs. {p.get('price_inr')}")
