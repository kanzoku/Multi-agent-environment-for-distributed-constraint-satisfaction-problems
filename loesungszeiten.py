import pandas as pd
import matplotlib.pyplot as plt
import os
import re

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


def create_and_save_combined_plot(data, systeme, architekturen, metric, ylabel, sheet_name, output_folder):
    if data.empty:
        print(f"No data for sheet {sheet_name}")
        return

    systeme = sorted(systeme, key=lambda x: int(re.search(r'\d+', x).group()))

    bar_width = 0.2
    inter_bar_width = 0.05
    group_width = (bar_width + inter_bar_width) * len(architekturen)
    index = [i * (group_width + 0.3) for i in range(len(systeme))]

    color_map = {
        'Problem-oriented (ASC)': 'blue',
        'Problem-oriented (DESC)': 'green',
        'Problem-oriented (Random)': 'red',
        'Hierarchical': 'orange',
        'Decentralized': 'purple',
        'Specialized (ASC)': 'brown',
        'Specialized (DESC)': 'pink',
        'Specialized (Random)': 'gray'
    }

    plt.figure(figsize=(12, 8))

    for i, architektur in enumerate(architekturen):
        means = []
        for system in systeme:
            system_data = data[(data['System'] == system) & (data['Architektur'] == architektur)][metric]
            mean_value = system_data.mean()
            means.append(mean_value)

        plt.bar([x + i * (bar_width + inter_bar_width) for x in index], means, width=bar_width,
                color=color_map.get(architektur, 'black'),
                label=architektur)

    level = re.sub(r'\s*\(E\)', '', sheet_name)

    plt.xlabel('System', fontsize=18)
    plt.ylabel(f'{ylabel} (ms)', fontsize=18)
    plt.title(f'{ylabel} for {level}', fontsize=20)
    plt.xticks([x + (bar_width + inter_bar_width) * (len(architekturen) / 2) for x in index], systeme, fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(fontsize=16)

    if '4x4' or 'Level 3' in sheet_name:
        plt.yscale('log')
    else:
        plt.ticklabel_format(style='plain', axis='y')

    sanitized_title = sanitize_filename(f'{ylabel} for {level}')
    png_filename = f"{sanitized_title}.png"
    svg_filename = f"{sanitized_title}.svg"

    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, png_filename))
    plt.savefig(os.path.join(output_folder, svg_filename), format='svg')
    plt.close()


statistik_file_path = 'Statistik_der_Testreihen.xlsx'

xls = pd.ExcelFile(statistik_file_path)

for sheet_name in xls.sheet_names:
    sheet_data = pd.read_excel(statistik_file_path, sheet_name=sheet_name)
    sheet_data['Architektur'] = sheet_data['Architektur'].replace(
        {
            'Problemorientiert (ASC)': 'Problem-oriented (ASC)',
            'Problemorientiert (DESC)': 'Problem-oriented (DESC)',
            'Problemorientiert (Random)': 'Problem-oriented (Random)',
            'Hierarchisch': 'Hierarchical',
            'Dezentral': 'Decentralized',
            'Spezialisiert (ASC)': 'Specialized (ASC)',
            'Spezialisiert (DESC)': 'Specialized (DESC)',
            'Spezialisiert (Random)': 'Specialized (Random)'
        }
    )
    systeme = sheet_data['System'].unique()
    architekturen = sheet_data['Architektur'].unique()

    create_and_save_combined_plot(sheet_data, systeme, architekturen, 'Durchschnittliche Lösungszeit',
                                  'Average Solution Time', sheet_name, output_folder)

