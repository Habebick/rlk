import pandas as pd
import sqlite3
import re
from table import generate_table

def get_active_devices(db_filename):
    try:
        conn = sqlite3.connect(db_filename)
        query = "SELECT * FROM components WHERE status = 'Active'"
        devices = pd.read_sql_query(query, conn)
        print(devices)
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def check_enough(component_type, num_required, cursor, model, new_status):
    query_check = """
        SELECT COUNT(*) FROM components
        WHERE component_type = ? AND model = ? AND status != ?
    """
    cursor.execute(query_check, (component_type, model, new_status))
    count = cursor.fetchone()[0]
    return count >= num_required

def update_devices(component_type, num_to_update, cursor, model, new_status):
    query_update = """
        UPDATE components
        SET status = ?
        WHERE component_type = ? AND model = ? AND status != ?
        AND component_id IN (SELECT component_id FROM components 
                              WHERE component_type = ? AND model = ? AND status != ? LIMIT ?)
    """
    cursor.execute(query_update, (new_status, component_type, model, new_status,
                                  component_type, model, new_status, num_to_update))

def update_devices_status(db_filename, num_routers, num_switches, model, new_status):
    try:
        with sqlite3.connect(db_filename) as conn:
            cursor = conn.cursor()

            enough_routers = check_enough('Router', num_routers, cursor, model, new_status)
            enough_switches = check_enough('Switch', num_switches, cursor, model, new_status)

            if enough_routers and enough_switches:
                update_devices('Router', num_routers, cursor, model, new_status)
                update_devices('Switch', num_switches, cursor, model, new_status)
                conn.commit()

            else:
                if not enough_routers:
                    print(f"Недостаточно Router с моделью '{model}'.")
                if not enough_switches:
                    print(f"Недостаточно Switch с моделью '{model}'.")
                print("Обновление не выполнено, так как недостаточно оборудования")

    except Exception as e:
        print(f"Ошибка: {e}")

def get_free_devices(db_filename):
    conn = sqlite3.connect(db_filename)
    query = "SELECT * FROM components WHERE status = 'Free'"
    devices = pd.read_sql_query(query, conn)
    print(devices)
    conn.close()


def update_status(db_filename, query):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


def planner(text,data):
    match = re.search(r'"([^"]*)"', text)
    model = match.group(1)
    match = re.findall(r"(\d+)(\D)", text)
    for a in match:
        count = a[0]
        if a[1] == 'S' or a[1] == 's':
            num_switch = int(a[0])
        if a[1] == 'R' or a[1] == 'r':
            num_routers = int(a[0])
    update_devices_status(data, num_routers, num_switch, model.capitalize(), 'Active')


#добавить топологию 2sw+2R"huawei"
def control():
    generate_table()


def clear_bd():
    devices = get_active_devices(data)
    query = "UPDATE components SET status = 'Free' WHERE status = 'Active'"
    update_status(data, query)


data = 'mydatabase.db'
text = '2sw+2R"Cisco"'
planner(text,data)

#[('2', 's'), ('2', 'R')]
