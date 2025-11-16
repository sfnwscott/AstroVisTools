import pandas as pd
import requests
import json
import datetime
import numpy as np
from pytz import timezone
from tabulate import tabulate
import sys
from termcolor import colored, cprint

def filter_objects_start(df, hemisphere, max_mag, size_range, object_types, s_after):
    northern_constellations = ["Ursa Major", "Ursa Minor", "Draco", "Cassiopeia", "Cepheus", "Camelopardalis", "Perseus", "Auriga", "Gemini", "Cancer", "Leo", "Lynx", "Boötes", "Hercules", "Lyra", "Cygnus", "Aquila", "Delphinus", "Pegasus", "Andromeda", "Triangulum", "Aries", "Taurus", "Orion", "Eridanus", "Cetus", "Fornax", "Sculptor", "Auriga", "Gemini", "Canis Major", "Canis Minor", "Monoceros", "Lepus", "Columba", "Puppis", "Vela", "Carina", "Pyxis", "Hydra", "Sextans", "Crater", "Corvus", "Leo Minor", "Coma Berenices", "Canes Venatici", "Virgo", "Libra", "Scorpius", "Ophiuchus", "Serpens", "Sagittarius", "Corona Borealis", "Hercules", "Draco", "Aquarius", "Capricornus", "Pisces", "Cepheus", "Cassiopeia", "Andromeda", "Lacerta", "Vulpecula", "Sagitta", "Cygnus", "Cepheus", "Pegasus", "Equuleus", "Delphinus", "Vulpecula", "Lyra", "Aquila", "Serpens", "Ophiuchus", "Scutum", "Sagittarius", "Corona Australis", "Telescopium", "Indus", "Microscopium", "Piscis Austrinus", "Grus", "Phoenix", "Tucana", "Pavo", "Octans", "Apus", "Mensa", "Chamaeleon", "Musca", "Volans", "Carina", "Circinus", "Crux", "Centaurus", "Lupus", "Ara", "Scorpius", "Norma", "Triangulum Australe", "Aries", "Taurus", "Gemini", "Cancer", "Canis Minor", "Lepus", "Monoceros", "Orion", "Gemini", "Canis Major", "Canis Minor", "Puppis", "Hydra", "Sextans", "Crater", "Corvus", "Crux", "Carina", "Vela", "Antlia", "Pyxis", "Pictor", "Dorado", "Reticulum", "Horologium", "Caelum", "Mensa"] # fill in with all constellations that are visible in north
    southern_constellations = ["Crux", "Carina", "Vela", "Centaurus", "Lupus", "Ara", "Scorpius", "Norma", "Triangulum Australe", "Aries", "Taurus", "Gemini", "Cancer", "Canis Minor", "Lepus", "Monoceros", "Orion", "Hydra", "Sextans", "Crater", "Corvus", "Virgo", "Libra", "Scorpius", "Ophiuchus", "Sagittarius", "Corona Australis", "Telescopium", "Indus", "Microscopium", "Piscis Austrinus", "Grus", "Phoenix", "Tucana", "Pavo", "Octans", "Apus", "Mensa", "Chamaeleon", "Musca", "Volans", "Carina", "Circinus", "Crux", "Centaurus", "Lupus", "Ara", "Scorpius", "Norma", "Triangulum Australe", "Aries", "Taurus", "Gemini", "Cancer", "Canis Minor", "Lepus", "Monoceros", "Orion", "Pictor", "Dorado", "Reticulum", "Horologium", "Caelum", "Mensa"] # fill in with constellations that are visible in south
    if hemisphere == 'N':
        valid_constellations = northern_constellations
    else:
        valid_constellations = southern_constellations
    print(f"\nNumber of Objects: {len(df)}")
    df_SS = df.tail(8) # last 8 are the planets + moon. These would get filtered out by constellation but we want to keep for now
    df = df.drop(df_SS.index) # remove manually to be later readded

    # # filter by if it's in the list of valid_constellations
    # df = df[df.Constellation.isin(valid_constellations)]
    # print(f"Number of Objects: {len(df)}")
   
    # filter by maximum magnitude
    df.Magnitude.astype(float)
    if len(df) == 0:
        quit('Parameters too tight')
    df = df[df.Magnitude <= max_mag]
    print(f"Number of Objects: {len(df)}")
    
    # range of min to max angular size
    df.Size.astype(float)
    if len(df) == 0:
        quit('Parameters too tight')
    df = df[(df.Size >= size_range[0]) & (df.Size <= size_range[1])]
    print(f"Number of Objects: {len(df)}")

    # re-add planets + moon
    df = pd.concat([df, df_SS])

    # specify object type
    df = df[df.Type.isin(object_types)]
    if len(df) == 0:
        quit('Parameters too tight')
    print(f"Number of Objects: {len(df)}")

    # get stellarium data
    df.reset_index(drop=True, inplace=True)
    above_horizon, alt, az, rise, set = [], [], [], [], []
    for i in range(len(df)):
        obj_name = str(df.ObjectNum[i]).replace(' ', '')
        try:
            response = requests.get(f"http://localhost:8090/api/objects/info?name={obj_name}&format=json")
            info = json.loads(response.text)
        except:
            print(f"Failed to get data for object {obj_name}")
        above_horizon.append(info['above-horizon'])
        alt.append(round(info['altitude'], 2))
        az.append(round(info['azimuth'], 2))
        rise.append(info['rise'])
        set.append(info['set'])
    df['Above_Horizon'] = above_horizon
    df['Alt'] = alt
    df['Az'] = az
    df['Rise'] = rise
    df['Set'] = set
    
    # reduce to just currently visible objects
    df = df[df.Above_Horizon]
    print(f"Number of Objects: {len(df)}\n")
    # showing = df[df['ObjectNum'].str.contains('M')][['ObjectNum', 'Name']]
    # print(tabulate(showing, headers=showing.columns, tablefmt='grid', showindex='never'))
    
    
    # calculate time until object sets
    diffs = []
    for time in list(df.Set):
        try:
            time = time.split('h')
            time[1] = time[1][:-1]
            s_after_set = int(time[0]) * 3600 + int(time[1]) * 60
            if s_after > 84600 / 2:
                if s_after_set <= s_after:
                    diff = s_after_set + 86400 - s_after
                else:
                    diff = s_after_set - s_after
            else:
                diff = s_after_set - s_after
            diff = diff / 3600 # convert to hours
            diff = round(diff, 2) # round off
        except:
            diff = "---"      
        diffs.append(diff)
    df['Hours_Until_Set'] = diffs

    return df


