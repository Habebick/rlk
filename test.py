import re
import sqlite3

import pandas as pd
import yaml

text = 'Switch(Cisco)+Switch(Huawei)'
db_filename = 'test.db'


def lab_1():
    text = "PC-A+Switch(Cisco)+Router(Cisco)+PC-B"
    planner(text)

def lab_2():
    pass


def planner(text):
    elements = text.split('+')
    devices = []
    for element in elements:
        device = []
        match = re.match(r'([^(]*)\(([^)]*)\)', element)
        device.append(match.group(1))
        device.append(match.group(2))
        devices.append(device)
    update_bd(devices)


def add_vlan(vlan, switchport, db_filename='vlan_config.db'):
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vlan_config (vlan, switchport, lab)
            VALUES (?, ?, ?)
        """, (vlan, switchport, 1))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")

    finally:
        if conn:
            conn.close()


def create_playbook(devices, output_file="vlan_playbook.yaml"):
    playbook = [
        {
            'gather_facts': 'no',
            'tasks': [
                {'name': 'Проверяем доступность по SSH',
                 'wait_for_connection': {'delay': 5, 'timeout': 60}},
            ]
        }
    ]
    try:
        with sqlite3.connect('vlan_config.db') as conn:
            cursor = conn.cursor()
            query_check = """
                    SELECT max(VLAN) FROM vlan_config
                 """
            cursor.execute(query_check)
            vlan = cursor.fetchone()[0]
    except Exception as e:
        print(f"Ошибка: {e}")

    for device in devices:
        vlan += 10
        add_vlan(vlan, device[3])
        vlan_task = {
            'name': f"Настройка порта {device[3]} в VLAN {vlan}",
            'ios_config': {
                'parents': f"interface {device[3]}",
                'lines': [
                    "switchport mode access",
                    f"switchport access vlan {vlan}",
                    "no cdp enable",
                ],
            },
        }
        playbook[0]['tasks'].append(vlan_task)

    # Добавляем задачу для сохранения конфигурации
    playbook[0]['tasks'].append({
        'name': 'Сохраняем конфигурацию ',
        'ios_command': {
            'commands': ['copy running-config startup-config']
        }
    })

    playbook_yaml = yaml.dump(playbook, indent=2)

    with open(output_file, "w") as f:
        f.write(playbook_yaml)


def update_bd(devices):
    try:
        with sqlite3.connect(db_filename) as conn:
            cursor = conn.cursor()
            for device in devices:
                enough_device = check_enough(device[0], cursor, device[1], 'Active')
                if (enough_device[0] > 0):
                    device.append(enough_device[1])
                    device.append(enough_device[2])
                else:
                    print('Недостаточно оборудование')
                    return False
            for device in devices:
                update_status(device[2], cursor, 'Active')
            conn.commit()
            test()
        create_playbook(devices)
    except Exception as e:
        print(f"Ошибка: {e}")


def check_enough(component_type, cursor, model, new_status):
    query_check = """
        SELECT COUNT(*), component_id, port1 FROM components
        WHERE component_type = ? AND model = ? AND status != ? LIMIT 1
    """
    cursor.execute(query_check, (component_type, model, new_status))
    return cursor.fetchone()


def update_status(component_id, cursor, status):
    query_update = """
        UPDATE components
        SET status = ?
        WHERE component_id = ?
    """
    cursor.execute(query_update, (status, component_id,))


def test():
    try:
        conn = sqlite3.connect(db_filename)
        query = "SELECT * FROM components WHERE status = 'Active'"
        devices = pd.read_sql_query(query, conn)
        print(devices)
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def clear_bd():
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        query = "UPDATE components SET status = 'Free' WHERE status = 'Active'"
        cursor.execute(query)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Произошла ошибка при работе с базой данных: {e}")
    finally:
        if conn:
            conn.close()


clear_bd()
planner(text)
