import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_text TEXT,
            anonymized_text TEXT,
            sentiment TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_entry(user_id, original_text, anonymized_text, sentiment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO entries (user_id, original_text, anonymized_text, sentiment)
        VALUES (?, ?, ?, ?)
    """, (user_id, original_text, anonymized_text, sentiment))
    conn.commit()
    conn.close()

def get_entries_by_sentiment(sentiment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT anonymized_text FROM entries
        WHERE sentiment=?
    """, (sentiment,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
