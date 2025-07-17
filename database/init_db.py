import sqlite3

DB_PATH = "db_active.db"

def init_db():
    """
    Инициализирует пустую базу данных sqlite3 в случае ее отсутствия в проекте
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            information_upload_date TEXT,
            type_active TEXT,
            name_of_the_asset TEXT,
            second_name_of_the_asset TEXT,
            amount_of_asset REAL,
            asset_purchase_date TEXT,
            purchase_price_of_one_asset_in_dollars REAL,
            purchase_price_of_one_asset_in_rubles REAL
        )
    """)
    conn.commit()
    conn.close()
    print("База данных инициализирована.")

if __name__ == "__main__":
    init_db()