import sqlite3

def inspect():
    conn = sqlite3.connect('/Users/chandu/Downloads/emotion-agent/events.db')
    cursor = conn.cursor()
    
    print("--- CHAT SESSIONS ---")
    cursor.execute("SELECT id, user_id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC")
    sessions = cursor.fetchall()
    for s in sessions:
        print(f"ID: {s[0]} | User: {s[1]} | Title: {s[2]} | Updated: {s[4]}")
        
    print("\n--- CHAT MESSAGES COUNT PER SESSION ---")
    cursor.execute("SELECT session_id, role, COUNT(*) FROM chat_messages GROUP BY session_id, role")
    msg_counts = cursor.fetchall()
    for mc in msg_counts:
        print(f"Session: {mc[0]} | Role: {mc[1]} | Count: {mc[2]}")
        
    conn.close()

if __name__ == '__main__':
    inspect()
