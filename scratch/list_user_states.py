import sqlite3

def list_user_states():
    conn = sqlite3.connect("/Users/chandu/Downloads/emotion-agent/backend/state.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, LENGTH(state_json) FROM user_state")
    rows = cursor.fetchall()
    print("User states in backend/state.db:")
    for row in rows:
        print(f"  User ID: {row[0]}, State size: {row[1]} bytes")
    conn.close()

if __name__ == "__main__":
    list_user_states()
