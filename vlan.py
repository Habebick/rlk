import sqlite3
import os

def create_and_populate_vlan_db(db_filename="vlan_config.db"):

    try:
        # Удаление существующей базы данных
        if os.path.exists(db_filename):
            os.remove(db_filename)
            print(f"Предыдущая база данных '{db_filename}' удалена.")

        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 1. Создание таблицы vlan_config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vlan_config (
                vlan INTEGER,
                switchport TEXT,
                groups_id INTEGER DEFAULT NULL,
                audience INTEGER DEFAULT NULL
            )
        """)
        print("Таблица 'vlan_config' успешно создана.")

        # 2. Заполнение таблицы данными
        data = [
            (123, 'PC', 0, None),
            (125, 'PC', 0, None),
            (223, 'PC', 0, None),
            (225, 'PC', 0, None),
            (323, 'PC', 0, None),
            (325, 'PC', 0, None)
        ]

        cursor.executemany("""
            INSERT INTO vlan_config (vlan, switchport, groups_id, audience)
            VALUES (?, ?, ?, ?)
        """, data)
        print("Данные успешно вставлены в таблицу 'vlan_config'.")

        # 3. Сохранение изменений
        conn.commit()
        print(f"База данных '{db_filename}' успешно создана и заполнена.")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")

    finally:
        if conn:
            conn.close()

# Пример использования:
if __name__ == "__main__":
    create_and_populate_vlan_db()