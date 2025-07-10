import sqlite3
import pandas as pd

DB_PATH = "database\db_active.db"

class Repository:
    @staticmethod
    def _get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _fetch_dataframe(cursor) -> pd.DataFrame:
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return pd.DataFrame(rows, columns=column_names)

    @staticmethod
    def insert_data_table(id_telebot, name_telebot, date, type_active, name_active, shortname_active,
                          count, day_buy, price_buy_USD, price_buy_RUB):
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO my_table (
                    id_telebot, name_telebot, date, type_active, name_active,
                    shortname_active, count, day_buy, price_buy_USD, price_buy_RUB
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_telebot, name_telebot, date, type_active, name_active,
                shortname_active, count, day_buy, price_buy_USD, price_buy_RUB
            ))
            conn.commit()

    @staticmethod
    def select_by_id_telebot(user_id: int) -> pd.DataFrame:
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM my_table WHERE id_telebot = ?", (user_id,))
            return Repository._fetch_dataframe(cursor)

    @staticmethod
    def select_all() -> pd.DataFrame:
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM my_table")
            return Repository._fetch_dataframe(cursor)

    @staticmethod
    def delete_rows_by_condition(row_id: int):
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM my_table WHERE id = ?", (row_id,))
                conn.commit()
                print(f"Удалено строк: {cursor.rowcount}")
            except sqlite3.OperationalError as e:
                print(f"Ошибка при удалении: {e}")

    @staticmethod
    def update_count_by_id(row_id: int, new_count: float):
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE my_table SET count = ? WHERE id = ?", (new_count, row_id))
                conn.commit()
                print(f"Обновлено строк: {cursor.rowcount}")
            except sqlite3.OperationalError as e:
                print(f"Ошибка при обновлении: {e}")