df = pd.read_csv('object_datasets/object_data_accurate.csv')
print("Make sure to open Stellarium with Remote Control plugin installed")

# # get parameters
# hemisphere = input("Hemisphere ('N' or 'S'): ").upper() # N or S. Almost everything is N but whatever
# max_mag = float(input("Maximum Apparent Magnitude: "))
# min_angular_size = float(input("Minimum Angular Size (arcmin): "))
# max_angular_size = float(input("Maximum Angular Size (arcmin): "))
# size_range = (min_angular_size, max_angular_size)
# type_dict = {'CN': 'Cluster Nebulosity', 'DS': 'Double Star', 'SG': 'Spiral Galaxy', 'DN': 'Diffuse Nebula', 'EG': 'Elliptical Galaxy', 'GX': 'Galaxy', 'IG': 'Irregular Galaxy', 'GC': 'Globular Cluster', 'SC': 'Star Cloud', 'SR': 'Supernova Remnant', 'PN': 'Planetary Nebula', 'GA': 'Group/Asterism', 'OC': 'Open Cluster', 'LG': 'Lenticular (S0) Galaxy', 'PL': 'Planet', 'MN': 'Moon'}
# print("Object Types:")
# for key, val in type_dict.items():
#     print("   {} ({})".format(key, val))
# print("   ALL (All Object Types)")
# print("   Non_Cluster (All Except Globular and Open Clusters)")
# input_types = input("Input types seperated by a space: ").upper().split(' ')
# if input_types == ["ALL"]:
#     object_types = list(type_dict.values())
# elif input_types == ["NON_CLUSTER"]:
#     object_types = ['Cluster Nebulosity', 'Double Star', 'Spiral Galaxy', 'Diffuse Nebula', 'Elliptical Galaxy', 'Galaxy', 'Irregular Galaxy', 'Star Cloud', 'Supernova Remnant', 'Planetary Nebula', 'Group/Asterism', 'Lenticular (S0) Galaxy', 'Planet', 'Moon']
# else:
#     object_types = []
#     for key in input_types:
#         object_types.append(type_dict[key])
# using_now = input("Use current time (Y/N)?: ").upper()
# if using_now == "N":
#     input_date = input("Set date and 24hr time in CST (MM DD YYYY HH MM): ")
#     month, day, year, hour, minute = [int(val) for val in input_date.split(' ')]
#     date_time = datetime.datetime(year, month, day, hour, minute)
#     t = date_time.astimezone(timezone('UTC'))
#     UT_time = t.hour + t.minute/60
#     # equation via the US naval observatory
#     julian_date = 367*t.year - np.trunc(7*(t.year + np.trunc((t.month + 9)/12))/4) 
#     julian_date = julian_date + np.trunc(275*t.month / 9) + t.day + 1721013.5 
#     julian_date = julian_date + UT_time/24 - 0.5*np.sign(100*t.year + t.month - 190002.5) + 0.5
#     # update stellarium with inputted date in JD
#     requests.post(f"http://localhost:8090/api/main/time?time={julian_date}")
#     if t.hour < 5:
#         # if it's early morning in UTC, the hour is high since the start of last day 
#         s_after = int((t.hour + 24) - 5) * 3600 + int(t.minute) * 60
#     else:
#         # otherwise it's on the same day as CST
#         s_after = int(t.hour - 5) * 3600 + int(t.minute) * 60
#     # back to CST for the seconds after the start of day
#     now = str(datetime.datetime.now()) # for later when writing to csv
#     current_date, current_time = now.split(' ')
#     current_time_split = current_time.split(':')
# else: 
# get and use current time
now = str(datetime.datetime.now()) # for later when writing to csv
date, time = now.split(' ')
year, month, day = [int(val) for val in date.split('-')]
hour, minute, second = [int(val[:2]) for val in time.split(':')]
date_time = datetime.datetime(year, month, day, hour, minute, second)
t = date_time.astimezone(timezone('UTC'))
UT_time = t.hour + t.minute/60
current_date, current_time = now.split(' ')
current_time_split = current_time.split(':')
# equation via the US naval observatory
julian_date = 367*t.year - np.trunc(7*(t.year + np.trunc((t.month + 9)/12))/4) 
julian_date = julian_date + np.trunc(275*t.month / 9) + t.day + 1721013.5 
julian_date = julian_date + UT_time/24 - 0.5*np.sign(100*t.year + t.month - 190002.5) + 0.5
requests.post(f"http://localhost:8090/api/main/time?time={julian_date}")
# seconds since start of inputted CST day
s_after = int(hour) * 3600 + int(minute) * 60


