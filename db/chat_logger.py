from datetime import datetime
import json
from db.db_manager import get_connection

DB_PATH = "db/chat_history.db"

def init_conversation_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_sessions (
            pdf_name VARCHAR(255) PRIMARY KEY,
            timestamp DATETIME,
            base_prompt TEXT,
            resp_id VARCHAR(255),
            history_json LONGTEXT,
            token_count INT
        )
    """)
    conn.commit()
    conn.close()

def save_pdf_session(pdf_name, base_prompt, resp_id, history, token_count):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pdf_sessions (pdf_name, timestamp, base_prompt, resp_id, history_json, token_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            timestamp = VALUES(timestamp),
            base_prompt = VALUES(base_prompt),
            resp_id = VALUES(resp_id),
            history_json = VALUES(history_json),
            token_count = VALUES(token_count)
    """, (
        pdf_name,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        base_prompt,
        resp_id,
        json.dumps(history),
        token_count
    ))
    conn.commit()
    conn.close()

def load_all_pdf_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_name, base_prompt, resp_id, history_json, token_count FROM pdf_sessions")
    rows = cursor.fetchall()
    conn.close()
    
    sessions = {}
    for pdf_name, base_prompt, resp_id, history_json, token_count in rows:
        sessions[pdf_name] = {
            "base_prompt": base_prompt,
            "resp_id": resp_id,
            "history": json.loads(history_json),
            "tokens": token_count
        }
    return sessions

def delete_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pdf_sessions")
    conn.commit()
    conn.close()
