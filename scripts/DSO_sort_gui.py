import pandas as pd
import requests
import json
import datetime
import numpy as np
from pytz import timezone
from tabulate import tabulate
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
#from termcolor import colored, cprint

print("Make sure to open Stellarium with Remote Control plugin installed")

type_dict = {'CN': 'Cluster Nebulosity', 'DS': 'Double Star', 'SG': 'Spiral Galaxy', 
             'DN': 'Diffuse Nebula', 'EG': 'Elliptical Galaxy', 'GX': 'Galaxy', 'IG': 'Irregular Galaxy', 
             'GC': 'Globular Cluster', 'SC': 'Star Cloud', 'SR': 'Supernova Remnant', 
             'PN': 'Planetary Nebula', 'GA': 'Group/Asterism', 'OC': 'Open Cluster', 
             'LG': 'Lenticular (S0) Galaxy', 'PL': 'Planet', 'MN': 'Moon'}
non_cluster_types = ['Cluster Nebulosity', 'Double Star', 'Spiral Galaxy', 'Diffuse Nebula', 'Elliptical Galaxy', 'Galaxy', 'Irregular Galaxy', 'Star Cloud', 'Supernova Remnant', 'Planetary Nebula', 'Group/Asterism', 'Lenticular (S0) Galaxy', 'Planet', 'Moon']

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") 

class DSOsortApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Deep Space Object Finder")
        self.geometry("1400x800") # 1080x700
        self.minsize(980, 620)

        # Configure responsive grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # controls
        self.grid_rowconfigure(1, weight=1)   # table

        self._build_controls()
        self._build_table()
        self._style_treeview_dark()

    def _build_controls(self):
        shell = ctk.CTkFrame(self, corner_radius=18, fg_color=("gray95", "#0f1115"))
        shell.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        shell.grid_columnconfigure((0,1,2), weight=1)

        # Hemisphere, angular size, and magnitude card
        ha_card = self._card(shell, "Object Parameters", row=0, col=0)
        #ha_card.grid_configure(columnspan=2)

        # hemisphere
        hemi_row = ctk.CTkFrame(ha_card, fg_color="transparent")
        hemi_row.pack(fill="x", padx=8, pady=6)#pady6
        ctk.CTkLabel(hemi_row, text="Hemisphere", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))#0,4
        self.hemisphere_var = tk.StringVar(value="N")
        hemi_btns = ctk.CTkFrame(hemi_row, fg_color="transparent")
        hemi_btns.pack(anchor="w")
        ctk.CTkRadioButton(hemi_btns, text="Northern", variable=self.hemisphere_var, value="N").pack(side="left", padx=6)
        ctk.CTkRadioButton(hemi_btns, text="Southern", variable=self.hemisphere_var, value="S").pack(side="left", padx=6)
       
        # angular size
        size_row = ctk.CTkFrame(ha_card, fg_color="transparent")
        size_row.pack(fill="x", padx=8, pady=(0, 10))#pady 0,10
        ctk.CTkLabel(size_row, text="Angular Size (arcmin)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))
        self.size_min_var = tk.IntVar(value=0)
        self.size_max_var = tk.IntVar(value=30)
        entry_row = ctk.CTkFrame(size_row, fg_color="transparent")
        entry_row.pack(fill="x", padx=6, pady=(2, 4))
        ctk.CTkLabel(entry_row, text="Min:").pack(side="left", padx=(4, 4))
        self.size_min_entry = ctk.CTkEntry(entry_row, width=60, textvariable=self.size_min_var)
        self.size_min_entry.pack(side="left")
        ctk.CTkLabel(entry_row, text="Max:", padx=8).pack(side="left")
        self.size_max_entry = ctk.CTkEntry(entry_row, width=60, textvariable=self.size_max_var)
        self.size_max_entry.pack(side="left")

        # magnitude
        mag_row = ctk.CTkFrame(ha_card, fg_color="transparent")
        mag_row.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(mag_row, text="Maximum Magnitude", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))
        self.max_mag_var = tk.DoubleVar(value=9)
        slider_min, slider_max = 1, 12
        self.mag_slider = ctk.CTkSlider(mag_row, width=300, from_=slider_min, to=slider_max, 
                                        number_of_steps=2*(slider_max - slider_min), variable=self.max_mag_var,
                                        command=self._update_mag_label)
        self.mag_slider.set(self.max_mag_var.get())
        self.mag_slider.pack(side='left', padx=10, pady=(4, 8))
        self.mag_label = ctk.CTkLabel(mag_row, text=f"{float(self.max_mag_var.get())}")
        self.mag_label.pack(anchor="w", padx=5, pady=(0, 8))
       
        # Object Types (Checkboxes + Select All)
        types_card = self._card(shell, "Object Types", row=0, col=1)
        self.type_vars = {name: tk.BooleanVar(value=False) for name in type_dict.values()}
        self.select_all_var = tk.BooleanVar(value=False)
        self.select_non_cluster = tk.BooleanVar(value=False)

        types_head = ctk.CTkFrame(types_card, fg_color="transparent")
        types_head.pack(fill="x", padx=8, pady=(6, 2))
        ctk.CTkCheckBox(types_head, text="Select All",
                        variable=self.select_all_var,
                        command=self._toggle_select_all).pack(side="left")
        ctk.CTkCheckBox(types_head, text="Non Cluster",
                        variable=self.select_non_cluster,
                        command=self._toggle_select_noncluster).pack(side="left")
        
        grid = ctk.CTkScrollableFrame(types_card, height=90, fg_color=("gray94", "#0a0c10"))
        grid.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        # Arrange checkboxes in two columns
        cols = 2
        for i, name in enumerate(type_dict.values()):
            r, c = divmod(i, cols)
            cb = ctk.CTkCheckBox(grid, text=name, variable=self.type_vars[name],
                                 command=self._sync_select_all_state)
            cb.grid(row=r, column=c, sticky="w", padx=6, pady=2)

        # Date/Time Input (single text box) + Use current time
        dt_card = self._card(shell, "Observation Date & Time", row=0, col=2)
        row1 = ctk.CTkFrame(dt_card, fg_color="transparent")
        row1.pack(fill="x", padx=8, pady=(8, 2))
        self.dt_text_var = tk.StringVar()
        self.dt_entry = ctk.CTkEntry(
            row1,
            width=120,
            textvariable=self.dt_text_var,
            placeholder_text="MM DD YYYY HH MM"
        )
        self.dt_entry.pack(side="left")
        help_lbl = ctk.CTkLabel(
            row1,
            text="Format: MM DD YYYY HH MM",
            font=ctk.CTkFont(size=11),
            text_color=("#333", "#aeb3bc"),
        )
        help_lbl.pack(side="left", padx=(10, 0))
        row2 = ctk.CTkFrame(dt_card, fg_color="transparent")
        row2.pack(fill="x", padx=8, pady=(4, 8))
        self.now_var = tk.BooleanVar(value=True)
        self.now_cb = ctk.CTkCheckBox(
            row2, text="Use current date & time", variable=self.now_var,
            command=self._toggle_now
        )
        self.now_cb.pack(side="left")
        self._apply_now_datetime()

        # Action Row
        actions = ctk.CTkFrame(shell, fg_color="transparent")
        actions.grid(row=1, column=0, columnspan=4, sticky="ew", padx=12, pady=(6, 4))
        actions.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(actions, text="", text_color=("black", "#c8cdd6"))
        self.status_label.grid(row=0, column=0, sticky="w")

        btns = ctk.CTkFrame(actions, fg_color="transparent")
        btns.grid(row=0, column=1, sticky="e")
        self.filter_btn = ctk.CTkButton(btns, text="Filter", command=self._on_filter, height=36)
        self.filter_btn.pack(side="left", padx=(0, 8))
        self.demo_btn = ctk.CTkButton(btns, text="Load Data", command=self._load_demo, height=36)
        self.demo_btn.pack(side="left")



    def _card(self, parent, title, row, col):
        card = ctk.CTkFrame(parent, corner_radius=16, fg_color=("white", "#12151c"))
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        parent.grid_columnconfigure(col, weight=1)
        title_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        title_lbl.pack(anchor="w", padx=12, pady=(10, 2))
        sep = ctk.CTkProgressBar(card, mode="determinate")
        sep.set(1)   # thin accent divider
        sep.pack(fill="x", padx=12, pady=(0, 6))
        return card
    
  
        
    # magnitude helper
    def _update_mag_label(self, *_):
        value = float(self.max_mag_var.get())
        self.mag_label.configure(text=f"{value}")

    # object type helpers
    def _toggle_select_all(self):
        state = self.select_all_var.get()
        for var in self.type_vars.values():
            var.set(state)
    def _toggle_select_noncluster(self):
        state = self.select_non_cluster.get()
        for var in self.type_vars.items():
            if var[0] in non_cluster_types:
                var[1].set(state)

    def _sync_select_all_state(self):
        # Keep the "Select All" box in sync if user toggles individual boxes
        all_checked = all(var.get() for var in self.type_vars.values())
        none_checked = not any(var.get() for var in self.type_vars.values())
        # If none or all selected, reflect exactly; otherwise leave as unchecked
        self.select_all_var.set(all_checked and not none_checked)

    # Date/time helpers
    def _apply_now_datetime(self):
        now = datetime.datetime.now()
        self.dt_text_var.set(f"{now.month:02d} {now.day:02d} {now.year:04d} {now.hour:02d} {now.minute:02d}")
        self.dt_entry.configure(state="disabled")

    def _toggle_now(self):
        if self.now_var.get():
            self._apply_now_datetime()
        else:
            self.dt_entry.configure(state="normal")

    def _get_selected_datetime(self):
        """
        Parse 'DD MM YYYY HH MM' from self.dt_text_var.
        Returns (datetime|None, error_msg|'').
        """
        raw = (self.dt_text_var.get() or "").strip()
        parts = raw.replace(",", " ").replace("/", " ").replace("-", " ").split()
        if len(parts) != 5:
            return None, "Use format: DD MM YYYY HH MM (e.g., 09 11 2025 21 30)."
        try:
            m, d, y, h, mi = map(int, parts)
        except ValueError:
            return None, "All date/time parts must be integers."
        if not (1 <= m <= 12):   return None, "Month must be 01–12."
        if not (1 <= d <= 31):   return None, "Day must be 01–31."
        if not (0 <= h <= 23):   return None, "Hour must be 00–23."
        if not (0 <= mi <= 59):  return None, "Minute must be 00–59."
        try:
            return datetime.datetime(y, m, d, h, mi), ""
        except ValueError as e:
            return None, f"Invalid date: {e}"  
        
    # filter
    def _on_filter(self):
        # Determine datetime (now vs user)
        if self.now_var.get():
            dt = datetime.datetime.now()
            dt_label = dt.strftime("%Y-%m-%d %H:%M (now)")
        else:
            dt, err = self._get_selected_datetime()
            if err:
                self.status_label.configure(text=f"⚠ {err}")
                return
            dt_label = dt.strftime("%Y-%m-%d %H:%M")
        t = dt.astimezone(timezone('UTC'))
        UT_time = t.hour + t.minute/60
        # equation via the US naval observatory
        julian_date = 367*t.year - np.trunc(7*(t.year + np.trunc((t.month + 9)/12))/4) 
        julian_date = julian_date + np.trunc(275*t.month / 9) + t.day + 1721013.5 
        julian_date = julian_date + UT_time/24 - 0.5*np.sign(100*t.year + t.month - 190002.5) + 0.5
        # update stellarium with inputted date in JD
        requests.post(f"http://localhost:8090/api/main/time?time={julian_date}")
        # if t.hour < 5:
        #     # if it's early morning in UTC, the hour is high since the start of last day 
        #     self.s_after = int((t.hour + 24) - 5) * 3600 + int(t.minute) * 60
        # else:
        #     # otherwise it's on the same day as CST
        self.s_after = int(dt.hour) * 3600 + int(dt.minute) * 60
        # back to CST for the seconds after the start of day
        now = str(datetime.datetime.now()) # for later when writing to csv
        current_date, current_time = now.split(' ')
        current_time_split = current_time.split(':')

        hemi = self.hemisphere_var.get()
        size_min = self.size_min_var.get()
        size_max = self.size_max_var.get()
        max_mag = self.max_mag_var.get()
        selected_types = [k for k, v in self.type_vars.items() if v.get()] or ["Any"]

        msg = f"Hemisphere: {hemi} | Size: {size_min:.1f}–{size_max:.1f}' | Maximum {max_mag} Magnitude |\n Types: {', '.join(selected_types)} |\n When: {dt_label}"
        self.status_label.configure(text=msg)

        df = pd.read_csv('../data/processed/object_data_accurate.csv')
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
        self.df = df

        self.df = self.filter_objects_start()
        


    def filter_objects_start(self):
        df = self.df
        s_after = self.s_after
        hemisphere = self.hemisphere_var.get()
        size_min = self.size_min_var.get()
        size_max = self.size_max_var.get()
        max_mag = self.max_mag_var.get()
        selected_types = [k for k, v in self.type_vars.items() if v.get()] or ["Any"]
        size_range = (size_min, size_max)

        northern_constellations = ["Ursa Major", "Ursa Minor", "Draco", "Cassiopeia", "Cepheus", "Camelopardalis", "Perseus", "Auriga", "Gemini", "Cancer", "Leo", "Lynx", "Boötes", "Hercules", "Lyra", "Cygnus", "Aquila", "Delphinus", "Pegasus", "Andromeda", "Triangulum", "Aries", "Taurus", "Orion", "Eridanus", "Cetus", "Fornax", "Sculptor", "Auriga", "Gemini", "Canis Major", "Canis Minor", "Monoceros", "Lepus", "Columba", "Puppis", "Vela", "Carina", "Pyxis", "Hydra", "Sextans", "Crater", "Corvus", "Leo Minor", "Coma Berenices", "Canes Venatici", "Virgo", "Libra", "Scorpius", "Ophiuchus", "Serpens", "Sagittarius", "Corona Borealis", "Hercules", "Draco", "Aquarius", "Capricornus", "Pisces", "Cepheus", "Cassiopeia", "Andromeda", "Lacerta", "Vulpecula", "Sagitta", "Cygnus", "Cepheus", "Pegasus", "Equuleus", "Delphinus", "Vulpecula", "Lyra", "Aquila", "Serpens", "Ophiuchus", "Scutum", "Sagittarius", "Corona Australis", "Telescopium", "Indus", "Microscopium", "Piscis Austrinus", "Grus", "Phoenix", "Tucana", "Pavo", "Octans", "Apus", "Mensa", "Chamaeleon", "Musca", "Volans", "Carina", "Circinus", "Crux", "Centaurus", "Lupus", "Ara", "Scorpius", "Norma", "Triangulum Australe", "Aries", "Taurus", "Gemini", "Cancer", "Canis Minor", "Lepus", "Monoceros", "Orion", "Gemini", "Canis Major", "Canis Minor", "Puppis", "Hydra", "Sextans", "Crater", "Corvus", "Crux", "Carina", "Vela", "Antlia", "Pyxis", "Pictor", "Dorado", "Reticulum", "Horologium", "Caelum", "Mensa"] # fill in with all constellations that are visible in north
        southern_constellations = ["Crux", "Carina", "Vela", "Centaurus", "Lupus", "Ara", "Scorpius", "Norma", "Triangulum Australe", "Aries", "Taurus", "Gemini", "Cancer", "Canis Minor", "Lepus", "Monoceros", "Orion", "Hydra", "Sextans", "Crater", "Corvus", "Virgo", "Libra", "Scorpius", "Ophiuchus", "Sagittarius", "Corona Australis", "Telescopium", "Indus", "Microscopium", "Piscis Austrinus", "Grus", "Phoenix", "Tucana", "Pavo", "Octans", "Apus", "Mensa", "Chamaeleon", "Musca", "Volans", "Carina", "Circinus", "Crux", "Centaurus", "Lupus", "Ara", "Scorpius", "Norma", "Triangulum Australe", "Aries", "Taurus", "Gemini", "Cancer", "Canis Minor", "Lepus", "Monoceros", "Orion", "Pictor", "Dorado", "Reticulum", "Horologium", "Caelum", "Mensa"] # fill in with constellations that are visible in south
        if hemisphere == 'N':
            valid_constellations = northern_constellations
        else:
            valid_constellations = southern_constellations
        df_SS = df.tail(8) # last 8 are the planets + moon. These would get filtered out by constellation but we want to keep for now
        df = df.drop(df_SS.index) # remove manually to be later readded

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
        df = df[df.Type.isin(selected_types)]
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
        
        # # present results
        # df_z_scaled = df.copy()
        # df_z_scaled['Magnitude_Score'] = (df_z_scaled['Magnitude'] - df_z_scaled['Magnitude'].mean()) / df_z_scaled['Magnitude'].std()
        # df_z_scaled['Size_Score'] = (df_z_scaled['Size'] - df_z_scaled['Size'].mean()) / df_z_scaled['Size'].std() 
        # sorted_results = df.loc[(0.6*df_z_scaled['Magnitude_Score'] + 0.4 * df_z_scaled['Size_Score']).sort_values().index] # currently on 60% 40% weighting
        # num_to_display = int(input(f"Number of objects to display out of {len(sorted_results)}: "))
        # print("Displaying select columns for the ranked objects weighted 60% for Magnitude and 40% for Size")
        # print(f"Showing {num_to_display}/{len(sorted_results)} rows\n")
        # showing = sorted_results[["ObjectNum", "Name", "Type", "Constellation", "Magnitude", "Size", "Hours_Until_Set"]].head(num_to_display)
        # #print(tabulate(showing, headers=showing.columns, tablefmt='grid', showindex='never'))

        # calculate time until object sets
        diffs = []
        print(s_after)
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

        # def replace(row):
        #     if row['RAHour'] == '---':
        #         return np.nan
        #     return df['RAHour'].astype(str) + 'h' + df['RAMinute'].astype(str) + 'm'
        #df['RA'] = df.apply(replace, axis=0)
       # df['RA'] = np.where(df['RAHour'] != '---', df['RAHour'].astype(str) + 'h' + df['RAMinute'].astype(str) + 'm', '---')
        #df['Dec'] = np.where(df['RAHour'] != '---', df['DecSign'].astype(str) + (df['DecDeg'].astype(float) + (df['DecDeg'].astype(float) / 60)).astype(str) + '°', '---')
        return df

    def _build_table(self):
        wrapper = ctk.CTkFrame(self, corner_radius=18, fg_color=("gray95", "#0f1115"))
        wrapper.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)
   
        # Treeview inside a CTkFrame (with scrollbars)
        self.table_frame = ctk.CTkFrame(wrapper, fg_color=("white", "#12151c"))
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        #print(self.df.columns)
        columns = ("number","name","type","constellation",'mag',"angsize","hrs")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=14)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Headings
        self.tree.heading("number", text="Number", anchor='w')
        self.tree.heading("name", text="Name", anchor='w')
        self.tree.heading("type", text="Type", anchor='w')
        self.tree.heading("constellation", text="Constellation", anchor='w')
        self.tree.heading("mag", text="Magnitude", anchor='w')
      #  self.tree.heading("ra", text="RA")
       # self.tree.heading("dec", text="Dec")
        self.tree.heading("angsize", text="Angular Size (')", anchor='w')
        self.tree.heading("hrs", text="Hours to Set", anchor='w')

        # # Column widths (responsive-ish defaults)
        self.tree.column("number", width=30, anchor="w")
        self.tree.column("name", width=60, anchor="w")
        self.tree.column("type", width=60, anchor="w")
        self.tree.column("constellation", width=80, anchor="w")
        self.tree.column("mag", width=60, anchor='w')
       # self.tree.column("ra", width=70, anchor="e")
       # self.tree.column("dec", width=90, anchor="e")
        self.tree.column("angsize", width=60, anchor="w")
        self.tree.column("hrs", width=60, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def _style_treeview_dark(self):
        # Style ttk Treeview to match customtkinter dark theme
        style = ttk.Style(self)
        try:
            # On some platforms, "clam" looks nicer for custom colors
            style.theme_use("clam")
        except tk.TclError:
            pass

        bg = "#12151c"
        alt_bg = "#151a22"
        fg = "#e6e9ef"
        sel_bg = "#2b6cb0"
        sel_fg = "#ffffff"
        hdr_bg = "#0d1117"
        hdr_fg = "#cdd9e5"
        grid_color = "#202632"

        style.configure("Treeview",
                        background=bg,
                        fieldbackground=bg,
                        foreground=fg,
                        rowheight=28,
                        borderwidth=0)
        style.map("Treeview",
                  background=[("selected", sel_bg)],
                  foreground=[("selected", sel_fg)])
        style.configure("Treeview.Heading",
                        background=hdr_bg,
                        foreground=hdr_fg,
                        relief="flat")
        style.map("Treeview.Heading",
                  relief=[("active", "flat"), ("pressed", "flat")])
        style.layout("Treeview", [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])
        #Add subtle grid lines using tag styles
        self.tree.tag_configure("odd", background=alt_bg)
        self.tree.tag_configure("even", background=bg)
       

    def _load_demo(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        df_disp = self.df[["ObjectNum","Name","Type","Constellation",'Magnitude',"Size","Hours_Until_Set"]]
        df_z_scaled = df_disp.copy()
        df_z_scaled['Magnitude_Score'] = (df_z_scaled['Magnitude'] - df_z_scaled['Magnitude'].mean()) / df_z_scaled['Magnitude'].std()
        df_z_scaled['Size_Score'] = (df_z_scaled['Size'] - df_z_scaled['Size'].mean()) / df_z_scaled['Size'].std() 
        df_disp = df_disp.loc[(0.6*df_z_scaled['Magnitude_Score'] + 0.4 * df_z_scaled['Size_Score']).sort_values().index] # currently on 60% 40% weighting
        for idx, row in df_disp.iterrows():
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=list(row), tags=(tag,))

        self.status_label.configure(text=f"Loaded {df_disp.shape[0]} objects")


if __name__ == "__main__":
    app = DSOsortApp()
    app.mainloop()

