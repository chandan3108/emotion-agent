import sqlite3
import json

db_path = "state.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT user_id, state_json FROM user_state")
rows = cursor.fetchall()
for r in rows:
    user_id = r[0]
    state_json = r[1]
    print(f"Processing User: {user_id}")
    try:
        data = json.loads(state_json)
        
        # Reset topic context and relevancy caches
        if "_topic_context" in data:
            print(f"  Old _topic_context: {data['_topic_context']}")
            data["_topic_context"] = {}
            
        if "_relevant_identity_facts" in data:
            print(f"  Old _relevant_identity_facts: {data['_relevant_identity_facts']}")
            data["_relevant_identity_facts"] = []
            
        if "_relevant_episodic_facts" in data:
            print(f"  Old _relevant_episodic_facts: {data['_relevant_episodic_facts']}")
            data["_relevant_episodic_facts"] = []
            
        if "_relevant_user_fact_keys" in data:
            print(f"  Old _relevant_user_fact_keys: {data['_relevant_user_fact_keys']}")
            data["_relevant_user_fact_keys"] = []
            
        # Update database
        updated_json = json.dumps(data)
        cursor.execute("UPDATE user_state SET state_json = ? WHERE user_id = ?", (updated_json, user_id))
        print("  State updated successfully in state.db!")
    except Exception as e:
        print(f"  Error processing state: {e}")

conn.commit()
conn.close()
print("Done clearing stale context!")
