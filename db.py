import sqlite3
import os
from datetime import datetime

DB_PATH = "/home/yayock79/lead_engine/leads.db"

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            niche TEXT NOT NULL,
            phone TEXT,
            website_url TEXT UNIQUE,
            review_count INTEGER DEFAULT 0,
            has_viewport BOOLEAN DEFAULT 0,
            http_status INTEGER,
            load_speed_sec REAL,
            is_broken_mobile BOOLEAN DEFAULT 0,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def wipe_leads(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads")
    conn.commit()
    conn.close()
    print("[DB] Cleared all aggregate directory rows from SQLite database.")

def save_lead(lead_data, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO leads 
            (business_name, niche, phone, website_url, review_count, has_viewport, http_status, load_speed_sec, is_broken_mobile, audit_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_data.get("business_name"),
            lead_data.get("niche"),
            lead_data.get("phone"),
            lead_data.get("website_url"),
            lead_data.get("review_count", 0),
            lead_data.get("has_viewport", False),
            lead_data.get("http_status", 0),
            lead_data.get("load_speed_sec", 0.0),
            lead_data.get("is_broken_mobile", False),
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Database error saving lead {lead_data.get('business_name')}: {e}")
        return None
    finally:
        conn.close()

def get_all_leads(only_broken=False, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if only_broken:
        cursor.execute("SELECT id, business_name, niche, phone, website_url, review_count, has_viewport, http_status, load_speed_sec, is_broken_mobile FROM leads WHERE is_broken_mobile = 1 ORDER BY id DESC")
    else:
        cursor.execute("SELECT id, business_name, niche, phone, website_url, review_count, has_viewport, http_status, load_speed_sec, is_broken_mobile FROM leads ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_lead_by_id(lead_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
