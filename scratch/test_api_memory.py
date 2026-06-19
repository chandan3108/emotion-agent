import httpx

url = "http://127.0.0.1:8000/api/user/web_user_001/memory"
try:
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()
    
    print("=== IDENTITY FACTS ===")
    for f in data.get("identity", {}).get("facts", []):
        print(f"  - {f['fact']} (Confidence: {f['confidence']}, Source: {f['source']})")
        
    print("\n=== EPISODIC MEMORIES ===")
    for e in data.get("episodic", {}).get("entries", []):
        print(f"  - [{e['event_type']}] {e['content']} (Salience: {e['salience']})")
        
except Exception as err:
    print(f"Error calling API: {err}")
