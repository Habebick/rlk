import re
import sqlite3

import pandas as pd
import yaml


class Device:
    def __init__(self, device_type, vendor, interface_name=None, port1=None, port2=None, audience_id=None):
        """
        Инициализация нового объекта Device.

        Args:
            device_type (str): Тип устройства (например, "Switch").
            vendor (str): Производитель устройства (например, "Cisco").
            interface_name (str): Имя интерфейса (например, "f0/1").
            audience_id (int): ID аудитории (например, 244).
        """
        self.device_type = device_type
        self.vendor = vendor
        self.port1 = port1
        self.port2 = port2
        self.audience_id = audience_id
        self.status = "active"  # Например, начальный статус

    def set_device_type(self, device_type):
        """Устанавливает тип устройства."""
        self.device_type = device_type

    def set_vendor(self, vendor):
        """Устанавливает производителя."""
        self.vendor = vendor

    def set_port1(self, port1):
        """Устанавливает производителя."""
        self.port1 = port1

    def set_port2(self, port2):
        """Устанавливает производителя."""
        self.port2 = port2

    def set_audience_id(self, audience_id):
        """Устанавливает производителя."""
        self.audience_id = audience_id

    # Геттеры (если они вам нужны)
    def get_device_type(self):
        return self.device_type

    def get_vendor(self):
        return self.vendor

    def get_port1(self):
        return self.port1

    def get_port2(self):
        return self.port2

    def get_audience_id(self, audience_id):
        return self.audience_id

    def get_group_name(self):
        """
        Определяет группу Ansible на основе audience_id.
        """
        if self.audience_id == 224:
            return "KK-224"
        elif self.audience_id == 344:
            return "KK-344"
        else:
            return "group_unknown"  # Или обработайте неизвестные аудитории другим способом


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
    print(elements)
    for element in elements:
        device = []
        if element == 'Switch' or element == 'Router':
            device = Device(element, 'Any')
        else:
            match = re.match(r'([^(]*)\(([^)]*)\)', element)
            device = Device(match.group(1), match.group(2))
        devices.append(device)
    update_bd(devices)


def add_vlan(vlan, switchport, groups_id, audience):
    try:
        with sqlite3.connect('vlan_config.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vlan_config (vlan, switchport, groups_id, audience)
                VALUES (?, ?, ?, ?)
            """, (vlan, switchport, groups_id, audience))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении VLAN: {e}")
    finally:
        if conn:
            conn.close()


def clear_vlan(groups_id, output_file="vlan_playbook.yaml"):
    try:
        with sqlite3.connect('vlan_config.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE vlan_config
                   SET groups_id = 0  
                   WHERE switchport = 'PC' and groups_id = ?     
                """, (groups_id,)
            )
            conn.commit()
            cursor.execute(
                """SELECT * FROM vlan_config
                WHERE groups_id = ?
                """, (groups_id,)
            )

            available_devices = cursor.fetchall()
            cursor.execute(
                """DELETE FROM vlan_config
                   WHERE groups_id = ?     
                """, (groups_id,)  # Важно: передаем groups_id в виде кортежа
            )

            conn.commit()
            print(f"Удалено {cursor.rowcount} записей с groups_id = {groups_id}")
            playbook = []
            device_group = {}
            for device in available_devices:
                auditorium = device[3]
                if auditorium not in device_group:
                    device_group[auditorium] = {'hosts': auditorium, 'gather_facts': 'no', 'tasks': []}
                del_vlan_task(device_group, auditorium, device[1], device[0])
            playbook.extend(list(device_group.values()))
            try:
                playbook_yaml = yaml.dump(playbook, indent=2, allow_unicode=True)
                with open(output_file, "w", encoding='utf-8') as f:
                    f.write(playbook_yaml)
                return True
            except Exception as e:
                print(f"Ошибка при записи playbook в файл: {e}")
                return False
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении VLAN: {e}")
    finally:
        if conn:
            conn.close()


def add_vlan_task(device_group, group_name, interface_name, vlan):
    task = {
        'name': f"Настройка порта {interface_name} в VLAN {vlan}",
        'ios_config': {
            'parents': f"interface {interface_name}",
            'lines': [
                "switchport mode access",
                f"switchport access vlan {vlan}",
                "no cdp enable",
            ],
        },
    }
    device_group[group_name]['tasks'].append(task)


def free_vm():
    try:
        conn = sqlite3.connect('vlan_config.db')
        cursor = conn.cursor()
        query_check = """
                    SELECT vlan FROM vlan_config WHERE groups_id = 0 ORDER BY vlan LIMIT 2;
                """
        cursor.execute(query_check)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Ошибка при получении VLAN: {e}")
        return False  # Возврат False в случае ошибки


def del_vlan_task(device_group, group_name, interface_name, vlan):
    task = {
        'name': f"Настройка порта {interface_name} в VLAN {vlan}",
        'ios_config': {
            'parents': f"interface {interface_name}",
            'lines': [
                "no switchport mode access",
                f"no switchport access vlan {vlan}",
                "cdp enable",
            ],
        },
    }
    device_group[group_name]['tasks'].append(task)


