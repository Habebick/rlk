import sqlite3
import os

def create_and_populate_database(db_filename="components.db"):
    db_filename = 'test.db'
    conn = None  # Инициализация conn вне блока try
    try:
        # Удаляем базу данных, если она существует (чтобы гарантировать создание с новой схемой)
        if os.path.exists(db_filename):
            os.remove(db_filename)
            print(f"Удалена существующая база данных '{db_filename}'.")

        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 1. Создание таблицы components (если она еще не существует)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                component_id INTEGER PRIMARY KEY,
                component_type TEXT,
                location INTEGER,
                model TEXT,
                status TEXT,
                port1 TEXT,
                port2 TEXT,
                groups_id INTEGER DEFAULT NULL  
            )
        """)
        print("Таблица 'components' успешно создана.")

        # 2. Заполнение таблицы данными
        data = [
            (1, 'Switch', 344, 'Huawei', 'Free', 'f1/0/33', 'f1/0/3', None),
            (2, 'Switch', 344, 'Cisco', 'Free', 'f1/0/34', 'f0/1', None),
            (3, 'Switch', 344, 'D-Link', 'Free', 'f0/1', 'f0/3', 3),
            (4, 'Switch', 344, 'Cisco', 'Free', 'f1/0/35', 'f0/1', None)
        ]

        # cursor.executemany("""
        #     INSERT INTO components (component_id, component_type, location, model, status, port1, port2)
        #     VALUES (?, ?, ?, ?, ?, ?, ?)
        # """, data)
        # Альтернативный способ вставки данных с учетом нового поля:
        cursor.executemany("""
            INSERT INTO components (component_id, component_type, location, model, status, port1, port2, groups_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
        """, data)
        print("Данные успешно вставлены в таблицу 'components'.")


        # 4. Сохранение изменений и закрытие соединения
        conn.commit()
        print(f"База данных '{db_filename}' успешно создана и заполнена.")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")

    finally:
        if conn:
            conn.close()

# Пример использования:
if __name__ == "__main__":
    create_and_populate_database()