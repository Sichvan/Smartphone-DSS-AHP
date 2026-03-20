import psycopg2
import pandas as pd
import json

DB_CONN = "dbname=smartphone_dss user=postgres password=123456789 host=localhost port=5432"

def init_history_table():
    """Tạo bảng lưu lịch sử nếu chưa có"""
    try:
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_history (
                id SERIAL PRIMARY KEY,
                user_text TEXT,
                top_phones JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[+] Khởi tạo Database PostgreSQL thành công!")
    except Exception as e:
        print(f"[-] Lỗi kết nối PostgreSQL (Chức năng lịch sử sẽ bị tắt): {e}")

def save_history(user_text, top_phones):
    """Lưu câu lệnh và kết quả top 5 vào CSDL"""
    try:
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()
        # Chuyển list Top 5 thành định dạng JSON để lưu vào cột JSONB
        cur.execute("""
            INSERT INTO user_history (user_text, top_phones)
            VALUES (%s, %s)
        """, (user_text, json.dumps(top_phones)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[-] Lỗi lưu lịch sử: {e}")

def get_user_history():
    """Lấy 10 lịch sử tìm kiếm gần nhất"""
    try:
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()
        cur.execute("SELECT id, user_text, top_phones, created_at FROM user_history ORDER BY created_at DESC LIMIT 10")
        rows = cur.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "user_text": row[1],
                "top_phones": row[2], # Dữ liệu dạng JSON list
                "created_at": row[3].strftime("%Y-%m-%d %H:%M:%S")
            })
        cur.close()
        conn.close()
        return history
    except Exception as e:
        print(f"[-] Lỗi lấy lịch sử: {e}")
        return []