def create_playbook(devices, group_id, output_file="vlan_playbook.yaml", param=True):
    playbook = []
    vlan = 10  # Начальное значение VLAN
    vlan_max = None

    try:
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('vlan_config.db')
        cursor = conn.cursor()

        # Определяем максимальный номер VLAN из таблицы
        result = free_vm()
        if len(result) == 2:
            vlan = result[0][0]
            vlan_max = result[1][0]
            cursor.execute(
                """UPDATE vlan_config
                   SET groups_id = ?  
                   WHERE vlan IN (?, ?)     
                """, (group_id, vlan, vlan_max)
            )
            conn.commit()
        else:
            print("Нет свободных ВМ")
            return False

    except Exception as e:
        print(f"Ошибка при получении VLAN: {e}")
        return False  # Возврат False в случае ошибки

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    # Формируем блоки плейбуков для каждой группы устройств
    device_group = {}
    for device in devices:
        auditorium = device.get_group_name()
        interface_name = []
        interface_name.append(device.get_port1())
        interface_name.append(device.get_port2())
        # Добавляем задания для группы устройств
        if auditorium not in device_group:
            device_group[auditorium] = {'hosts': auditorium, 'gather_facts': 'no', 'tasks': []}
        if param:
            # Добавляем задачи для каждого интерфейса
            add_vlan_task(device_group, auditorium, interface_name[0], vlan)
            add_vlan(vlan, interface_name[0], group_id, auditorium)
            if device == devices[-1]:
                vlan = vlan_max
            else:
                vlan += 10
            add_vlan_task(device_group, auditorium, interface_name[1], vlan)
            add_vlan(vlan, interface_name[0], group_id, auditorium)
        else:
            # Добавляем задание для конкретной группы
            del_vlan_task(device_group, auditorium, interface_name[0], vlan)
            vlan += 10
            del_vlan_task(device_group, auditorium, interface_name[1], vlan)

    # Преобразуем словарь групп в список плейбучных заданий
    playbook.extend(list(device_group.values()))

    try:
        # Конвертирование плейбука в YAML и запись в файл
        playbook_yaml = yaml.dump(playbook, indent=2, allow_unicode=True)
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(playbook_yaml)
        return True
    except Exception as e:
        print(f"Ошибка при записи playbook в файл: {e}")
        return False


def update_bd(devices):
    try:
        with sqlite3.connect(db_filename) as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")
            group_id = max_groups_id() + 1
            for device in devices:
                # Проверка доступности
                available_devices = cursor.execute(
                    """SELECT COUNT(*), component_id, location,port1,port2 FROM components
                    WHERE component_type=? AND model=? AND status!=?
                    """, (device.get_device_type(), device.get_vendor(), "Active")).fetchone()
                device.set_audience_id(available_devices[2])
                device.set_port1(available_devices[3])
                device.set_port2(available_devices[4])
                if available_devices[0] and len(free_vm()) == 2:
                    # Если устройство доступно, обновляем статус
                    cursor.execute(
                        """UPDATE components
                           SET status=?, groups_id = ?
                           WHERE component_id=?
                        """, ('Active', group_id, available_devices[1]))

                else:
                    print("Оборудование отсутствует!")
                    conn.rollback()
                    return False
            conn.commit()

        # test()
        create_playbook(devices, group_id)
    except Exception as e:
        print(f"Ошибка: {e}")


def check_enough(component_type, cursor, model, new_status):
    # Добавить Any
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


def max_groups_id():
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        result = cursor.execute("""
            SELECT MAX(groups_id) 
            FROM components 
            WHERE groups_id IS NOT NULL
        """)
        group_id = result.fetchone()[0]
        cursor.close()
        conn.close()
        return (group_id)
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def test():
    try:
        conn = sqlite3.connect(db_filename)
        query = "SELECT * FROM components WHERE status = 'Active'"
        devices = pd.read_sql_query(query, conn)
        print(devices)
        conn.close()
        conn = sqlite3.connect('vlan_config.db')
        cursor = conn.cursor()
        query_update = """
                UPDATE vlan_config
                SET groups_id = 0 
                WHERE groups_id = -1
            """
        #cursor.execute(query_update)
        #conn.commit()
        query = "SELECT * FROM vlan_config"
        devices = pd.read_sql_query(query, conn)
        cursor.execute(
            """SELECT * FROM vlan_config
            """,
        )

        available_devices = cursor.fetchall()
        print(available_devices)
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def clear_bd(groups_id, db_filename = 'test.db'):  # Добавим db_filename как параметр
    conn = None  # Инициализируем conn вне try
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        query = "UPDATE components SET status = 'Free' WHERE status = 'Active' AND `groups_id` = ?"
        cursor.execute(query, (groups_id,))
        conn.commit()
        print(f"Обновлено {cursor.rowcount} записей в components.")
        try:
            clear_vlan(groups_id)
        except Exception as e:
            print(f"Ошибка при вызове clear_vlan: {e}")
            # Решите, нужно ли продолжать или прервать выполнение

    except sqlite3.Error as e:
        print(f"Произошла ошибка при работе с базой данных: {e}")
    finally:
        if conn:
            conn.close()


#clear_bd(42)
#test()
#planner(text)
#test()
