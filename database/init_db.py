import sqlite3

DB_PATH = "db_active.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_telebot INTEGER,
            name_telebot TEXT,
            date TEXT,
            type_active TEXT,
            name_active TEXT,
            shortname_active TEXT,
            count REAL,
            day_buy TEXT,
            price_buy_USD REAL,
            price_buy_RUB REAL
        )
    """)
    conn.commit()
    conn.close()
    print("База данных инициализирована.")

if __name__ == "__main__":
    init_db()