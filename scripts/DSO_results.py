import pandas as pd
import os
from tabulate import tabulate
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def show_past_results():
    print("Saved Results:")
    filedict = dict()
    filenames = os.listdir('data_saves')
    filenames = [i for i in filenames if i != '.DS_Store']
    for i, name in enumerate(filenames):
        filedict.update({i: name})
        print(f"   [{i}] {name}")
    file_num = int(input('File number to examine: '))
    df = pd.read_csv('data_saves/' + filedict[file_num])

    # present results
    print("\nWhat would you like to sort by?")
    sortoptions = ["Type", "Constellation", "Magnitude", "Size", "Hours_Until_Set", "Magnitude and Size"]
    print(*sortoptions, sep=" | ")
    category = input("Input category: ")
    if category.upper() == "MAGNITUDE AND SIZE":
        df_z_scaled = df.copy()
        df_z_scaled['Magnitude_Score'] = (df_z_scaled['Magnitude'] - df_z_scaled['Magnitude'].mean()) / df_z_scaled['Magnitude'].std()
        df_z_scaled['Size_Score'] = (df_z_scaled['Size'] - df_z_scaled['Size'].mean()) / df_z_scaled['Size'].std() 
        sorted_results = df_z_scaled.loc[(0.6*df_z_scaled['Magnitude_Score'] + 0.4 * df_z_scaled['Size_Score']).sort_values().index] # currently on 60% 40% weighting
    else:
        sorted_results = df.sort_values(by=[category])
    
    num_to_display = int(input(f"\nNumber of objects to display out of {len(sorted_results)}: "))
    print("Columns: ")
    #df_z_scaled = df_z_scaled.drop(columns=['Unnamed: 0'])
    sorted_results = sorted_results.drop(columns=['Unnamed: 0'])
    print("   ", *sorted_results.columns[0:9], sep=' | ')
    print("   ", *sorted_results.columns[9:16], sep=' | ')
    print('    Overview = ObjectNum, Name, Type, Constellation, Magnitude, Size, Hours_Until_Set, Altitude, Azimuth')
    cols_input = input("Columns to be presented: ").split(' ')
    if cols_input == ['overview']:
        cols_input = ["ObjectNum", "Name", "Type", "Constellation", "Magnitude", "Size", "Hours_Until_Set", "Alt", "Az"]
    else:
        pass

    if category.upper() == "MAGNITUDE AND SIZE":
        print("Displaying selected columns for the ranked objects weighted 60% for Magnitude and 40% for Size")
    else:
        print(f"Displaying selected columns for the ranked objects sorted by {category}")
    showing = sorted_results[cols_input].head(num_to_display)
    print(f"Showing {num_to_display}/{len(sorted_results)} rows\n")
    print(tabulate(showing, headers=showing.columns, tablefmt='grid', showindex='never'))

if __name__ == "__main__":
    show_past_results()