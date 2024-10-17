import pandas as pd
import matplotlib.pyplot as plt
import os
import re

file_path = 'datenbank.xlsx'
sheet_name = 'Übersicht'

data = pd.read_excel(file_path, sheet_name=sheet_name)

data['System'] = data['System'].astype(str)
systeme = sorted(data['System'].unique(), key=int)
agentensysteme = data['Agentsystem'].unique()
sizes = data['Size'].unique()

output_folder = 'W:\\data\\03_Studium\\Bachelorarbeit\\Grafiken\\Plots'
os.makedirs(output_folder, exist_ok=True)


def sanitize_filename(title):
    umlaut_map = str.maketrans({
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue',
        'ß': 'ss'
    })
    title = title.translate(umlaut_map)
    title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
    return title


agentensystem_titel_map = {
    'constraint': 'Problem-oriented Architecture',
    'decentralized': 'Decentralized Architecture',
    'hierarchical': 'Hierarchical Architecture',
    'combined': 'Specialized Architecture'
}

color_map = {
    'Problem-oriented Architecture': 'blue',
    'Decentralized Architecture': 'green',
    'Hierarchical Architecture': 'red',
    'Specialized Architecture': 'orange'
}


def create_and_save_combined_plot(data, systeme, agentensysteme, size, output_folder, agentensystem_titel_map):
    if size == '9x9':
        filtered_systeme = sorted([system for system in systeme if system != '2'], key=int)
    elif size == '4x4':
        filtered_systeme = sorted(systeme, key=int)
    else:
        filtered_systeme = sorted(systeme, key=int)

    data_filtered = data[data['Size'] == size]

    if data_filtered.empty:
        print(f"No data for size {size}")
        return

    bar_width = 0.2
    inter_bar_width = 0.05
    group_width = (bar_width + inter_bar_width) * len(agentensysteme)
    index = [i * (group_width + 0.3) for i in range(len(filtered_systeme))]

    plt.figure(figsize=(12, 8))

    for i, agentensystem in enumerate(agentensysteme):
        means = []
        for system in filtered_systeme:
            system_data = data_filtered[
                (data_filtered['System'] == system) & (data_filtered['Agentsystem'] == agentensystem)
            ]['Gesamt-Initialisierungszeit (ms)']
            mean_value = system_data.mean()
            means.append(mean_value)

        plt.bar(
            [x + i * (bar_width + inter_bar_width) for x in index],
            means,
            width=bar_width,
            color=color_map[agentensystem_titel_map.get(agentensystem, agentensystem)],
            label=agentensystem_titel_map.get(agentensystem, agentensystem)
        )

    plt.xlabel('System', fontsize=18)
    plt.ylabel('Average Initialization Time (ms)', fontsize=18)
    plt.title(f'Average Initialization Time for Different Architectures ({size})', fontsize=20)
    plt.xticks([x + (bar_width + inter_bar_width) * (len(agentensysteme) / 2) for x in index],
               [f"{system} Core" for system in filtered_systeme], fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(fontsize=16)

    if '4x4' not in size:
        plt.ticklabel_format(style='plain', axis='y')

    title = f'Average Initialization Time for Different Architectures ({size})'
    sanitized_title = sanitize_filename(title)
    filename = f"{sanitized_title}.png"
    svg_filename = f"{sanitized_title}.svg"
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, filename))
    plt.savefig(os.path.join(output_folder, svg_filename), format='svg')
    plt.close()

create_and_save_combined_plot(data, systeme, agentensysteme, '9x9', output_folder, agentensystem_titel_map)
create_and_save_combined_plot(data, systeme, agentensysteme, '4x4', output_folder, agentensystem_titel_map)

