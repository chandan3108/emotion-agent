import sqlite3

def dump_memory_search():
    conn = sqlite3.connect("/Users/chandu/Downloads/emotion-agent/memory_search.db")
    cursor = conn.cursor()
    
    # Let's see the schema of memory_fts
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='memory_fts'")
    print("Schema:", cursor.fetchone()[0])
    
    # Query all contents
    cursor.execute("SELECT * FROM memory_fts")
    rows = cursor.fetchall()
    print(f"\nTotal rows in memory_fts: {len(rows)}")
    for i, row in enumerate(rows[:50]):
        print(f"Row {i}: {row}")
        
    conn.close()

if __name__ == "__main__":
    dump_memory_search()
