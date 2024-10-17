import pandas as pd


file_path = 'datenbank.xlsx'
sheet_name = 'Ergebnisse'
data = pd.read_excel(file_path, sheet_name=sheet_name)


data['Erfolg'] = data['Erfolg'].str.lower()


level_configs = {
    'Level 1': {
        'systems': {
            '24 Core': list(range(9, 17)),
            '12 Core': list(range(51, 59)),
            '4 Core': list(range(93, 101))
        },
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)']
    },
    'Level 2': {
        'systems': {
            '24 Core': list(range(17, 25)),
            '12 Core': list(range(59, 67)),
            '4 Core': list(range(101, 109))
        },
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)']
    },
    'Level 3': {
        'systems': {
            '24 Core': list(range(25, 33)),
            '12 Core': list(range(67, 75)),
            '4 Core': list(range(109, 117))
        },
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)']
    },
    'Level 4': {
        'systems': {
            '24 Core': list(range(33, 39)),
            '12 Core': list(range(75, 81)),
            '4 Core': list(range(117, 123))
        },
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)']
    },
    'Level 5': {
        'systems': {
            '24 Core': list(range(39, 43)),
            '12 Core': list(range(81, 85)),
            '4 Core': list(range(123, 127))
        },
        'testreihe_names': ['Problemorientiert (ASC)',
                            'Spezialisiert (ASC)', 'Spezialisiert (DESC)', 'Spezialisiert (Random)']
    }
}

additional_config = {
    '4x4 Sudoku': {
        'systems': {
            '24 Core': list(range(1, 9)),
            '12 Core': list(range(43, 51)),
            '4 Core': list(range(85, 93)),
            '2 Core': list(range(127, 135))
        },
        'testreihe_names': ['Problemorientiert (ASC)', 'Problemorientiert (DESC)', 'Problemorientiert (Random)',
                            'Hierarchisch', 'Dezentral', 'Spezialisiert (ASC)', 'Spezialisiert (DESC)',
                            'Spezialisiert (Random)']
    }
}


def calculate_statistics(data, configs, include_unsuccessful=False):
    statistics = []

    for config_name, config in configs.items():
        for system, testreihe_ids in config['systems'].items():
            for test_id, test_name in zip(testreihe_ids, config['testreihe_names']):
                loesungszeit = data[data['Testreihe-ID'] == test_id]['Lösungszeit (ms)']
                loesungsnachrichten = data[data['Testreihe-ID'] == test_id]['Lösungs-Nachrichten']
                wertveraenderungen = data[data['Testreihe-ID'] == test_id]['Wertveränderungen']
                erfolg = data[data['Testreihe-ID'] == test_id]['Erfolg']

                if include_unsuccessful:
                    avg_loesungszeit = loesungszeit.mean()
                    std_loesungszeit = loesungszeit.std()
                    median_loesungszeit = loesungszeit.median()
                    avg_loesungsnachrichten = loesungsnachrichten.mean()
                    std_loesungsnachrichten = loesungsnachrichten.std()
                    median_loesungsnachrichten = loesungsnachrichten.median()
                    avg_wertveraenderungen = wertveraenderungen.mean()
                    std_wertveraenderungen = wertveraenderungen.std()
                    median_wertveraenderungen = wertveraenderungen.median()
                else:
                    successful_filter = erfolg == 'ja'
                    avg_loesungszeit = loesungszeit[successful_filter].mean()
                    std_loesungszeit = loesungszeit[successful_filter].std()
                    median_loesungszeit = loesungszeit[successful_filter].median()
                    avg_loesungsnachrichten = loesungsnachrichten[successful_filter].mean()
                    std_loesungsnachrichten = loesungsnachrichten[successful_filter].std()
                    median_loesungsnachrichten = loesungsnachrichten[successful_filter].median()
                    avg_wertveraenderungen = wertveraenderungen[successful_filter].mean()
                    std_wertveraenderungen = wertveraenderungen[successful_filter].std()
                    median_wertveraenderungen = wertveraenderungen[successful_filter].median()

                stats = {
                    'Kategorie': config_name,
                    'System': system,
                    'Architektur': test_name,
                    'Durchschnittliche Lösungszeit': avg_loesungszeit,
                    'Standardabweichung Lösungszeit': std_loesungszeit,
                    'Median Lösungszeit': median_loesungszeit,
                    'Durchschnittliche Lösungsnachrichten': avg_loesungsnachrichten,
                    'Standardabweichung Lösungsnachrichten': std_loesungsnachrichten,
                    'Median Lösungsnachrichten': median_loesungsnachrichten,
                    'Durchschnittliche Wertveränderungen': avg_wertveraenderungen,
                    'Standardabweichung Wertveränderungen': std_wertveraenderungen,
                    'Median Wertveränderungen': median_wertveraenderungen,
                    'Erfolgreiche Lösungen': (erfolg == 'ja').sum()
                }

                statistics.append(stats)

    df = pd.DataFrame(statistics)

    df = df.applymap(lambda x: '{:.2f}'.format(x) if isinstance(x, (int, float)) else x)
    df = df.applymap(lambda x: x.rstrip('0').rstrip('.') if isinstance(x, str) and '.' in x else x)

    return df


statistics_df_include = calculate_statistics(data, level_configs, include_unsuccessful=True)
statistics_df_exclude = calculate_statistics(data, level_configs, include_unsuccessful=False)
additional_statistics_df_include = calculate_statistics(data, additional_config, include_unsuccessful=True)
additional_statistics_df_exclude = calculate_statistics(data, additional_config, include_unsuccessful=False)

with pd.ExcelWriter('Statistik_der_Testreihen.xlsx') as writer:
    for level in level_configs.keys():
        df_include = statistics_df_include[statistics_df_include['Kategorie'] == level]
        df_exclude = statistics_df_exclude[statistics_df_exclude['Kategorie'] == level]
        df_include.to_excel(writer, sheet_name=f'{level} (mnE)', index=False)
        df_exclude.to_excel(writer, sheet_name=f'{level} (E)', index=False)
    additional_statistics_df_include.to_excel(writer, sheet_name='4x4 Sudoku (mnE)', index=False)
    additional_statistics_df_exclude.to_excel(writer, sheet_name='4x4 Sudoku (E)', index=False)