# update planets' current magnitudes, sizes, and distances
SS_magnitudes, SS_distances, SS_sizes = [], [], []
for object in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Moon']:
    response = requests.get(f"http://localhost:8090/api/objects/info?name={object}&format=json")
    info = json.loads(response.text)
    SS_magnitudes.append(round(info['vmag'], 2))
    SS_distances.append(round(info['distance'] * 1.58125e-5, 2)) # convert from AU to ly
    SS_sizes.append(round(info['size-dd'] * 60, 2)) # convert dd to arcmins
df.loc[[len(df) - (8 - i) for i in range(8)], 'Magnitude'] = SS_magnitudes
df.loc[[len(df) - (8 - i) for i in range(8)], 'Distance (ly)'] = SS_distances
df.loc[[len(df) - (8 - i) for i in range(8)], 'Size'] = SS_sizes

# run function
df = filter_objects_start(df, 'N', 8, (0,30), ['Cluster Nebulosity', 'Double Star', 'Spiral Galaxy', 'Diffuse Nebula', 'Elliptical Galaxy', 'Galaxy', 'Irregular Galaxy', 'Star Cloud', 'Supernova Remnant', 'Planetary Nebula', 'Group/Asterism', 'Lenticular (S0) Galaxy', 'Planet', 'Moon'], s_after)

print(df)
