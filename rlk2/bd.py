import sqlite3  # Для SQLite


def update_status(db_filename, query):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


data = 'mydatabase.db'
query = "UPDATE components SET component_type = 'Switch' WHERE component_type = 'PC'"
update_status(data, query)
# SQLite
conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM components")
rows = cursor.fetchall()
print("\nСодержимое таблицы 'components':")
for row in rows:
    print(row)