import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
def get_connection():
    return mysql.connector.connect(
        host="mysql",
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )

def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255),
            question TEXT,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_chat_message(session_id, question, answer):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, question, answer)
        VALUES (%s, %s, %s)
    """, (session_id, question, answer))
    conn.commit()
    conn.close()
