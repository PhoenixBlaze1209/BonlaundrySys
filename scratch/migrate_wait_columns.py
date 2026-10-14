# scratch/migrate_wait_columns.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.database import engine
from sqlalchemy import text

def run():
    with engine.connect() as conn:
        cols_q = [r[0] for r in conn.execute(text("SHOW COLUMNS FROM tbl_queue")).fetchall()]
        print("Existing tbl_queue cols:", cols_q)
        
        if 'verified_at' not in cols_q:
            conn.execute(text("ALTER TABLE tbl_queue ADD COLUMN verified_at DATETIME NULL"))
            print("Added verified_at to tbl_queue")
            
        if 'started_at' not in cols_q:
            conn.execute(text("ALTER TABLE tbl_queue ADD COLUMN started_at DATETIME NULL"))
            print("Added started_at to tbl_queue")
            
        if 'actual_wait_mins' not in cols_q:
            conn.execute(text("ALTER TABLE tbl_queue ADD COLUMN actual_wait_mins DECIMAL(6,2) NULL"))
            print("Added actual_wait_mins to tbl_queue")
            
        if 'created_at' not in cols_q:
            conn.execute(text("ALTER TABLE tbl_queue ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            print("Added created_at to tbl_queue")
            
        cols_a = [r[0] for r in conn.execute(text("SHOW COLUMNS FROM tbl_appointment")).fetchall()]
        print("Existing tbl_appointment cols:", cols_a)
        
        if 'verified_at' not in cols_a:
            conn.execute(text("ALTER TABLE tbl_appointment ADD COLUMN verified_at DATETIME NULL"))
            print("Added verified_at to tbl_appointment")
            
        conn.commit()
    print("Schema migration completed successfully!")

if __name__ == '__main__':
    run()
