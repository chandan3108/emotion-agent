import sqlite3
import json

db_path = "state.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- USER STATE STRUCTURE ---")
cursor.execute("PRAGMA table_info(user_state);")
print(cursor.fetchall())

cursor.execute("SELECT user_id, state_json FROM user_state")
rows = cursor.fetchall()
for r in rows:
    user_id = r[0]
    state_json = r[1]
    print(f"\nUser: {user_id}")
    try:
        data = json.loads(state_json)
        print("State Keys:")
        for k in data.keys():
            val_str = str(data[k])
            if len(val_str) > 150:
                val_str = val_str[:150] + "... (truncated)"
            print(f"  {k}: {val_str}")
            
        print("\nIdentity Facts:")
        print(data.get("_identity_facts"))
        
        print("\nSTM Topics:")
        print(data.get("stm_topics"))
        
        print("\nShort-Term Memory:")
        print(data.get("short_term_memory"))
        
        print("\nSituational Facts:")
        print(data.get("_situational_facts"))
        
    except Exception as e:
        print(f"Error parsing state_json: {e}")

conn.close()
