import sqlite3
import json

def dump_web_user_history():
    conn = sqlite3.connect("/Users/chandu/Downloads/emotion-agent/state.db")
    cursor = conn.cursor()
    cursor.execute("SELECT state_json FROM user_state WHERE user_id = 'web_web_user_001'")
    row = cursor.fetchone()
    if not row:
        print("No user web_web_user_001 found in root state.db")
        return
        
    state = json.loads(row[0])
    # Let's inspect stm and episodic memory
    memory_hierarchy = state.get("memory_hierarchy", {})
    stm = memory_hierarchy.get("stm", [])
    print(f"Short Term Memory (stm) count: {len(stm)}")
    for m in stm:
        print(f"  [{m.get('sender', 'unknown')}]: {m.get('content')}")
        
    episodic = memory_hierarchy.get("episodic", [])
    print(f"\nEpisodic Memory count: {len(episodic)}")
    for e in episodic:
        print(f"  [{e.get('event_type')}]: {e.get('content')}")
        
    conn.close()

if __name__ == "__main__":
    dump_web_user_history()
