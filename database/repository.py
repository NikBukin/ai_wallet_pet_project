import sqlite3
import pandas as pd

DB_PATH = "database/db_active.db"

class Repository:
    @staticmethod
    def _get_connection():
        """
        Для подключения к базе данных sqlite3
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _fetch_dataframe(cursor) -> pd.DataFrame:
        """
        Получение данных из таблицы в виде pandas
        """
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return pd.DataFrame(rows, columns=column_names)

    @staticmethod
    def insert_data_table(id_telebot, name_telebot, date, type_active, name_active, shortname_active,
                          count, day_buy, price_buy_USD, price_buy_RUB):
        """
        Добавление новой записи в таблицу assets
        """
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assets (
                    user_id, user_name, information_upload_date, type_active, name_of_the_asset,
                    second_name_of_the_asset, amount_of_asset, asset_purchase_date, purchase_price_of_one_asset_in_dollars, purchase_price_of_one_asset_in_rubles
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_telebot, name_telebot, date, type_active, name_active,
                shortname_active, count, day_buy, price_buy_USD, price_buy_RUB
            ))
            conn.commit()

    @staticmethod
    def select_by_id_telebot(user_id: int) -> pd.DataFrame:
        """
        Получение данных из таблицы assets по конкретному пользователю (по user_id)
        """
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assets WHERE user_id = ?", (user_id,))
            return Repository._fetch_dataframe(cursor)

    @staticmethod
    def select_all() -> pd.DataFrame:
        """
        Получение всех данных из таблицы assets
        """
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assets")
            return Repository._fetch_dataframe(cursor)

    @staticmethod
    def delete_rows_by_condition(row_id: int):
        """
        Удаление конкретной записи по уникальному ключу id
        """
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM assets WHERE id = ?", (row_id,))
                conn.commit()
                print(f"Удалено строк: {cursor.rowcount}")
            except sqlite3.OperationalError as e:
                print(f"Ошибка при удалении: {e}")

    @staticmethod
    def update_count_by_id(row_id: int, new_count: float):
        """
        Изменение количества актива в уже существующей записи по уникальному ключу id
        """
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE assets SET amount_of_asset = ? WHERE id = ?", (new_count, row_id))
                conn.commit()
                print(f"Обновлено строк: {cursor.rowcount}")
            except sqlite3.OperationalError as e:
                print(f"Ошибка при обновлении: {e}")

    @staticmethod
    def update_mailing_settings(chat_id, mailing_period, mailing_day, mailing_week, mailing_time):
        """
        Удаление конкретной записи по уникальному ключу id
        """
        with Repository._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM mailing_settings WHERE user_id = ?", (chat_id,))
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"Ошибка при удалении: {e}")
            cursor = conn.cursor()
            try:
                cursor.execute("""
                   INSERT INTO mailing_settings (user_id, m_period, m_day_in_week, m_day, m_time)
                   VALUES (?, ?, ?, ?, ?)
                   """, (
                       chat_id, mailing_period, mailing_week, mailing_day, mailing_time
                   ))
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"Ошибка при добавлении: {e}")

    @staticmethod
    def get_mailing_settings_all():
        return pd.read_sql("SELECT * FROM mailing_settings", sqlite3.connect(DB_PATH))

    @staticmethod
    def get_mailing_settings(user_id: int):
        query = "SELECT * FROM mailing_settings WHERE user_id = ?"
        df = pd.read_sql(query, sqlite3.connect(DB_PATH), params=[user_id])
        return df.iloc[0] if not df.empty else None