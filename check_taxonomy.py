import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

with open('data/disease_taxonomy.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)['taxonomy']

print(f"Total Diseases in Taxonomy: {len(tax)}")
for dis in tax:
    en_cnt = len(tax[dis].get('en', []))
    hi_cnt = len(tax[dis].get('hi', []))
    te_cnt = len(tax[dis].get('te', []))
    ta_cnt = len(tax[dis].get('ta', []))
    print(f"{dis:30} | en: {en_cnt} | hi: {hi_cnt} | te: {te_cnt} | ta: {ta_cnt}")
