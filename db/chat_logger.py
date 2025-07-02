from datetime import datetime
import json
from db.db_manager import get_connection

def init_conversation_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_sessions (
            pdf_name VARCHAR(255) PRIMARY KEY,
            timestamp TIMESTAMP,
            base_prompt TEXT,
            resp_id VARCHAR(255),
            history_json TEXT,
            token_count INT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def save_pdf_session(pdf_name, base_prompt, resp_id, history, token_count):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pdf_sessions (pdf_name, timestamp, base_prompt, resp_id, history_json, token_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (pdf_name) DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            base_prompt = EXCLUDED.base_prompt,
            resp_id = EXCLUDED.resp_id,
            history_json = EXCLUDED.history_json,
            token_count = EXCLUDED.token_count
    """, (
        pdf_name,
        datetime.now(),
        base_prompt,
        resp_id,
        json.dumps(history),
        token_count
    ))
    conn.commit()
    cursor.close()
    conn.close()

def load_all_pdf_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_name, base_prompt, resp_id, history_json, token_count FROM pdf_sessions")
    rows = cursor.fetchall()
    cursor.close()
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
    cursor.close()
    conn.close()
