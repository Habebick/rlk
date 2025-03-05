import sqlite3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

db_filename = 'mydatabase.db'

def generate_table():
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        audiences = [224, 344, 411]

        table_data = {}
        for aud in audiences:
            cursor.execute(
                "SELECT component_type, model, status FROM components WHERE location = ?", (aud,)
            )
            devices = cursor.fetchall()

            device_names = []
            for i, device in enumerate(devices):
                component_type, model, status = device
                device_name = f"{component_type[0]}{i + 1}-{model}"
                table_data.setdefault(aud, []).append((device_name, status))

        max_rows = max(len(table_data.get(aud, [])) for aud in audiences)
        num_cols = len(audiences)

        fig, ax = plt.subplots()
        ax.axis('off')
        cell_text = []
        colors = []
        for i in range(max_rows):
            row_text = []
            row_colors = []
            for aud_idx, aud in enumerate(audiences):
                if i < len(table_data[aud]):
                    device_name, status = table_data[aud][i]
                    row_text.append(device_name)
                    if status == 'Active':
                        row_colors.append(mcolors.to_hex('lightcoral'))
                    elif status == 'Free':
                        row_colors.append(mcolors.to_hex('lightgreen'))
                    else:
                         row_colors.append(mcolors.to_hex('lightgrey'))
                else:
                    row_text.append('')
                    row_colors.append('white')

            cell_text.append(row_text)
            colors.append(row_colors)

        col_labels = [f"P{aud}" for i, aud in enumerate(audiences)]
        table = ax.table(cellText=cell_text,
                         colLabels=col_labels,
                         cellLoc='center',
                         loc='center',
                         cellColours=colors)
        table.scale(1, 1.5)

        plt.tight_layout()
        plt.show()
    finally:
        if conn:
            conn.close()

