import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

tests = [
    ("hello", "en", False, 0),
    ("tell me a joke", "en", False, 0),
    ("what is python programming", "en", False, 0),
    ("what is pain", "en", True, 3),
    ("which are heart dieses", "en", True, 3),
    ("what is diabetes", "en", True, 3),
    ("how to reduce stress", "en", True, 2),
    ("मुझे हाई ब्लड प्रेशर की शिकायत है", "hi", True, 3),
    ("મારા ચહેરા પર ખૂબ ખીલ અને પિમ્પલ્સ છે", "gu", True, 3)
]

print("=" * 70)
print("🌐 TESTING LIVE API ENDPOINT: http://127.0.0.1:8000/api/chat")
print("=" * 70)

all_passed = True

for query, lang, exp_suggest, exp_min_prods in tests:
    req_data = json.dumps({
        "message": query,
        "session_id": f"live_eval_{lang}",
        "language": lang
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        prods = [p["name"] for p in res.get("products", [])]
        protocol = res.get("disease_protocol")
        dis_name = protocol.get("disease") if protocol else "None"
        resp_text = res.get("response", "")

        print(f"\n[QUERY] '{query}' ({lang})")
        print(f"  - Products ({len(prods)}): {prods}")
        print(f"  - Disease Protocol: {dis_name}")
        print(f"  - Response Length: {len(resp_text)} characters")

        # Verify decision
        if exp_suggest:
            if len(prods) < exp_min_prods:
                print(f"  ❌ FAILED: Expected at least {exp_min_prods} products, got {len(prods)}")
                all_passed = False
            else:
                print(f"  ✅ PASSED: Accurate OnlyVeda product suggestions included.")
        else:
            if len(prods) != 0:
                print(f"  ❌ FAILED: Expected 0 products for conversational/non-health, got {len(prods)}")
                all_passed = False
            else:
                print(f"  ✅ PASSED: 0 products suggested (pure conversational / non-health redirection).")

print("\n" + "=" * 70)
if all_passed:
    print("🏆 ALL LIVE API VERIFICATION TESTS PASSED PERFECTLY!")
else:
    print("❌ SOME LIVE TESTS FAILED")
print("=" * 70)
