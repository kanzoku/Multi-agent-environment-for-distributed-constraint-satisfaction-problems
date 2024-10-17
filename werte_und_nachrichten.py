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


def create_and_save_bar_plot_by_level(data, levels, architekturen, metric, ylabel, output_folder):
    if data.empty:
        print(f"No data available")
        return

    print(f"Creating bar plot for: {metric}")

    bar_width = 0.1
    inter_bar_width = 0.05
    group_width = (bar_width + inter_bar_width) * len(architekturen)
    index = [i * (group_width + 0.3) for i in range(len(levels))]

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
        for level in levels:
            level_data = data[(data['Level'] == level) & (data['Architektur'] == architektur)][metric]
            mean_value = level_data.mean()
            means.append(mean_value)
            print(f"Level: {level}, Architecture: {architektur}, Mean: {mean_value}")

        plt.bar([x + i * (bar_width + inter_bar_width) for x in index], means, width=bar_width,
                color=color_map.get(architektur, 'black'), label=architektur)

    plt.xlabel('Levels', fontsize=18)
    plt.ylabel(ylabel, fontsize=18)
    plt.yscale('log')
    plt.title(f'{ylabel} for all Levels', fontsize=20)
    plt.xticks([x + (bar_width + inter_bar_width) * (len(architekturen) / 2) for x in index], levels, fontsize=16)
    plt.legend()
    plt.yticks(fontsize=16)

    title = f'{ylabel} for all Levels'
    sanitized_title = sanitize_filename(title)

    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{sanitized_title}_bar.png"))
    plt.savefig(os.path.join(output_folder, f"{sanitized_title}_bar.svg"), format='svg')
    plt.close()


def create_and_save_line_plot_by_level(data, levels, architekturen, metric, ylabel, output_folder):
    if data.empty:
        print(f"No data available")
        return

    print(f"Creating line plot for: {metric}")

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
        for level in levels:
            level_data = data[(data['Level'] == level) & (data['Architektur'] == architektur)][metric]
            mean_value = level_data.mean()
            means.append(mean_value)
            print(f"Level: {level}, Architecture: {architektur}, Mean: {mean_value}")

        plt.plot(levels, means, marker='o', label=architektur, color=color_map.get(architektur, 'black'))

    plt.xlabel('', fontsize=18)
    plt.ylabel(ylabel, fontsize=18)
    plt.yscale('log')
    plt.title(f'{ylabel} for all Levels', fontsize=20)
    plt.xticks(rotation=45, fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(fontsize=16)

    title = f'{ylabel} for all Levels'
    sanitized_title = sanitize_filename(title)

    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f"{sanitized_title}_line.png"))
    plt.savefig(os.path.join(output_folder, f"{sanitized_title}_line.svg"), format='svg')
    plt.close()


statistik_file_path = 'Statistik_der_Testreihen.xlsx'

xls = pd.ExcelFile(statistik_file_path)

successful_sheets = [sheet_name for sheet_name in xls.sheet_names if '(E)' in sheet_name and '4x4 Sudoku' not in sheet_name]

all_data = pd.DataFrame()
for sheet_name in successful_sheets:
    sheet_data = pd.read_excel(statistik_file_path, sheet_name=sheet_name)
    level_number = re.search(r'\d+', sheet_name).group()
    sheet_data['Level'] = f'Level {level_number}'

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
    all_data = pd.concat([all_data, sheet_data], ignore_index=True)

print("All data:")
print(all_data.head())

levels = sorted(set(all_data['Level'].unique()), key=lambda x: int(re.search(r'\d+', x).group()))
architekturen = all_data['Architektur'].unique()

print("Levels:", levels)
print("Architectures:", architekturen)

create_and_save_bar_plot_by_level(all_data, levels, architekturen, 'Durchschnittliche Lösungsnachrichten', 'Average Solution Messages', output_folder)
create_and_save_line_plot_by_level(all_data, levels, architekturen, 'Durchschnittliche Lösungsnachrichten', 'Average Solution Messages', output_folder)
create_and_save_bar_plot_by_level(all_data, levels, architekturen, 'Durchschnittliche Wertveränderungen', 'Average Value Changes', output_folder)
create_and_save_line_plot_by_level(all_data, levels, architekturen, 'Durchschnittliche Wertveränderungen', 'Average Value Changes', output_folder)

