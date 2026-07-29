import sqlite3
from contextlib import contextmanager
from config import DATABASE_FILE

@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_FILE, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize_database():
    with get_connection() as connection:
        connection.executescript(
            '''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'Business Analyst',
                department TEXT,
                manager_name TEXT,
                mentor_name TEXT,
                location TEXT,
                experience_level TEXT,
                joining_date TEXT,
                onboarding_day INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS milestone_completion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                milestone_id TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                UNIQUE(employee_id, milestone_id),
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT UNIQUE,
                employee_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium',
                status TEXT NOT NULL DEFAULT 'Open',
                assigned_to TEXT,
                resolution TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS ticket_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                comment TEXT,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sentiment_label TEXT NOT NULL,
                sentiment_score REAL NOT NULL,
                needs_support INTEGER NOT NULL DEFAULT 0,
                urgent_terms TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            '''
        )
        connection.execute(
            '''
            INSERT OR IGNORE INTO employees
            (id, employee_code, name, email, role, department, manager_name,
             mentor_name, location, experience_level, joining_date, onboarding_day)
            VALUES
            (1, 'EMP001', 'Aarav Sharma', 'aarav.sharma@example.com',
             'Business Analyst', 'Digital Transformation', 'Meera Kapoor',
             'Rohan Iyer', 'Pune', 'Associate', '2026-07-01', 7)
            '''
        )
