import sqlite3
import os

# Definim unde stă dB Buffer
DB_PATH = "nexus_buffer.db"

def get_db_connection():
    """Deschide ușa către baza de date pentru a citi/scrie."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Ca să primim datele ca dicționare, nu ca liste simple
    return conn

def init_db():
    """Se rulează o singură dată la pornire pentru a crea structura (Tabelele)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabela pentru Utilizatori (Securitate)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 2. Tabela pentru Comenzi Live (Rampa / WMS)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders_live (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_logistic TEXT,
            payload_fiscal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Inserăm un admin de test dacă baza e goală
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'arhitect')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('rampa', '1234', 'wms')")

    conn.commit()
    conn.close()
    print("✅ dB Buffer a fost inițializat cu succes!")

# Dacă rulăm direct acest fișier, creează baza de date.
if __name__ == "__main__":
    init_db()
