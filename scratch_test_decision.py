import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.bot_engine import OnlyVedaChatbot

bot = OnlyVedaChatbot()

test_queries = [
    'hello',
    'good morning',
    'who are you',
    'what can you do',
    'tell me a joke',
    'what is your name',
    'thank you so much',
    'bye',
    'what is pain',
    'which are heart dieses',
    'i have high bp',
    'my stomach is aching',
    'my face has pimples',
    'suggest medicine for knee pain',
    'what is diabetes',
    'can you help me with health',
    'what is ayurveda',
    'how to reduce stress'
]

for q in test_queries:
    res = bot.chat(q)
    prods = [p['name'] for p in res['products']]
    print(f'PROMPT: "{q}"')
    print(f'  -> Products count: {len(prods)} | Products: {prods[:2]}')
    print(f'  -> Has disease protocol: {bool(res["disease_protocol"])}')
    print(f'  -> Response starts: {res["response"][:80].replace(chr(10), " ")}...')
    print('-'*50)
