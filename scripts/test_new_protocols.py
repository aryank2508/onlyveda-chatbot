"""Test new disease protocols are working after import."""
import urllib.request, json, time

BASE = "http://127.0.0.1:8000/api/chat"

TESTS = [
    # New diseases from Excel
    ("I have piles problem",           True,  ["Anurect"]),
    ("mujhe kidney stone hai",         True,  ["Kidney", "Stowip"]),
    ("I have thyroid problem",         True,  ["Ashyuka", "Immuferin"]),
    ("I have migraine",                True,  ["Ashyuka", "Intelget"]),
    ("I am suffering from dengue",     True,  ["Cariwal"]),
    ("I have pcos period problem",     True,  ["Evareg", "U-She"]),
    ("hair fall problem",              True,  ["Hair 2X", "Multivitamin"]),
    ("mujhe obesity hai",              True,  ["Biomelt"]),
    ("I have fatty liver",             True,  ["Milk Thistle"]),
    ("eye health vision problem",      True,  ["I-Well"]),
    ("varicose veins problem",         True,  ["L-Arginine"]),
    # Educational - should NOT show products
    ("what is dengue",                 False, []),
    ("what is thyroid",                False, []),
    ("what is piles",                  False, []),
    # Existing diseases - still work
    ("high blood pressure hai",        True,  ["Linopress"]),
    ("acne pimples problem",           True,  ["Xemma", "Active 365"]),
]

def call_api(msg):
    body = json.dumps({"message": msg, "session_id": "test_new_db"}).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

time.sleep(3)
passed = 0
failed = 0
for query, expect_products, expect_names in TESTS:
    try:
        r = call_api(query)
        has_prods = len(r.get("products", [])) > 0
        resp_lower = r["response"].lower()
        names_found = all(any(n.lower() in resp_lower for n in [en]) for en in expect_names) if expect_names else True

        ok = (has_prods == expect_products) and names_found
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        prod_count = len(r.get("products", []))
        print(f"[{status}] '{query}' -> products={prod_count}, names_ok={names_found}")
    except Exception as e:
        failed += 1
        print(f"[ERROR] '{query}' -> {e}")

print(f"\nResult: {passed}/{passed+failed} PASSED")
