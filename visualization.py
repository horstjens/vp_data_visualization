import os.path
#import csv
import random
import colorsys
# non-standard-lib
import pandas as pd  # install with pip install pandas
import vpython as vp  # install with pip install vpython
#import sys
import os
import signal

VERSION = "0.34.f"

"""
generators (circles in diagram)
        >angle (for windmills) (-180° to 180°)
        >power 
nodes or busbars(small networks)
       get power from generators. send power to other networks. 
       recive power from other networks (negative numbers).
       send power to consumers (loads)
       > volt


cables connect nodes with each powers 
       > power from/to

loads:
      > p value

loading = % of MVA -> its for color coding the cables (* 100)

# MVA calculation:
% loading = sqrt (P^2 + Q^2) / MVArating
P and Q are the active and reactive flow in the circuit 
Q = zero
P is power from csv table (power of generator, 

active power ... P
reactive power ... Q

POWER CKT ... is power from Cable  (use only the bigger one)
Power (without CKT) ... power from Generator

"""




class Data:
    """Data contains variables taken from the excel/csv file"""
    # create a pandas dataframe from csv
    df = pd.read_csv("simulation_data_uae.csv")
    # geo = pd.read_csv("clean_geodata.csv")
    df_locations = pd.read_csv("uae_locations.csv")

    col_names = list(df.columns)

    #nodes = {}  # node_number: ( latitude, longitude, generator_number, is_load )
    nodes = {}  # node_number: (lat, long, is_generator, is_load, is_storage)
    node_geo = {}
    node_names = {} # node_number: node_name
    node_names2 = {} # node_name: node_number
    #node_colors = {} # (node_numbeR (from), node_number (to)  : color (for diagram legend)
    loads = [] # node_number
    storages = [] # storage_number
    generators = [] # node_number
    cables = []
    cables_dict = {}


    node_numbers = df_locations["number"]
    for node_number in node_numbers:
        line_number = node_number - 1
        node_names[node_number] = df_locations.iloc[line_number]["name"]
        node_names2[node_names[node_number]] = node_number
        # get latitude, longitude
        lat = df_locations.iloc[line_number]["latitude"]
        lon = df_locations.iloc[line_number]["longitude"]
        node_geo[node_number]= (lat,lon)
        if df_locations.iloc[line_number]["generator"] == "Yes":
            generators.append(node_number)
        if df_locations.iloc[line_number]["load"] == "Yes":
            loads.append(node_number)
        if df_locations.iloc[line_number]["storage"]== "Yes":
            storages.append(node_number)
        for target_number in node_numbers:
            if not pd.isna(df_locations.iloc[line_number][f"to_{target_number}"]):
                cables.append((node_number, target_number))
                if node_number not in cables_dict:
                    cables_dict[node_number] = [target_number]
                else:
                    cables_dict[node_number].append(target_number)
    print("-----------geo:----------------")
    for k, v in node_geo.items():
        print(k,":",v[0],v[1])
    print("--------------------------------")
    # take some interesting columns (called 'series' in pandas)
    print("cables:", cables_dict)

    time_min = df["time"].min()
    time_max = df["time"].max()

    frequency_min = df["frequency"].min()
    frequency_max = df["frequency"].max()

    nodes_min = None
    nodes_max = None

    for col_name in [name for name in col_names if name.startswith("VOLT_")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        nodes_min = mi if nodes_min is None else min(mi, nodes_min)
        nodes_max = ma if nodes_max is None else max(ma, nodes_max)

    storage_loading_min = None
    storage_loading_max = None
    for col_name in [name for name in col_names if name.startswith("storage_loading")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        storage_loading_min = mi if storage_loading_min is None else min(mi, storage_loading_min)
        storage_loading_max = ma if storage_loading_max is None else max(ma, storage_loading_max)

    storage_power_min = None
    storage_power_max = None
    for col_name in [name for name in col_names if name.startswith("storage_power")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        storage_power_min = mi if storage_power_min is None else min(mi, storage_power_min)
        storage_power_max = ma if storage_power_max is None else max(ma, storage_power_max)

    storage_state_min = None
    storage_state_max = None
    for col_name in [name for name in col_names if name.startswith("storage_state")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        storage_state_min = mi if storage_state_min is None else min(mi, storage_state_min)
        storage_state_max = ma if storage_state_max is None else max(ma, storage_state_max)

    loads_min = None
    loads_max = None

    for col_name in [name for name in col_names if name.startswith("load_power")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        loads_min = mi if loads_min is None else min(mi, loads_min)
        loads_max = ma if loads_max is None else max(ma, loads_max)

    cables_loading_min = None
    cables_loading_max = None

    for col_name in [name for name in col_names if name.startswith("cable_loading")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        cables_loading_min = mi if cables_loading_min is None else min(mi, cables_loading_min)
        cables_loading_max = ma if cables_loading_max is None else max(ma, cables_loading_max)

    cables_loss_min = None
    cables_loss_max = None

    for col_name in [name for name in col_names if name.startswith("cable_loss")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        cables_loss_min = mi if cables_loss_min is None else min(mi, cables_loss_min)
        cables_loss_max = ma if cables_loss_max is None else max(ma, cables_loss_max)

    cables_power_min = None
    cables_power_max = None

    for col_name in [name for name in col_names if name.startswith("cable_power")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        cables_power_min = mi if cables_power_min is None else min(mi, cables_power_min)
        cables_power_max = ma if cables_power_max is None else max(ma, cables_power_max)

    generators_power_min = None
    generators_power_max = None

    for col_name in [name for name in col_names if name.startswith("generator_power")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        generators_power_min = mi if generators_power_min is None else min(mi, generators_power_min)
        generators_power_max = ma if generators_power_max is None else max(ma, generators_power_max)

    generators_angle_min = None
    generators_angle_max = None
    for col_name in [name for name in col_names if name.startswith("generator_angle")]:
        # print("angle:",col_name)
        mi = df[col_name].min()
        ma = df[col_name].max()
        # print(mi,ma)
        generators_angle_min = mi if generators_angle_min is None else min(mi, generators_angle_min)
        generators_angle_max = ma if generators_angle_max is None else max(ma, generators_angle_max)
    # print("Generators angle min-max:", generators_angle_min, generators_angle_max)
    generators_loading_min = None
    generators_loading_max = None

    for col_name in [name for name in col_names if name.startswith("generator_loading")]:
        mi = df[col_name].min()
        ma = df[col_name].max()
        generators_loading_min = mi if generators_loading_min is None else min(mi, generators_loading_min)
        generators_loading_max = ma if generators_loading_max is None else max(ma, generators_loading_max)

    power_max = max(loads_max, generators_power_max, cables_power_max)
    time_col_name = "time"
    # print(generators_power_max, generators_power_min)
    print("Data calculation finished")
    print("cables power min - max:", cables_power_min, cables_power_max)
    print("generators power min - max:", generators_power_min, generators_power_max)
    print("loads power min - max:", loads_min, loads_max)
    print("storage power min - max:", storage_power_min, storage_power_max )


class Sim:
    running = True # mainloop
    axis_x = None
    axis_y = None
    axis_z = None
    flying_while_paused = False  # arrows fly also in pause mode
    test_arrow = None
    canvas_width = 1200 # 3d canvas
    canvas_height = 900 # 3d canvas
    dia_width = 400 #250     # for the 12 little diagrams on the right side
    dia_height = 200 #125    # for the 12 little diagrams on the right side
    mode = "arrange"
    camera_height = 0.25
    camera_range = 1.75
    camera_pitch = -90
    shortest_subcable = None
    legend = {} # nodenumber node_shorstname (from-to) : color-vector
    legend_nodes = {} #node_number : color_vector
    legend_cables = {} # (from,to) : color_vector
    dia_tick_color = vp.color.black
    #legend = create_color_legend()  # dictionary

    decimals_node = 1
    decimals_storage = 1
    decimals_load = 1
    decimals_generator = 1
    decimals_cable = 1
    label_storage = "p" # or "loading" TODO state ??
    label_load = "p" # or "loading"
    label_generator = "p" # or "angle" or "p+angle" or "loading"
    label_cable = "p" # "loading" or "p+loading"


    # minmax, lat: [41.06477, 44.00462]   -> 41,45
    # minmax, lon: [-73.79277, -69.66182] -> -74, -69

    # box bounded by 22°32’26.45”N, 51°28’48.53”E & 26°22’22.03”N, 56°34’23.91”E
    # minmax, lat: 22, 27
    # minmax lon: 51, 57
    mapname1 = os.path.join("assets", "map_uae4.jpg")
    mapname2 = os.path.join("assets", "map_uae5.jpg")
    pietextures = []
    for p in range(0,101):
        pietextures.append(os.path.join("assets", f"pie_percent_{p:02}.png"))
    #bounding_box = (-74, 41, -69, 45)
    #bounding_box = (51,22.5,57,26.5)
    # uae geo 2:
    # min (lat,lon):  23.3691	    46.594261   -> 23,   46
    # max (lat, lon): 25.145999	56.376785   -> 27,   57
    bounding_box = (51, 23, 57,26)
    x1, z1, x2, z2 = bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]
    middle = (x1 + abs(x1 - x2) / 2, z1 + abs(z1 - z2) / 2)
    center = vp.vector(middle[0], 0, middle[1])
    grid_max_x = abs(x1 - x2)
    grid_max_z = abs(z1 - z2)

    # glider_number = 1
    selected_object = None
    animation_running = False
    dragging = False


    # main 3d view
    scene = vp.canvas(title=f'simulation version {VERSION}',
                      # caption="coordinates: ",
                      width=canvas_width, height=canvas_height,
                      center=center,
                      background=vp.color.gray(0.8),
                      align="left",  # caption is to the right?
                      )

    # wheels
    scene_dia_needle_frequency = vp.canvas(
                       #title="network frequency",
                       #width=dia_width,
                       #height=canvas_height,
                       width=dia_height * 1.25,
                       height=dia_height,
                       center=vp.vector(0, 0, 0),
                       background=vp.color.gray(0.99),
                       #align="right",
                       align="left"
                       )

    scene_dia_needle_angle = vp.canvas(
                       #title="generator angle",
                       #width=dia_width,
                       #height=canvas_height,
                       width=dia_height * 1.25,
                       height=dia_height,
                       center=vp.vector(0, 0, 0),
                       background=vp.color.gray(0.99),
                       #align="right",
                       align="left"
                       )

    # net frequency

    graph_dia1 = vp.graph(width = dia_width,
                          height=dia_height,
                          background=vp.color.gray(0.9),
                          title="network frequency",
                          xtitle="time (s)",
                          ytitle="Hz",
                          align="left",
                          fast=False,
                          )


    graph_dia2 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.85),
        title= "Nodes Voltage",
        xtitle="time (s)",
        ytitle= "V",
        align="left",
        fast=False,
    )

    graph_dia3 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.8),
        title="Load Power",
        xtitle="time (s)",
        ytitle="MW",
        align="left",
        fast=False,
    )


    graph_dia4 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.75),
        title="Generator angle",
        xtitle="time (s)",
        ytitle="grad",
        align="left",
        fast=False,
    )


    graph_dia5 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.75),
        title="Generator Power",
        xtitle="time (s)",
        ytitle="MW",
        align="left",
        fast=False,
    )


    graph_dia6 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.65),
        title="Generator Loading",
        xtitle="time (s)",
        ytitle="%",
        align="left",
        fast=False,
    )

    graph_dia7 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.6),
        title="Storage Power",
        xtitle="time (s)",
        ytitle="MW",
        align="left",
        fast=False,
    )


    graph_dia8 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.55),
        title="Cable Loading",
        xtitle="time (s)",
        ytitle="%",
        align="left",
        fast=False,
    )


    graph_dia9 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.5),
        title="Cable Power",
        xtitle="time (s)",
        ytitle="MW",
        align="left",
        fast=False,
    )


    graph_dia10 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.45),
        title="Storage Loading",
        xtitle="time (s)",
        ytitle="%",
        align="left",
        fast=False,
    )

    graph_dia11 = vp.graph(
        width=dia_width,
        height=dia_height,
        background=vp.color.gray(0.4),
        title="Storage State",
        xtitle="time (s)",
        ytitle="?",
        align="left",
        fast=False,
    )


    scene3 = vp.canvas(#title="orange message area",
                      width=canvas_width+dia_width * 2,
                      height=20,
                      #center=center,
                      background = vp.color.orange)

    needle_frequency = None # for network frequency
    needles = {}            # for generator angles

    number_of_sub_cables = 2  # should be an even number, because sub-nodes = sub_cables -1. and we need a "middle" subnode
    fps = 60
    dt = 1 / fps
    i = 1  # line in data sheet
    old_i = None
    gui = {}  # widgets for gui
    colordict = {"crit_low": vp.vector(0, 0, 1),  # dark ,
                 "too_low": vp.vector(0, 0.5, 1),  # gray,
                 "low": vp.vector(0, 1, 1),  # cyan
                 "good_low": vp.vector(0, 1, 0.5),  # light green
                 "good_high": vp.vector(0, 1, 0),  # green
                 "high": vp.vector(0.5, 1, 0),  # green-yellow
                 "too_high": vp.vector(1, 1, 0),  # yellow
                 "crit_high": vp.vector(1, 0, 0),  # red
                 }
    colors = {"nodes": vp.color.blue,
              "generators": vp.color.yellow,
              "loads": vp.color.red,
              "storages": vp.color.cyan,
              "cables": vp.color.orange, # vp.color.gray(0.5),
              # "mini_arrow": vp.color.purple,
              # "flyers1": vp.color.magenta,
              # "flyers2": vp.color.purple,
              "disc": vp.color.gray(0.75),
              "grid": vp.color.black,
              "ground": vp.color.green,
              "pointer0": vp.color.orange,
              "pointer1": vp.color.red,
              "generator_lines": vp.color.gray(0.25),
              "load_lines": vp.color.gray(0.25),
              "storage_lines": vp.color.cyan,
              "losses": vp.color.red,
              "middles": vp.color.gray(0.75)
              }
    factor = {"generators_h": 0.001,
              "generators_r": 0.0,
              "nodes_h": 0.1,
              "nodes_r": 0.0,
              "loads_h": 0.001,
              "loads_r": 0.0,
              "cables_h": 0.0,
              "cables_r": 0.0,
              "arrows": 0.01,
              "arrows_x": 0.01,
              "arrows_z": 0.01,
              "losses": 1.0,
              "pointer1": 1.5,  # pointer1 to display angle of generator. multiplying base["generator_r"]
              "pointer2": 2.0,  # pointer2 to display angle of generator. multiplying base["generator_r"]
              "storages_h": 0.001,
              "storages_r": 0.0,
              }
    base = {"generators_h": 0.0,
            "generators_r": 0.01,
            "nodes_h": 0.0,
            "nodes_r": 0.01,
            "loads_h": 0.0,
            "loads_r": 0.01,
            "cables_h": 0.03,
            "cables_r": 0.005,
            "middles_h": 0.0,
            "middles_r": 0.005,
            "storages_h": 0.01,
            "storages_r": 0.01,
            "flying_arrows_length": 0.01,  # length of a flying arrow in world coordinate units
            "flying_arrows_distance": 4,  # distance in arrow_lengths between 2 arrows
            }

    visible = {"generators": True,
               "nodes": True,
               "cables": True,
               "loads": True,
               "middles": True,
               "storages":True,
               # "flyers": False,
               }
    dynamic_colors = {"generators": False,
                      "nodes": False,
                      "cables": False,
                      "loads": False,
                      "middles": False,
                      "storages": False,
                      }
    # textures = {  # "generators": os.path.join("energy2.png"),
    #    # "nodes": os.path.join("energy1.png"),
    #    #"map": os.path.join("assets", "map002.png"),
    # }
    animation_duration = 2000  # seconds
    frame_duration = animation_duration / len(Data.df)
    # mini_arrow_length = 2
    # mini_arrow_base1 = 1
    # mini_arrow_base2 = 1
    # mini_arrow_distance = 20
    # mini_arrow_speed = 8

    # cursor = vp.cylinder(radius = 1, color=vp.color.white, pos = vp.vector(0,0,0), axis=vp.vector(0,0.2,0),
    # opacity=0.5, pickable=False)
    sloped_cables = False  # cables are sloped depending on the height of the connected node cylinders
    tubes_radius_factor = 1.0
    tubes_radius_delta = 0.0
    tubes_opacity = 0.15
    sub_cable_pointlist = {}  # {(i,j):[p,p,p...],}
    sub_cable_lengthlist = {}  # {(i,j):[l,l,l...],}
    # --- vpython objects -----
    tubes_node = {}  # {(i,j):cylinder,}
    tubes_load = {}  # {node_number:cylinder,}
    tubes_generator = {}  # {generator_number:cylinder,}
    tubes_storage = {} # {storage_number:cylinder}
    grid = []
    nodes = {}
    cables = {}  # direct connections (gold), only visible when in arrange mode
    cables_middle = {}  # point exactly between 2 nodes. to display pie chart and label. can be moved by mouse! (attached to sub-node?)
    cablepower = {}  # (i,j):power
    loads = {}  # consumer of energy
    storages = {}
    storages_glass = {}
    generators = {}
    generators_glass = {}
    pointer0 = {}  # to display angle at each generator
    pointer1 = {}  # to display angle at each generator
    discs = {}  # for generators
    pie_charts = {} # for cables (middle)
    generator_lines = {}  # between node and generator
    load_lines = {}  # between node and load
    storage_lines = {} # between node and storage
    sub_nodes = {}  # pink cylinders, draggable by mouse, only visible when in arrange mode
    sub_cables = {}  # pink curve for cable, connecting the sub_nodes. will be transformed into black shadows at simulation start
    # shadows = {}   # black shadows on y position 0, a clone from the sub-cable curve
    labels = {}  # 2d text label (detailed)
    letters = {}  # 2d text label (just the name/number)
    # mini_arrows = {}  # flying along the path, only visible when in simulation mode
    # mini_shadows = {}  # shadow for each glider
    mini_losses = {}  # stalagtites below each glider
    # arrows indication flow in cables
    arrows_ij = {}  # arrows along sub_nodes, pointing from lower node number to higher node number
    arrows_ji = {}  # arrows along sub_nodes, pointing from hight node number to lower node number
    arrows_number = 0
    arrows = {}  # (i,j)
    shadows = {}
    generator_arrows = {}
    load_arrows = {}
    arrows_speed = 0.02
    arrows_speed_min = 0.00
    arrows_speed_max = 0.25


class Shadowarrow(vp.arrow):
    """if flow is True:
            flying from A to B
            flying from previous_point to next_point
       if flow is False:
            flying from B to A
            flying from next_point to previous_point
    """

    def __init__(self, nodestring="AB", **kwargs):
        super().__init__(**kwargs)
        # print("black arrow created")
        if nodestring not in Sim.blackarrows:
            Sim.blackarrows[nodestring] = []
        Sim.blackarrows[nodestring].append(self)
        self.nodestring = nodestring
        self.flow = Sim.arrow_flow
        self.speed = Sim.arrow_speed
        self.color = vp.color.black
        self.shaftwidth = 0.03
        self.turning = False
        self.turn_direction = 1

        # get pos from nodestring and flow
        if self.flow:
            index = 0  # fly from A to B
            self.next_point = 1
            self.previous_point = 0
            self.axis = vp.norm(Sim.points[1] - Sim.points[0])
        else:
            index = -1  # fly from B to A
            self.next_point = -2
            self.previous_point = -1
            self.axis = vp.norm(Sim.points[-2] - Sim.points[-1])
        self.axis = vp.norm(self.axis) * Sim.arrow_length
        self.new_axis = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.fly_direction = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.pos = Sim.points[index] - self.axis

    def flip_direction(self):
        self.flow = Sim.arrow_flow
        # self.fly_direction *= -1
        # self.axis *= -1
        if self.flow:  # from A to B
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(
                    Sim.points[self.next_point] - Sim.points[self.previous_point]) * Sim.arrow_length
            elif self.previous_point is not None:
                self.new_axis = vp.norm(
                    Sim.points[self.previous_point] - Sim.points[self.previous_point - 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.yellow

        else:  # from B to A
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(
                    Sim.points[self.previous_point] - Sim.points[self.next_point]) * Sim.arrow_length
            elif self.next_point is not None:
                self.new_axis = vp.norm(
                    Sim.points[self.next_point] - Sim.points[self.next_point + 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.blue
        # --- both ---
        self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)
        self.axis = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

    def update(self):
        if self.flow != Sim.arrow_flow:
            self.flip_direction()
        self.pos += self.speed * Sim.dt * vp.norm(self.fly_direction)
        # magnitude of a vector is always positive
        if self.previous_point is not None:
            self.distance_from_previous_point = vp.mag(self.pos - Sim.points[self.previous_point])
        if self.next_point is not None:
            self.distance_from_next_point = vp.mag(self.pos - Sim.points[self.next_point])
        # except IndexError:
        #    print("IndexError", self.previous_point, self.next_point)
        #    if self.next_point == len(Sim.points):
        #        self.next_point -= 1
        # if self.axis != self.fly_direction:
        #    self.turing = True
        # else:
        #    self.turing = False
        diff_angle = vp.diff_angle(self.fly_direction, self.axis)
        # print("diff angle, abs", diff_angle, abs(diff_angle))
        if abs(vp.diff_angle(self.axis, self.new_axis)) > 0.05:
            self.turning = True
        else:
            self.axis = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)
            self.turning = False
        if self.turning:
            diff_angle_old = abs(vp.diff_angle(self.axis, self.new_axis))
            # print("diff_angle:", vp.degrees(diff_angle), self.previous_point, self.next_point)
            oldpos = self.pos
            self.rotate(origin=self.pos,
                        angle=vp.radians(Sim.arrow_turn_speed) * Sim.dt * self.turn_direction,
                        axis=vp.vector(0, 1, 0))
            self.pos = oldpos
            diff_angle_new = abs(vp.diff_angle(self.axis, self.new_axis))
            if diff_angle_new > diff_angle_old:
                self.turn_direction *= -1

        if self.flow:
            # flying from previous point to next point
            # if self.next_point < len(Sim.points):
            if self.next_point is not None and self.previous_point is not None:
                # not at end
                # if (self.distance_from_previous_point + vp.mag(self.fly_direction) / 2) > (
                #        Sim.distances[self.next_point] - Sim.distances[self.previous_point]):
                prev_to_tip = self.distance_from_previous_point + vp.mag(self.fly_direction) * 2
                prev_to_tail = self.distance_from_previous_point
                full_length = Sim.distances[self.next_point] - Sim.distances[self.previous_point]
                if prev_to_tail < full_length < prev_to_tip:
                    # try: # if self.next_point + 1 == len(Sim.points) -> IndexError
                    #    self.new_axis = vp.norm(
                    #        Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    #    pass # do not change new_axis
                    if (self.next_point + 1) < len(Sim.points):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif prev_to_tail > full_length:
                    self.pos = Sim.points[self.next_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.next_point + 1) < len(Sim.points):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    else:
                        # apparently arrow reached end of AB direction and is waiting to be recycled
                        self.new_axis = vp.norm(Sim.points[1] - Sim.points[0]) * Sim.arrow_length

                    self.previous_point += 1
                    self.next_point += 1

                    if self.next_point >= len(Sim.points):
                        self.next_point = None

                    # overshot = self.distance_from_previous_point + vp.mag(self.fly_direction) - (
                    #    Sim.distances[self.next_point] - Sim.distances[self.previous_point])
                    # self.pos = Sim.points[self.next_point]

            else:  # at end
                if self.distance_from_previous_point > vp.mag(self.axis) / 2:
                    # if self.distance_from_next_point < vp.mag
                    # self.visible = False
                    self.color = vp.color.red
                    # go to waiting
                    self.speed = 0
        elif not self.flow:
            # flying from next point to previous point
            # if self.previous_point >= 0:
            if self.previous_point is not None and self.next_point is not None:
                # not at end
                # print(self.next_point, self.previous_point)
                # if (self.distance_from_next_point + vp.mag(self.axis) / 2) > (
                #        Sim.distances[self.next_point] - Sim.distances[self.previous_point]):
                next_to_tip = self.distance_from_next_point + vp.mag(self.fly_direction) * 2
                next_to_tail = self.distance_from_next_point
                full_length = Sim.distances[self.next_point] - Sim.distances[self.previous_point]
                if next_to_tail < full_length < next_to_tip:
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.previous_point - 1] - Sim.points[self.previous_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif next_to_tail > full_length:
                    self.pos = Sim.points[self.previous_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.previous_point - 1] - Sim.points[self.previous_point]) * Sim.arrow_length
                    else:
                        # apparently reached first waypoint, in BA direction, prepare for recycling
                        self.new_axis = vp.norm(Sim.points[-2] - Sim.points[-1]) * Sim.arrow_length
                    self.previous_point -= 1
                    self.next_point -= 1

                    if self.previous_point < 0:
                        self.previous_point = None
            else:  # at end
                if self.distance_from_next_point > vp.mag(self.axis) / 2:
                    # self.visible = False
                    self.color = vp.color.red
                    # go to waiting
                    self.speed = 0




class FlyingArrowToLoad(vp.arrow):
    """flying from Node to attached Load"""

    def __init__(self, load_number, **kwargs):
        super().__init__(**kwargs)
        self.load_number = load_number
        self.number = Sim.arrows_number
        Sim.load_arrows[self.number] = self
        Sim.arrows_number += 1
        # self.curve = Sim.load_lines[load_number] # curve is laying on floor
        # self.node_number = Sim.generators[gen_number].node_number
        self.node_number = load_number
        self.node = Sim.nodes[self.node_number]
        self.load = Sim.loads[self.node_number]
        self.axis = vp.norm(Sim.loads[self.node_number].pos - Sim.nodes[self.node_number].pos) * Sim.base[
            "flying_arrows_length"]
        Sim.shadows[self.number] = vp.arrow(color=vp.color.gray(0.1), pos=vp.vector(self.pos.x, 0, self.pos.z),
                                            axis=vp.vector(self.axis.x, 0, self.axis.z))
        Sim.shadows[self.number].axis = self.axis
        #self.delta100 = Data.nodes_max - Data.nodes_min
        #self.delta100 = Data.power_max
        self.max_distance = vp.mag(self.load.pos - self.node.pos) - self.load.radius

    def update(self, dt):
        #try:
        #    #deltap = self.load.power - Data.loads_min
        #    deltap = self.load.power # - 0
        #except AttributeError:
        #    return
        try:
            speedpercent = self.load.power / Data.power_max
        except AttributeError:
            return
        speed = Sim.arrows_speed_min + speedpercent * (Sim.arrows_speed_max - Sim.arrows_speed_min)
        #print("speed (node->load)", speed, speedpercent)

        # always have the same y pos as the connected Node
        # new_pos = self.pos + vp.norm(self.axis) * Sim.arrows_speed * dt
        new_pos = self.pos + vp.norm(self.axis) * speed * dt
        pos0 = vp.vector(new_pos.x, 0, new_pos.z)
        # self.pos0 = vp.vector(self.pos.x,0, self.pos.z)
        overshoot = vp.mag(pos0-self.node.pos) + vp.mag(self.axis) - self.max_distance
        if overshoot > 0:
        #if vp.mag(pos0 - self.node.pos) > self.max_distance:
            new_pos = self.node.pos + vp.norm(self.axis) * overshoot
                        #vp.mag(pos0 - self.node.pos) - vp.mag(self.load.pos - self.node.pos))
            # self.axis = vp.norm(self.pos2 - self.pos) * Sim.base["flying_arrows_length"]
        # self.pos = vp.vector(new_pos.x, self.node.axis.y, new_pos.z)
        if Sim.sloped_cables:
            self.pos = vp.vector(new_pos.x, self.node.axis.y, new_pos.z)
        else:
            power = Data.df[f"load_power_{self.load_number}"][Sim.i]
            y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
            self.pos = vp.vector(new_pos.x, y, new_pos.z)
        # update shadow
        Sim.shadows[self.number].pos = vp.vector(new_pos.x, 0, new_pos.z)


class FlyingArrowFromGenerator(vp.arrow):
    """flying from Generator to attached Node"""

    def __init__(self, gen_number, **kwargs):
        super().__init__(**kwargs)
        self.gen_number = gen_number
        self.number = Sim.arrows_number
        Sim.generator_arrows[self.number] = self
        Sim.arrows_number += 1
        # self.curve = Sim.generator_lines[gen_number] # curve is laying on floor
        self.node_number = Sim.generators[gen_number].number
        self.node = Sim.nodes[self.node_number]
        self.generator = Sim.generators[self.gen_number]
        self.axis = vp.norm(Sim.nodes[self.node_number].pos - Sim.generators[self.gen_number].pos) * Sim.base[
            "flying_arrows_length"]
        Sim.shadows[self.number] = vp.arrow(color=vp.color.gray(0.1), pos=vp.vector(self.pos.x, 0, self.pos.z),
                                            axis=vp.vector(self.axis.x, 0, self.axis.z))
        Sim.shadows[self.number].axis = self.axis
        #self.delta100 = Data.generators_power_max - Data.generators_power_min
        self.max_distance = vp.mag(self.node.pos - self.generator.pos) - self.node.radius

    def update(self, dt):
        # always have the same y pos as the connected Node
        #try:
        #    deltap = self.generator.power - Data.generators_power_min
        #except:
        #    return
        #speedpercent = deltap / self.delta100
        #speed = Sim.arrows_speed_min + speedpercent * (Sim.arrows_speed_max - Sim.arrows_speed_min)
        try:
            speedpercent = self.generator.power / Data.power_max
        except AttributeError:
            return
        speed = Sim.arrows_speed_min + speedpercent * (Sim.arrows_speed_max - Sim.arrows_speed_min)

        # new_pos = self.pos + vp.norm(self.axis) * Sim.arrows_speed * dt
        new_pos = self.pos + vp.norm(self.axis) * speed * dt
        pos0 = vp.vector(new_pos.x, 0, new_pos.z)
        # self.pos0 = vp.vector(self.pos.x,0, self.pos.z)
        #if vp.mag(pos0 - self.generator.pos) > vp.mag(self.node.pos - self.generator.pos):
        #    new_pos = self.generator.pos + vp.norm(self.axis) * (
        #                vp.mag(pos0 - self.generator.pos) - vp.mag(self.node.pos - self.generator.pos))
            # self.axis = vp.norm(self.pos2 - self.pos) * Sim.base["flying_arrows_length"]
        overshoot = vp.mag(pos0 - self.generator.pos) + vp.mag(self.axis) - self.max_distance
        if overshoot > 0:
            # if vp.mag(pos0 - self.node.pos) > self.max_distance:
            new_pos = self.generator.pos + vp.norm(self.axis) * overshoot


        if Sim.sloped_cables:
            self.pos = vp.vector(new_pos.x, self.node.axis.y, new_pos.z)
        else:
            power = Data.df[f"generator_power_{self.gen_number}"][Sim.i]
            y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
            self.pos = vp.vector(new_pos.x, y, new_pos.z)
        # update shadow
        Sim.shadows[self.number].pos = vp.vector(new_pos.x, 0, new_pos.z)


class FlyingDisc(vp.cylinder):
    """disc-formed shadow of a flying ball,
    traveling on the groud between nodes, subnodes,
    generators, loads, storages etc.
    highest power value is maximum speed (100%)
    traveling speed is local power value in relation to the maximum speed
    boss can be cable, generator, storage, load
    """
    container = []
    distances = {} # {boss_string, [i_number,j_number]}


    def __init__(self, boss, power, **kwargs):
        self.boss = boss
        self.power = power
        super().__init__(**kwargs)
        # boss is actually the name of the df column, like 'storage_power_1'
        # power = Data.df[f"storage_power_{number}"][Sim.i]
        FlyingDisc.container.append(self)
        if self.boss.startswith("storage_power"):
            #print(self.boss, self.boss.split("_"))
            self.i = int(self.boss.split("_")[-1])
            self.j = int(self.boss.split("_")[-1]) # the same
            self.pointlist = [Sim.nodes[self.i].pos, Sim.storages[self.i].pos]
            self.length_list = [0, vp.mag(self.pointlist[0]-self.pointlist[1])]
            # start where ? depending if storage power is positive (start at node), fly_direction = 1 or negative (start at storage, fly_direction = -1
            #self.power = Data.df[f"storage_power_{self.i}"][Sim.i]
            #self.speed_percent =
            if self.power > 0:
                self.fly_direction = 1
                self.pos = self.pointlist[0]
                self.target = self.pointlist[1]
                if self.boss not in FlyingDisc.distances:
                    FlyingDisc.distances[self.boss] = [0, self.length_list[1]]
                else:
                    FlyingDisc.distances[self.boss][0] = 0
            else:
                self.fly_direction = -1
                self.pos = self.pointlist[-1]
                self.target = self.pointlist[0]
                if self.boss not in FlyingDisc.distances:
                    FlyingDisc.distances[self.boss] = [self.length_list[1], 0]
                else:
                    FlyingDisc.distances[self.boss][1] = 0
        self.radius = Sim.base["flying_arrows_length"]
        self.axis = vp.vector(0,0.001,0)
        self.color = vp.color.green
        self.opacity = 0.5
        self.speed = 0

    def update(self, power):
        if power == 0:
            self.color = vp.color.yellow
            return
        #else:
        self.color = vp.color.green
        # speed calculation
        speedpercent = abs(self.power / Data.power_max)
        print(speedpercent)
        speed = speedpercent * Sim.arrows_speed_max
        # new pow
        if self.power > 0:
            direction = vp.norm(self.pointlist[1] - self.pointlist[0])
        else:
            direction = vp.norm(self.pointlist[0] - self.pointlist[1])
        self.pos += direction * speed * Sim.dt
        #print("new pos:", self.pos)
        dist_i = vp.mag(self.pos - self.pointlist[0])
        dist_j = vp.mag(self.pos - self.pointlist[1])
        if dist_i < FlyingDisc.distances[self.boss][0]:
            FlyingDisc.distances[self.boss][0] = dist_i
        if dist_j < FlyingDisc.distances[self.boss][-1]:
            FlyingDisc.distances[self.boss][-1] = dist_j


class FlyingArrow(vp.arrow):
    def __init__(self, i, j, k, i2j, **kwargs):
        super().__init__(**kwargs)
        self.number = Sim.arrows_number
        Sim.arrows_number += 1
        self.i = i
        self.j = j
        self.k = k  # sub-cable point where arrow is starting from
        self.k2 = None  # sub-cable point where arrow is traveling to
        self.i2j = i2j  # bool # direction of power flow: True if power flows from node i toward node j. otherwise False
        # curve = Sim.sub_cables[(i,j)]
        # self.pointlist = [d["pos"] for d in curve.slice(0, curve.npoints)] # curve is lying on the floor
        self.pointlist = Sim.sub_cable_pointlist[(i, j)]
        # total_length = 0
        # self.length_list = []
        # for k, pos in enumerate(self.pointlist):
        #    if k == 0:
        #        self.length_list.append(0)
        #    else:
        #        total_length += vp.mag(self.pointlist[k]-self.pointlist[k-1])
        #        self.length_list.append(total_length)
        self.length_list = Sim.sub_cable_lengthlist[(i, j)]
        self.new_k2()
        self.pos2 = self.pointlist[self.k2]
        self.axis = vp.norm(self.pos2 - self.pos) * Sim.base["flying_arrows_length"]
        # append self to list, create if necessary
        if (self.i, self.j) not in Sim.arrows:
            Sim.arrows[(self.i, self.j)] = []  # empty list
        Sim.arrows[(self.i, self.j)].append(self)
        self.color = Sim.colors["cables"]
        # create shadow arrow
        Sim.shadows[self.number] = vp.arrow(color=vp.color.gray(0.1), pos=vp.vector(self.pos.x, 0, self.pos.z),
                                            axis=vp.vector(self.axis.x, 0, self.axis.z))
        #self.delta100 = Data.cables_power_max - Data.cables_power_min

    def new_k2(self):
        if self.i2j:
            self.k2 = self.k + 1
            if self.k2 == len(self.pointlist):
                self.pos = self.pointlist[0]
                self.k = 0
                self.k2 = 1
        else:
            self.k2 = self.k - 1
            if self.k2 < 0:
                self.pos = self.pointlist[-1]
                self.k = len(self.pointlist) - 1
                self.k2 = len(self.pointlist) - 2

    def flip_direction(self):
        self.k, self.k2 = self.k2, self.k
        self.i2j = not self.i2j
        self.pos2 = self.pointlist[self.k2]
        self.axis = vp.norm(self.pos2 - vp.vector(self.pos.x, 0, self.pos.z)) * Sim.base["flying_arrows_length"]
        # self.color = vp.color.green

    def calculate_sloped_y(self, full_ydiff):
        """full_ydiff is the y distance between the tops of the 2 connected nodes"""
        if self.i2j:
            #  coming from self.k, traveling to self.k2
            base_length = self.length_list[self.k]
            delta = vp.mag(vp.vector(self.pos.x, 0, self.pos.z) - self.pointlist[self.k])
            length = base_length + delta
            return length / self.length_list[-1] * full_ydiff
        else:
            base_length = self.length_list[self.k2]
            delta = vp.mag(vp.vector(self.pos.x, 0, self.pos.z) - self.pointlist[self.k2])
            length = base_length + delta
            return length / self.length_list[-1] * full_ydiff

    def update(self, dt):
        save_y = self.pos.y
        #try:
        #    deltap = Sim.cablepower[(self.i, self.j)] - Data.cables_power_min
        #except:
        #    return
        #speedpercent = deltap / self.delta100
        #speed = Sim.arrows_speed_min + speedpercent * (Sim.arrows_speed_max - Sim.arrows_speed_min)
        try:
            speedpercent = Sim.cablepower[(self.i, self.j)]  / Data.power_max
        except:
            # some error
            return
        speed = Sim.arrows_speed_min + speedpercent * (Sim.arrows_speed_max - Sim.arrows_speed_min)

        # new_pos = self.pos + vp.norm(self.axis) * Sim.arrows_speed * dt
        new_pos = self.pos + vp.norm(self.axis) * speed * dt
        self.pos = new_pos
        self.pos0 = vp.vector(new_pos.x, 0, new_pos.z)
        # print("newpos:",self.i,self.j, self.pos)
        # if middle of arrow is over pos2, rotate arrow and get new pos2
        # middle = self.pos + self.axis / 2
        # if vp.mag(middle - self.pointlist[self.k]) > vp.mag(self.pointlist[self.k2]-self.pointlist[self.k]):
        reached_end = False
        if all((self.i2j, self.k2 == (len(self.pointlist)-1))):
            radius = Sim.nodes[self.j].radius + Sim.base["flying_arrows_length"]
            reached_end = True
        elif all((not self.i2j, self.k2 == 0)):
            radius = Sim.nodes[self.i].radius + Sim.base["flying_arrows_length"]
            reached_end = True
        else:
            radius = Sim.base["flying_arrows_length"] /2
        overshoot = vp.mag(self.pos0 - self.pointlist[self.k]) - (vp.mag(self.pointlist[self.k2] - self.pointlist[self.k]) - radius)
        if overshoot > 0:
            if self.i2j:
                self.k += 1
            else:
                self.k -= 1
            self.new_k2()
            npos = self.pointlist[self.k]
            self.pos2 = self.pointlist[self.k2]
            axis_old = vp.vector(self.axis.x, self.axis.y, self.axis.z)
            self.axis = vp.norm(self.pos2 - npos) * Sim.base["flying_arrows_length"]

            if not reached_end:
                # reached end node
                self.pos = npos
                self.pos += vp.norm(self.axis) * overshoot
                self.pos += self.axis * -0.5  # FEHLER??
                #else:
                    # new point in straight line (middle point)
                #pass
            else:
                self.pos = npos
                self.pos += vp.norm(self.axis) * overshoot


        self.pos.y = save_y
        # update shadow
        Sim.shadows[self.number].pos = vp.vector(self.pos.x, 0, self.pos.z)
        Sim.shadows[self.number].axis = vp.vector(self.axis.x, 0, self.axis.z)


# helper functions for calculating loading value
# from https://stackoverflow.com/a/9701141
def get_colors(num_colors):
    """returns a list of colors as vp.vectors"""
    colors=[]
    i = 0
    while i <= 360:
        hue = i/360.
        lightness = (50 + random.random()*10)/100.
        saturation = (90 + random.random() * 10)/100.
        c =colorsys.hls_to_rgb(hue, lightness, saturation)
        colors.append(vp.vector(c[0], c[1], c[2]))
        i+= 360 / num_colors
    return colors


def col_name_angle(generator_number):
    return f"ANGL {generator_number}[{generator_number} 1.0000]1"


def col_name_power(generator_number):
    return f"POWR {generator_number}[{generator_number} 1.0000]1"


def col_name_node(node_number):
    # col_name for node 1: "VOLT 1 [1 1.0000]"
    return f"VOLT {node_number} [{node_number} 1.0000]"


def col_name_cable(from_number, to_number):
    return f"POWR {from_number} TO {to_number} CKT '1 '"


# ------- helper functions for Sim ----

def create_color_legend():
    # --------------- create node colors for legend -------
    # node_numbers is [number, number2,...]
    # everything except white (1,1,1)
    # in cables_dict is {source_node_number : [target_node_number, target_node_number ...] }
    # in cables is [(source,target), (source,target)....]
    # in node_names is {node_number:name}
    # node_colors = {}  # (node_numbeR (from), node_number (to)|None  : color (for diagram legend)

    # find out how many different colors are needed for legend.
    # each node needs a legend, each cable needs a legend
    # however, the first cable of a source node can share its color with the color of that node
    # also, nodes without cables may exist
    node_numbers = Data.df_locations["number"]
    number_of_nodes = len(node_numbers)
    # nodes without cable as source:
    nodes_without_cable = [] # without cable source
    cable_tuples = []
    for n1 in Data.node_numbers:
        for k, vlist in Data.cables_dict.items():
            vlist.sort()
            for v in vlist:
                if (k==n1) and (v > n1):
                    cable_tuples.append((k, v))
                if (v==n1) and (k > n1):
                    cable_tuples.append((v, k))
    cable_tuples.sort()
    #print("cable tuples:", cable_tuples)
    naked_nodes = []
    for nn in Data.node_numbers:
        found = False
        for n1,n2 in cable_tuples:
            if n1 == nn:
                found = True
                break
        if not found:
            naked_nodes.append(nn)
    #print("naked nodes:", naked_nodes)
    number_of_colors = len(cable_tuples) + len(naked_nodes)
    #delta = int(number_of_colors ** (1 / 3))
    colors = get_colors(number_of_colors)
    # headline
    Sim.legend[" # from  to "] = vp.vector(0,0,0) # black headline

    nn = min(node_numbers)
    #colors = [0, 0, 0]
    legend = {}
    i = 0
    while nn <= max(node_numbers):
        #colors = increase_color(colors, delta)
        if nn in naked_nodes:
            key = f"{nn:>2} {Data.node_names[nn]}     "
            #colors = increase_color(colors, delta)
            color = colors[i]
            i += 1
            Sim.legend_nodes[nn] = color
            Sim.legend[key] = color

        else:
            for k,v in cable_tuples:
                if k == nn:
                    #colors = increase_color(colors, delta)
                    color = colors[i]
                    i += 1
                    if k not in Sim.legend_nodes:
                        key = f"{nn:>2} {Data.node_names[nn]} {Data.node_names[v]}"
                        Sim.legend_nodes[nn] = color # vp.vector(colors[0], colors[1], colors[2])
                    else:
                        key = f"   {Data.node_names[nn]} {Data.node_names[v]}"
                    Sim.legend_cables[(k, v)] = color # vp.vector(colors[0], colors[1], colors[2])
                    Sim.legend[key] = color # vp.vector(colors[0], colors[1], colors[2])
        nn += 1
    # print
    for k,v in Sim.legend.items():
        print(k,v)



def increase_color(colors, delta):
    """helper function for class Data"""
    colors[2] += 1/delta
    if colors[2] > 1:
        colors[2] = 0
        colors[1] += 1/delta
        if colors[1] > 1:
            colors[1] = 0
            colors[0] += 1/delta
    return colors

def geo_to_local(lat):
    """vpythons z axis is looking south, therefore calculate latitude coordinate into vpythons z axis"""
    distance_to_center = lat - Sim.middle[1]
    return Sim.middle[1] - distance_to_center


# ------------ helper function for GUI ------------

def camera_to_topdown():
    # Sim.scene.camera.pos = vp.vector(0, 2, 0)
    # Sim.scene.forward = vp.vector(0.0, -1, 0)
    # Sim.scene.up = vp.vector(0, 0, -1)
    # Sim.scene.range = Sim.grid_max / 2
    # Sim.scene.autoscale = True
    # Sim.scene.autoscale = False
    ## Sim.scene.userzoom = False
    # Sim.scene.userspin = False
    # TODO: research why graphic (curve radius, mouse handling) is messed up when camera.pos is changed at the end of this function
    # Sim.scene.forward = vp.vector(0.0, -Sim.camera_height, 0) # makes horrible thick curves
    Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height, Sim.center.z)
    Sim.scene.forward = vp.vector(0.0, -1, 0)  # camera pos is moved
    # Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height , Sim.center.z) # horrible result
    Sim.scene.camera.pos.x = Sim.center.x  # ok

    Sim.scene.up = vp.vector(0, 0, -1)

    ###Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height, geo_to_local(Sim.center.z))
    # Sim.scene.range = Sim.grid_max_x / 2
    Sim.scene.autoscale = True

    # Sim.scene.userzoom = False
    Sim.scene.userspin = False
    # Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height , geo_to_local(Sim.center.z))
    # Sim.scene.camera.pos.x = Sim.center.x
    Sim.scene.center = Sim.center
    Sim.scene.autoscale = False
    Sim.scene.range = Sim.camera_range

    # print("Sim.scene.center:", Sim.scene.center) # TODO: into gui (lable)
    # Sim.scene.camera.pos.z = Sim.center.z


def widget_func_dia_width(b):
    #winput
    Sim.dia_width = int(b.number)
    Sim.graph_dia1.width = int(b.number)

def widget_func_dia2(b):
    print("nodes entry:", b.text)

def widget_func_restart(b):
    """stop and rewind"""
    # print("start was pressed", b.text)
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    Sim.i = 0
    Sim.gui["frameslider"].value = 0
    Sim.gui["label_frame"].text = f"{Sim.i}/{len(Data.df)} time: {Data.df['time'][Sim.i]}"


def widget_func_step_back(b):
    """one step back in time"""
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    if Sim.i > 0:
        Sim.i -= 1
        Sim.gui["frameslider"].value = Sim.i
        Sim.gui["label_frame"].text = f"{Sim.i}/{len(Data.df)} time: {Data.df['time'][Sim.i]}"
        print("now at Step", Sim.i)
        update_stuff()
    else:
        print("Already at first step")


def widget_func_step_forward(b):
    """one step forward in time"""
    """one step back in time"""
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    if Sim.i < len(Data.df):
        Sim.i += 1
        Sim.gui["frameslider"].value = Sim.i
        Sim.gui["label_frame"].text = f"{Sim.i}/{len(Data.df)} time: {Data.df['time'][Sim.i]}"
        print("now at Step", Sim.i)
        update_stuff()
    else:
        print("already at first step")


def widget_func_end(b):
    """go to last step"""
    # print("start was pressed", b.text)
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    Sim.i = len(Data.df)
    Sim.gui["frameslider"].value = len(Data.df)
    Sim.gui["label_frame"].text = f"{Sim.i}/{len(Data.df)} time: {Data.df['time'][Sim.i]}"


def widget_func_pie_charts_visible(b):
    """checkbox """
    for (i,j), piebox in Sim.pie_charts.items():
        piebox.visible = b.checked

def widget_func_pie_chart_text(b):
    print("choice is now:", b.selected)

def widget_func_pie_chart_size(b):
    """winput"""
    for (i,j), piebox in Sim.pie_charts.items():
        piebox.size = vp.vector(b.number, 0.001, b.number)

def widget_func_play(b):
    # print("play button was pressed", b.text)
    if "play" in b.text.lower():
        Sim.animation_running = True
        Sim.gui["play"].text = "Pause ||"
        # update_stuff()
    else:
        Sim.animation_running = False
        Sim.gui["play"].text = "Play >"


def widget_func_tube_opacity(b):
    Sim.tubes_opacity = b.value
    Sim.gui["tube_opacity"].text = f"{Sim.tubes_opacity:.2f}"
    for (i, j), tubelist in Sim.tubes_node.items():
        for tube in tubelist:
            tube.opacity = b.value
    for tube in Sim.tubes_load.values():
        tube.opacity = b.value
    for tube in Sim.tubes_generator.values():
        tube.opacity = b.value
    for tube in Sim.tubes_storage.values():
        tube.opacity = b.value
    # generator glass
    for glass in Sim.generators_glass.values():
        glass.opacity = b.value
    # storage glass
    for glass in Sim.storages_glass.values():
        glass.opacity = b.value

def widget_func_quit(b):
    Sim.running = False


def widget_func_time_slider(b):
    """jump to a specific frame in the dataset """
    # print("slider is set to ", b.value)
    # Sim.connAB.pos.y = power_ab[b.value]
    # Sim.gui["label_frame"].text = str(b.value)
    Sim.i = b.value
    Sim.gui["label_frame"].text = f"{Sim.i}/{len(Data.df)} time: {Data.df['time'][Sim.i]}"
    update_stuff()


def widget_func_subnodes_add():
    print("adding a subnode")
    # delete all, then make new
    # get current number of subnodes
    # Sim.gui["help2] = "removing a subnode from:  subnode (29, 38, 1) press [+] or [-] buttons above to add or remove subnodes."
    full_text = Sim.gui["help2"].text
    if "subnode" not in full_text:
        print("Error: help2 does not display subnode")
        return
    # find positions of round brackets
    startchar = full_text.find("(")
    endchar = full_text.find(")")
    middle = full_text[startchar + 1:endchar]
    i, j, k = middle.split(",")
    i, j, k = int(i), int(j), int(k)
    # print("ijk:", i, j, k)
    # how many point are in the subcables ?
    n = Sim.sub_cables[(i, j)].npoints
    # print("npoints:", n, )
    # how many points in subcable exist?

    # is n an even number?
    # if n%2 == 0:
    #    print(f"error: even number of points {n} in sub-cable ({i},{j}")
    #    return
    # really remove some subnodes
    # remove all old
    for k in range(1, n - 1):
        Sim.sub_nodes[(i, j, k)].visible = False
    # print("before del:", len(Sim.sub_nodes))
    for key in list(Sim.sub_nodes.keys()):
        if all((key[0] == i, key[1] == j)):
            del Sim.sub_nodes[key]
    # print("after del:", len(Sim.sub_nodes))
    Sim.sub_cables[(i, j)].clear()  # remove all points
    # print("empty?", Sim.sub_cables[(i, j)].npoints)
    # create new ... should be an even number!
    new_n = n + 1
    # print(f"adding number of points in subcable to {new_n}")
    start = Sim.nodes[i].pos
    end = Sim.nodes[j].pos
    diff = end - start
    pointlist = []  # for sub-cables
    pointlist.append(start)
    for k in range(1, new_n):  # x subnodes
        p = start + k * vp.norm(diff) * vp.mag(diff) / new_n  # divide by
        subdisc = vp.cylinder(pos=p, radius=Sim.base["nodes_r"] / 2, color=vp.color.magenta,
                              axis=vp.vector(0, Sim.base["nodes_r"] / 3, 0),
                              pickable=True)
        subdisc.number = (i, j, k)
        subdisc.what = "subnode"
        Sim.sub_nodes[(i, j, k)] = subdisc
        pointlist.append(subdisc.pos)
    pointlist.append(end)
    # -- add points to curve
    Sim.sub_cables[(i, j)].unshift(pointlist)
    # print("new n:", Sim.sub_cables[(i, j)].npoints)
    # Sim.sub_cables[(i, j)] = vp.curve(color=vp.color.magenta, radius=0.0, pos=pointlist, pickable=False)
    # print("done")


def widget_func_subnodes_remove():
    # get current number of subnodes
    # Sim.gui["help2] = "removing a subnode from:  subnode (29, 38, 1) press [+] or [-] buttons above to add or remove subnodes."
    full_text = Sim.gui["help2"].text
    if "subnode" not in full_text:
        print("Error: help2 does not display subnode")
        return
    # find positions of round brackets
    startchar = full_text.find("(")
    endchar = full_text.find(")")
    middle = full_text[startchar + 1:endchar]
    i, j, k = middle.split(",")
    i, j, k = int(i), int(j), int(k)
    # print("ijk:",i,j,k)
    # how many point are in the subcables ?
    n = Sim.sub_cables[(i, j)].npoints
    # print("npoints:", n, )
    # how many points in subcable exist?
    if n <= 3:
        print("This is the only subnode in this cable. Impossible to remove")
        return
    # is n an even number?
    # if n%2 == 0:
    #    print(f"error: even number of points {n} in sub-cable ({i},{j}")
    #    return
    # really remove some subnodes
    # remove all old
    for k in range(1, n - 1):
        Sim.sub_nodes[(i, j, k)].visible = False
    # print("before del:",len(Sim.sub_nodes))
    for key in list(Sim.sub_nodes.keys()):
        if all((key[0] == i, key[1] == j)):
            del Sim.sub_nodes[key]
    # print("after del:", len(Sim.sub_nodes))
    Sim.sub_cables[(i, j)].clear()  # remove all points
    # print("empty?",Sim.sub_cables[(i,j)].npoints)
    # create new ... should be an even number!
    new_n = n - 2
    # print(f"reducing number of points in subcable to {new_n}")
    start = Sim.nodes[i].pos
    end = Sim.nodes[j].pos
    diff = end - start
    pointlist = []  # for sub-cables
    pointlist.append(start)
    for k in range(1, new_n):  # x subnodes
        p = start + k * vp.norm(diff) * vp.mag(diff) / new_n  # divide by
        subdisc = vp.cylinder(pos=p, radius=Sim.base["nodes_r"] / 2, color=vp.color.magenta,
                              axis=vp.vector(0, Sim.base["nodes_r"] / 3, 0),
                              pickable=True)
        subdisc.number = (i, j, k)
        subdisc.what = "subnode"
        Sim.sub_nodes[(i, j, k)] = subdisc
        pointlist.append(subdisc.pos)
    pointlist.append(end)
    # -- add points to curve
    Sim.sub_cables[(i, j)].unshift(pointlist)
    # print("new n:", Sim.sub_cables[(i,j)].npoints)
    # Sim.sub_cables[(i, j)] = vp.curve(color=vp.color.magenta, radius=0.0, pos=pointlist, pickable=False)
    # print("done")


def widget_func_toggle_dynamic_nodes(b):
    Sim.dynamic_colors["nodes"] = b.checked
    update_stuff()


def widget_func_toggle_dynamic_loads(b):
    Sim.dynamic_colors["loads"] = b.checked
    update_stuff()


def widget_func_toggle_dynamic_generators(b):
    Sim.dynamic_colors["generators"] = b.checked
    update_stuff()

def widget_func_toggle_dynamic_storages(b):
    Sim.dynamic_colors["storages"] = b.checked
    update_stuff()

def widget_func_toggle_dynamic_cables(b):
    Sim.dynamic_colors["cables"] = b.checked
    update_stuff()


def widget_func_toggle_nodes_labels(b):
    """toggles labels for nodes"""
    #choices = ["none", "Volt"],
    for name, value in Sim.labels.items():
        if name.startswith("node"):
            if b.index == 0: # none
                Sim.labels[name].visible = False
            elif b.index == 1: # Volt
                Sim.labels[name].visible = True
                #Sim.labels[name].visible = b.checked


def widget_func_toggle_loads_labels(b):
    if b.index == 1:
        Sim.label_load = "p"
    #elif b.index == 2:
    #    Sim.label_load = "loading" # ??
    for name, value in Sim.labels.items():
        if name.startswith("load"):
            if b.index == 0:
                Sim.labels[name].visible = False
            else:
                Sim.labels[name].visible = True

def widget_func_load_decimal(b):
    Sim.decimals_load = b.number
    update_stuff()


def widget_func_toggle_nodes_letters(b):
    """toggle letters for nodes"""
    # Sim.letters[f"node {number}"]
    # 0: none, 1:name, 2:number, 3:both
    # Data.node_names = {}  # node_number: node_name
    # Data.node_names2 = {}  # node_name: node_number
    for key, label in Sim.letters.items():
        if key.startswith("node "):
            number = int(key.split(" ")[-1])
            name = Data.node_names[number]
            if b.index == 0:
                label.visible = False
            elif b.index == 1:  # name
                label.text = name
                label.visible = True
            elif b.index == 2: # number
                label.text = str(number)
                label.visible = True
            elif b.index == 3: # both
                label.text = f"{number}\n{name}"
                label.visible = True
    #        label.visible = b.checked



def widget_func_toggle_cable_letters(b):
    #for key, label in Sim.letters.items():
    #    if key.startswith("cable "):
    #        label.visible = b.checked
    # "cable {i}-{j}"
    for key, label in Sim.letters.items():
        if key.startswith("cable "):
            number1 = int(key.split(" ")[-1].split("-")[0])
            number2 = int(key.split(" ")[-1].split("-")[1])
            name1 = Data.node_names[number1]
            name2 = Data.node_names[number2]
            if b.index == 0:
                label.visible = False
            elif b.index == 1:  # name
                label.text = f"{name1}-{name2}"
                label.visible = True
            elif b.index == 2:  # number
                label.text = f"{number1}-{number2}"
                label.visible = True
            elif b.index == 3:  # both
                label.text = f"{number1}-{number2}\n{name1}-{name2}"
                label.visible = True


def widget_func_toggle_generator_letters(b):
    #for key, label in Sim.letters.items():
    #    if key.startswith("generator "):
    #        label.visible = b.checked
    # Data.node_names = {}  # node_number: node_name
    # Data.node_names2 = {}  # node_name: node_number
    for key, label in Sim.letters.items():
        if key.startswith("generator "):
            number = int(key.split(" ")[-1])
            name = Data.node_names[number]
            if b.index == 0:
                label.visible = False
            elif b.index == 1:  # name
                label.text = name
                label.visible = True
            elif b.index == 2: # number
                label.text = str(number)
                label.visible = True
            elif b.index == 3: # both
                label.text = f"{number}\n{name}"
                label.visible = True


def widget_func_toggle_loads_letters(b):
    #for key, label in Sim.letters.items():
    #    if key.startswith("load "):
    #        label.visible = b.checked
    # Data.node_names = {}  # node_number: node_name
    # Data.node_names2 = {}  # node_name: node_number
    for key, label in Sim.letters.items():
        if key.startswith("load "):
            number = int(key.split(" ")[-1])
            name = Data.node_names[number]
            if b.index == 0:
                label.visible = False
            elif b.index == 1:  # name
                label.text = name
                label.visible = True
            elif b.index == 2: # number
                label.text = str(number)
                label.visible = True
            elif b.index == 3: # both
                label.text = f"{number}\n{name}"
                label.visible = True


def widget_func_toggle_generator_labels(b):
    """toggles labels for generators"""
    #["none", "p", "angle", "p+angle", "loading"],
    if b.index == 1:
        Sim.label_generator = "p"
    elif b.index == 2:
        Sim.label_generator = "angle"
    elif b.index == 3:
        Sim.label_generator = "p+angle"
    elif b.index == 4:
        Sim.label_generator = "loading"
    for name, value in Sim.labels.items():
        if name.startswith("generator"):
            if b.index > 0:
                Sim.labels[name].visible = True
            else:
                Sim.labels[name].visible = False
    if b.index > 0:
        update_stuff()


def widget_func_toggle_cable_labels(b):
    """toggles labels for cables"""
    # none, p, loading, p+loading
    if b.index == 1:
        Sim.label_cable = "p"
        update_stuff()
    elif b.index == 2:
        Sim.label_cable = "loading"
        update_stuff()
    elif b.index == 3:
        Sim.label_cable = "p+loading"
        update_stuff()
    elif b.index == 4:
        Sim.label_cable = "mva"
        update_stuff()
    for name, value in Sim.labels.items():
        if name.startswith("cable"):
            if b.index == 0:
                Sim.labels[name].visible = False
            else:
                Sim.labels[name].visible = True


def widget_func_generator_decimal(b):
    Sim.decimals_generator = b.number
    update_stuff()

def widget_func_cable_decimal(b):
    Sim.decimals_cable = b.number
    update_stuff()

def widget_func_toggle_cables(b):
    """toggles visibility for sub-cables on floor (shadows) """
    # print("setting subcables to:", b.checked)
    for curve in Sim.sub_cables.values():
        curve.visible = b.checked
    # tubes:
    for (i, j), tubelist in Sim.tubes_node.items():
        for tube in tubelist:
            tube.visible = b.checked
    for tube in Sim.tubes_load.values():
        tube.visible = b.checked
    for tube in Sim.tubes_generator.values():
        tube.visible = b.checked
    for tube in Sim.tubes_storage.values():
        tube.visible = b.checked
    # arrow shadows:
    for number, arrow in Sim.shadows.items():
        arrow.visible = b.checked
    # arrows:
    for number, arrowlist in Sim.arrows.items():
        for a in arrowlist:
            a.visible = b.checked
    # update gui checkboxes:
    Sim.gui["box_cable_shadow"].checked = b.checked
    Sim.gui["arrows_visible"].checked = b.checked
    Sim.gui["box_arrow_shadow"].checked = b.checked
    update_stuff()

def widget_func_toggle_glass_visible(b):
    for number, glass in Sim.generators_glass.items():
        glass.visible=b.checked
    for number, glass in Sim.storages_glass.items():
        glass.bisible=b.checked

def widget_func_toggle_storages(b):
    """toggle visibility for wind storages """
    for i in Sim.storages:
        Sim.storages[i].visible = b.checked
        Sim.storage_lines[i].visible = b.checked

def widget_func_toggle_storages_letters(b):
    #for key, label in Sim.letters.items():
    #    if key.startswith("storage "):
    #        label.visible = b.checked
    # Sim.letters[f"node {number}"]
    # 0: none, 1:name, 2:number, 3:both
    # Data.node_names = {}  # node_number: node_name
    # Data.node_names2 = {}  # node_name: node_number
    for key, label in Sim.letters.items():
        if key.startswith("storage "):
            number = int(key.split(" ")[-1])
            name = Data.node_names[number]
            if b.index == 0:
                label.visible = False
            elif b.index == 1:  # name
                label.text = name
                label.visible = True
            elif b.index == 2:  # number
                label.text = str(number)
                label.visible = True
            elif b.index == 3:  # both
                label.text = f"{number}\n{name}"
                label.visible = True

def widget_func_toggle_storages_labels(b):
    """toggles labels for storages"""
    #["none", "P", "% loading"],
    if b.index == 1:
        Sim.label_storage = "p"
    elif b.index == 2:
        Sim.label_storage = "loading"
    for name, value in Sim.labels.items():
        if name.startswith("storage"):
            if b.index == 0:
                Sim.labels[name].visible = False
            elif b.index in (1,2):
                Sim.labels[name].visible = True
    if b.index in (1,2):
        update_stuff()

def widget_func_storage_decimal(b):
    Sim.decimals_storage = b.number
    update_stuff()

def widget_func_toggle_cursor_brackets(b):
    Sim.gui["bracket_left"].visible = b.checked
    Sim.gui["bracket_right"].visible = b.checked
    Sim.axis_x.visible = b.checked
    Sim.axis_y.visible = b.checked
    Sim.axis_z.visible = b.checked


def widget_func_toggle_nodes(b):
    """toggle visibility for nodes (busbars)"""
    for i, cyl in Sim.nodes.items():
        cyl.visible = b.checked


def widget_func_toggle_generators(b):
    """toggle visibility for wind generators """
    for i in Sim.generators:
        Sim.generators[i].visible = b.checked
        # Sim.discs[i].visible = b.checked
        # Sim.pointer0[i].visible = b.checked
        # Sim.pointer1[i].visible = b.checked
        Sim.generator_lines[i].visible = b.checked


def widget_func_toggle_loads(b):
    """toggle visibility for loads"""
    for i in Sim.loads:
        Sim.loads[i].visible = b.checked
        Sim.load_lines[i].visible = b.checked


def widget_func_toggle_generators_angle(b):
    """toggle visibility for wind generators disc and pointers"""
    for i in Sim.generators:
        # Sim.generators[i].visible = b.checked
        Sim.discs[i].visible = b.checked
        Sim.pointer0[i].visible = b.checked
        Sim.pointer1[i].visible = b.checked
        # Sim.generator_lines[i].visible = b.checked


def widget_func_toggle_arrow_shadow(b):
    for number, arrow in Sim.shadows.items():
        arrow.visible = b.checked

def widget_func_toggle_arrows(b):
    # make arrows visible / invisible
    for number, arrowlist in Sim.arrows.items():
        for a in arrowlist:
            a.visible = b.checked

def widget_func_toggle_flying_while_paused(b):
    Sim.flying_while_paused = b.checked


def widget_func_toggle_cable_shadow(b):
    for curve in Sim.sub_cables.values():
        for k in range(curve.npoints):
            curve.modify(k, visible=b.checked)
    # generator-cables
    for curve in Sim.generator_lines.values():
        curve.visible = b.checked

    # load-cables
    for curve in Sim.load_lines.values():
        curve.visible = b.checked
        # pass



def widget_func_toggle_grid(b):
    """toggles grid lines"""
    for line in Sim.grid:
        line.visible = b.checked



def widget_func_toggle_sloped_cables(b):
    Sim.sloped_cables = b.checked
    # if not b.checked:
    # return all subcable curve points to y value zero:
    # for (i, j), curve in Sim.sub_cables.items():
    # yi = Sim.nodes[i].axis.y
    # yj = Sim.nodes[j].axis.y
    #    n = Sim.number_of_sub_cables
    # delta = (yj - yi) / n
    #    for k in range(curve.npoints):
    #        oldpos = curve.point(k)["pos"]
    #        curve.modify(k, pos=vp.vector(oldpos.x, 0, oldpos.z))
    # for arrow in Sim.arrows_ij.values():
    #    arrow.pos.y = 0
    #    arrow.axis.y = 0
    # for arrow in Sim.arrows_ji.values():
    #    arrow.pos.y = 0
    #    arrow.axis.y = 0
    update_stuff()



def update_generator_glass():
    for number, glass in Sim.generators_glass.items():
        #glass.visible = False
        glass.radius = Sim.generators[number].radius * 1.05
        cyl = Sim.generators[number]
        glass.axis = vp.vector(0, cyl.rating * Sim.factor["generators_h"] + Sim.base["generators_h"], 0)
        #glass.axis.y = Sim.generators[number].rating * Sim.factor["generators_h"] + Sim.base["generators_h"]
        #glass.axis.y = Sim.generators[number].axis.y * Sim.ganerators[number].rating
        #glass.visible = True
        if number == 23:
            print(f"Generator glass number {number}, radius {glass.radius}, axis.y {glass.axis.y} , generator.axis.y {Sim.generators[number].axis.y}, rating {Sim.generators[number].rating}")

def update_storage_glass():
    for number, glass in Sim.storages_glass.items():
        glass.radius = Sim.storages[number].radius * 1.05
        glass.axis.y = Sim.storages[number].rating * Sim.factor["storages_h"] + Sim.base["storages_h"]

def widget_func_generators_factor_h(b):
    # print("the y factor for generators is now:", b.number)
    Sim.factor["generators_h"] = b.number
    update_stuff()
    update_generator_glass()



def widget_func_cables_factor_h(b):
    Sim.factor["cables_h"] = b.number
    update_stuff()


def widget_func_generators_factor_r(b):
    Sim.factor["generators_r"] = b.number
    update_stuff()
    update_generator_glass()

def widget_func_loads_factor_r(b):
    Sim.factor["loads_r"] = b.number
    update_stuff()


def widget_func_generators_base_h(b):
    Sim.base["generators_h"] = b.number
    update_stuff()
    update_generator_glass()


def widget_func_storages_base_h(b):
    Sim.base["storages_h"] = b.number
    update_stuff()
    update_storage_glass()

def widget_func_storages_base_r(b):
    Sim.base["storages_r"] = b.number
    update_stuff()
    update_storage_glass()

def widget_func_storages_factor_h(b):
    print("old:", Sim.factor["storages_h"])
    Sim.factor["storages_h"] = b.number
    print("new:", Sim.factor["storages_h"])
    update_stuff()
    update_storage_glass()
    #print("final:", Sim.factor["storages_h"])

def widget_func_storages_factor_r(b):
    Sim.factor["storages_r"] = b.number
    update_stuff()
    update_storage_glass()

def widget_func_flying_arrows_speed_min(b):
    Sim.arrows_speed_min = b.number


def widget_func_flying_arrows_speed_max(b):
    Sim.arrows_speed_max = b.number


def widget_func_cables_base_h(b):
    Sim.base["cables_h"] = b.number
    update_stuff()


def widget_func_generators_base_r(b):
    Sim.base["generators_r"] = b.number
    update_stuff()
    update_generator_glass()


def widget_func_nodes_factor_h(b):
    # print("the y factor for nodes is now:", b.number)
    Sim.factor["nodes_h"] = b.number
    update_stuff()


def widget_func_loads_factor_h(b):
    Sim.factor["loads_h"] = b.number
    update_stuff()


def widget_func_nodes_factor_r(b):
    Sim.factor["nodes_r"] = b.number
    update_stuff()

def widget_func_nodes_decimal(b):
    Sim.decimals_node = b.number
    update_stuff()

def widget_func_map(b):
    # index:0 : google (mapname1), index1: empty (mapname2)
    if b.index == 0:
        Sim.mapbox.texture={'file': Sim.mapname1,
                 # 'bumpmap':bumpmaps.stucco,
                 # 'place':'left',
                 # 'flipx':True,
                 # 'flipy':True,
                 'turn': 0,
                 }
    elif b.index == 1:
        Sim.mapbox.texture = {'file': Sim.mapname2,
                              # 'bumpmap':bumpmaps.stucco,
                              # 'place':'left',
                              # 'flipx':True,
                              # 'flipy':True,
                              'turn': 0,
                              }
    elif b.index == 2:
        Sim.mapbox.texture = None



def widget_func_nodes_base_h(b):
    Sim.base["nodes_h"] = b.number
    update_stuff()


def widget_func_create_curves(b):
    Sim.gui["create_curves"].disabled = True
    create_stuff2_curves()

def widget_func_filter_combo(b):
    """
    Sim.gui["filter_combo"]
    ["Nodes", "Generators", "Loads","Storages" ,"Cables", ]
    """
    #print("index:", b.index)
    if b.index == 0: # Nodes
        print("node curves are: ", list(Sim.gui["node_curves"].keys()))
        visible_node_numbers =  [n for n in Sim.gui["node_curves"].keys() if Sim.gui["node_curves"][n].visible]
        if len(visible_node_numbers) == len(Data.node_numbers):
            t = "all"
        elif len(visible_node_numbers) == 0:
            t = "none"
        else:
            t = " ".join([str(n) for n in visible_node_numbers])
        Sim.gui["filter_text"].text = t

def widget_func_filter_text(b):
    """
    Sim.gui["filter_text"]
    """

    print("text entered into filter was:", b.text)
    curvedict =  {
       "Nodes": ( "node_curves", ),
       "Loads": ( "load_curves",),
       "Generators": ( "generator_angle_curves", "generator_power_curves", "generator_loading_curves" ),
       "Storages" : ("storage_power_curves", "storage_loading_curves","storage_state_curves" ),
       "Cables": ( "cable_loading_curves", "cable_power_curves" ),
    }
    for node_type, curvenames in curvedict.items():
        if Sim.gui["filter_combo"].selected == node_type: # "Nodes":
            for curvename in curvenames:
                if b.text.lower() in ("none", "0", "nothing", "clear"):
                    for node_number, curve in Sim.gui[curvename].items():
                        curve.visible = False
                elif b.text.lower() in ("all", "*"):
                    for node_number, curve in Sim.gui[curvename].items():
                        curve.visible = True
                elif len(b.text) > 0:
                    filterwords = b.text
                    # replace commas with space
                    filterwords = filterwords.replace(",", " ")
                    filterwords = [word for word in filterwords.split(" ") if len(word) > 0]
                    filternumbers = []
                    for word in filterwords:
                        if word.isdigit() and int(word) in Data.node_numbers:
                            filternumbers.append(int(word))
                        elif word.upper() in Data.node_names2:
                            filternumbers.append(Data.node_names2[word.upper()])
                    b.text= " ".join([str(i) for i in filternumbers])
                    for node_number, curve in Sim.gui[curvename].items():
                        if node_number in filternumbers:
                            curve.visible = True
                        else:
                            curve.visible = False
            break # not necessary any more to test other node types



def widget_func_legend_combo(b):
    #print("index: ", b.index) # 0.... show, 1 .... hide
    for textlabel in Sim.gui["legend"]:
        if b.index == 0:
            textlabel.visible = True
        elif b.index == 1:
            textlabel.visible = False

def widget_func_legend_height(b):
    # winput
    for textlabel in Sim.gui["legend"]:
        textlabel.height = b.number


def widget_func_load_preset(b):
    print("selected preset:", b.index, b.selected)
    if b.index == 1: # default
        Sim.gui["box_sloped_cables"].checked = False
        Sim.sloped_cables = False
        # nodes
        Sim.gui["nodes_factor_r"].text = "0.0"
        Sim.factor["nodes_r"] = 0.0
        Sim.gui["nodes_base_r"].text= "0.06"
        Sim.base["nodes_r"] = 0.06
        Sim.gui["nodes_factor_h"].text= "0.1"
        Sim.factor["nodes_h"] = 0.1
        Sim.gui["nodes_base_h"].text= "0.0"
        Sim.base["nodes_h"] = 0.0
        # cables
        Sim.gui["cables_factor_r"].text = "0.0"
        Sim.factor["cables_r"] = 0.0
        Sim.gui["cables_base_r"].text = "0.03"
        Sim.base["cables_r"] = 0.03
        Sim.gui["cables_factor_h"].text = "0.0"
        Sim.factor["cables_h"] = 0.0
        Sim.gui["cables_base_h"].text = "0.03"
        Sim.base["cables_h"] = 0.03
        # generators
        Sim.gui["generators_factor_r"].text = "0.0"
        Sim.factor["generators_r"] = 0.0
        Sim.gui["generators_base_r"].text = "0.05"
        Sim.base["generators_r"] = 0.05
        Sim.gui["generators_factor_h"].text = "0.001"
        Sim.factor["generators_h"] = 0.001
        Sim.gui["generators_base_h"].text = "0.0"
        Sim.base["generators_h"] = 0.0
        # loads
        Sim.gui["loads_factor_r"].text = "0.0"
        Sim.factor["loads_r"] = 0.0
        Sim.gui["loads_base_r"].text = "0.04"
        Sim.base["loads_r"] = 0.04
        Sim.gui["loads_factor_h"].text = "0.001"
        Sim.factor["loads_h"] = 0.001
        Sim.gui["loads_base_h"].text = "0.0"
        Sim.base["loads_h"] = 0.0
    elif b.index == 2: # yokoyama1 (A) .. generators change height, cables change radius
        Sim.gui["box_sloped_cables"].checked = False
        Sim.sloped_cables = False
        # nodes
        Sim.gui["nodes_factor_r"].text = "0.0"
        Sim.factor["nodes_r"] = 0.0
        Sim.gui["nodes_base_r"].text = "0.04"
        Sim.base["nodes_r"] = 0.04
        Sim.gui["nodes_factor_h"].text = "0.0"
        Sim.factor["nodes_h"] = 0.0
        Sim.gui["nodes_base_h"].text = "0.1"
        Sim.base["nodes_h"] = 0.1
        # cables
        Sim.gui["cables_factor_r"].text = "0.0001"
        Sim.factor["cables_r"] = 0.0001
        Sim.gui["cables_base_r"].text = "0.01"
        Sim.base["cables_r"] = 0.01
        Sim.gui["cables_factor_h"].text = "0.0"
        Sim.factor["cables_h"] = 0.0
        Sim.gui["cables_base_h"].text = "0.01"
        Sim.base["cables_h"] = 0.01
        # generators
        Sim.gui["generators_factor_r"].text = "0.0"
        Sim.factor["generators_r"] = 0.0
        Sim.gui["generators_base_r"].text = "0.05"
        Sim.base["generators_r"] = 0.05
        Sim.gui["generators_factor_h"].text = "0.001"
        Sim.factor["generators_h"] = 0.001
        Sim.gui["generators_base_h"].text = "0.0"
        Sim.base["generators_h"] = 0.0
        # loads
        Sim.gui["loads_factor_r"].text = "0.0"
        Sim.factor["loads_r"] = 0.0
        Sim.gui["loads_base_r"].text = "0.04"
        Sim.base["loads_r"] = 0.04
        Sim.gui["loads_factor_h"].text = "0.001"
        Sim.factor["loads_h"] = 0.001
        Sim.gui["loads_base_h"].text = "0.0"
        Sim.base["loads_h"] = 0.0
    elif b.index == 3: # yokoyama2 (B) .. only generators change height
        Sim.gui["box_sloped_cables"].checked = False
        Sim.sloped_cables = False
        # nodes
        Sim.gui["nodes_factor_r"].text = "0.0"
        Sim.factor["nodes_r"] = 0.0
        Sim.gui["nodes_base_r"].text = "0.04"
        Sim.base["nodes_r"] = 0.04
        Sim.gui["nodes_factor_h"].text = "0.0"
        Sim.factor["nodes_h"] = 0.0
        Sim.gui["nodes_base_h"].text = "0.1"
        Sim.base["nodes_h"] = 0.1
        # cables
        Sim.gui["cables_factor_r"].text = "0.0"
        Sim.factor["cables_r"] = 0.0
        Sim.gui["cables_base_r"].text = "0.03"
        Sim.base["cables_r"] = 0.03
        Sim.gui["cables_factor_h"].text = "0.0"
        Sim.factor["cables_h"] = 0.0
        Sim.gui["cables_base_h"].text = "0.03"
        Sim.base["cables_h"] = 0.03
        # generators
        Sim.gui["generators_factor_r"].text = "0.0"
        Sim.factor["generators_r"] = 0.0
        Sim.gui["generators_base_r"].text = "0.05"
        Sim.base["generators_r"] = 0.05
        Sim.gui["generators_factor_h"].text = "0.001"
        Sim.factor["generators_h"] = 0.001
        Sim.gui["generators_base_h"].text = "0.0"
        Sim.base["generators_h"] = 0.0
        # loads
        Sim.gui["loads_factor_r"].text = "0.0"
        Sim.factor["loads_r"] = 0.0
        Sim.gui["loads_base_r"].text = "0.04"
        Sim.base["loads_r"] = 0.04
        Sim.gui["loads_factor_h"].text = "0.001"
        Sim.factor["loads_h"] = 0.001
        Sim.gui["loads_base_h"].text = "0.0"
        Sim.base["loads_h"] = 0.0
    elif b.index == 4:  # yokoyama3 (C) sloped cables, nodes and generators change height
        Sim.gui["box_sloped_cables"].checked = True
        Sim.sloped_cables = True
        # nodes
        Sim.gui["nodes_factor_r"].text = "0.0"
        Sim.factor["nodes_r"] = 0.0
        Sim.gui["nodes_base_r"].text = "0.06"
        Sim.base["nodes_r"] = 0.06
        Sim.gui["nodes_factor_h"].text = "0.1"
        Sim.factor["nodes_h"] = 0.1
        Sim.gui["nodes_base_h"].text = "0.0"
        Sim.base["nodes_h"] = 0.0
        # cables
        Sim.gui["cables_factor_r"].text = "0.0"
        Sim.factor["cables_r"] = 0.0
        Sim.gui["cables_base_r"].text = "0.03"
        Sim.base["cables_r"] = 0.03
        Sim.gui["cables_factor_h"].text = "0.0"
        Sim.factor["cables_h"] = 0.0
        Sim.gui["cables_base_h"].text = "0.03"
        Sim.base["cables_h"] = 0.03
        # generators
        Sim.gui["generators_factor_r"].text = "0.0"
        Sim.factor["generators_r"] = 0.0
        Sim.gui["generators_base_r"].text = "0.05"
        Sim.base["generators_r"] = 0.05
        Sim.gui["generators_factor_h"].text = "0.001"
        Sim.factor["generators_h"] = 0.001
        Sim.gui["generators_base_h"].text = "0.0"
        Sim.base["generators_h"] = 0.0
        # loads
        Sim.gui["loads_factor_r"].text = "0.0"
        Sim.factor["loads_r"] = 0.0
        Sim.gui["loads_base_r"].text = "0.04"
        Sim.base["loads_r"] = 0.04
        Sim.gui["loads_factor_h"].text = "0.001"
        Sim.factor["loads_h"] = 0.001
        Sim.gui["loads_base_h"].text = "0.0"
        Sim.base["loads_h"] = 0.0
    elif b.index == 5: # Yokoama D: sloped cables, nodes change height, generators change height and radius
        Sim.gui["box_sloped_cables"].checked = True
        Sim.sloped_cables = True
        # nodes
        Sim.gui["nodes_factor_r"].text = "0.0"
        Sim.factor["nodes_r"] = 0.0
        Sim.gui["nodes_base_r"].text = "0.06"
        Sim.base["nodes_r"] = 0.06
        Sim.gui["nodes_factor_h"].text = "0.1"
        Sim.factor["nodes_h"] = 0.1
        Sim.gui["nodes_base_h"].text = "0.0"
        Sim.base["nodes_h"] = 0.0
        # cables
        Sim.gui["cables_factor_r"].text = "0.0"
        Sim.factor["cables_r"] = 0.0
        Sim.gui["cables_base_r"].text = "0.03"
        Sim.base["cables_r"] = 0.03
        Sim.gui["cables_factor_h"].text = "0.0"
        Sim.factor["cables_h"] = 0.0
        Sim.gui["cables_base_h"].text = "0.03"
        Sim.base["cables_h"] = 0.03
        # generators
        Sim.gui["generators_factor_r"].text = "0.0001"
        Sim.factor["generators_r"] = 0.0001
        Sim.gui["generators_base_r"].text = "0.01"
        Sim.base["generators_r"] = 0.01
        Sim.gui["generators_factor_h"].text = "0.001"
        Sim.factor["generators_h"] = 0.001
        Sim.gui["generators_base_h"].text = "0.0"
        Sim.base["generators_h"] = 0.0
        # loads
        Sim.gui["loads_factor_r"].text = "0.0"
        Sim.factor["loads_r"] = 0.0
        Sim.gui["loads_base_r"].text = "0.04"
        Sim.base["loads_r"] = 0.04
        Sim.gui["loads_factor_h"].text = "0.001"
        Sim.factor["loads_h"] = 0.001
        Sim.gui["loads_base_h"].text = "0.0"
        Sim.base["loads_h"] = 0.0
    # in every case:
    update_stuff()



def widget_func_loads_base_h(b):
    Sim.base["loads_h"] = b.number
    update_stuff()


def widget_func_nodes_base_r(b):
    Sim.base["nodes_r"] = b.number
    update_stuff()


def widget_func_loads_base_r(b):
    Sim.base["loads_r"] = b.number
    update_stuff()


def set_tube_radius(radius):
    for (i, j), tubelist in Sim.tubes_node.items():
        for tube in tubelist:
            tube.radius = radius
    for tube in Sim.tubes_load.values():
        tube.radius = radius
    for tube in Sim.tubes_generator.values():
        tube.radius = radius
    for tube in Sim.tubes_storage.values():
        tube.radius = radius
    ## generator glass
    #for glass in Sim.generators_glass.values():
    #    glass.opacity = b.value
    ## storage glass
    #for glass in Sim.storages_glass.values():
    #    glass.opacity = b.value

def widget_func_cables_factor_r(b):
    Sim.factor["cables_r"] = b.number
    update_stuff()
    # tubes radius
    radius = Sim.base["cables_r"] + Sim.factor["cables_r"] * Data.cables_power_max * Sim.tubes_radius_factor + Sim.tubes_radius_delta
    set_tube_radius(radius)

def widget_func_cables_base_r(b):
    Sim.base["cables_r"] = b.number
    update_stuff()
    # tubes radius
    radius = Sim.base["cables_r"] + Sim.factor["cables_r"] * Data.cables_power_max * Sim.tubes_radius_factor + Sim.tubes_radius_delta
    set_tube_radius(radius)

def widget_func_camera_goto(b):
    #menu
    print("camera should go to node:", b.selected)
    if b.selected == "center":
        camera_to_topdown()
        return
    node_number = int(b.selected.split()[0])
    nodepos = Sim.nodes[node_number].pos
    print(nodepos)

    Sim.scene.camera.pos = vp.vector(nodepos.x, Sim.camera_height, nodepos.z)
    Sim.scene.forward = vp.vector(0.0, -1, 0)  # camera pos is moved
    # Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height , Sim.center.z) # horrible result
    Sim.scene.camera.pos.x = nodepos.x  # ok

    Sim.scene.up = vp.vector(0, 0, -1)

    ###Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height, geo_to_local(Sim.center.z))
    # Sim.scene.range = Sim.grid_max_x / 2
    #Sim.scene.autoscale = True

    # Sim.scene.userzoom = False
    #Sim.scene.userspin = False
    # Sim.scene.camera.pos = vp.vector(Sim.center.x, Sim.camera_height , geo_to_local(Sim.center.z))
    # Sim.scene.camera.pos.x = Sim.center.x
    #Sim.scene.center = Sim.center
    Sim.scene.autoscale = False
    Sim.scene.range = Sim.camera_range

def widget_func_camera_north(b):
    Sim.scene.camera.pos.z -= 0.25
    print(Sim.scene.camera.pos)


def widget_func_camera_NS(b):
    Sim.scene.center.z = b.value
    Sim.gui["camera_NS"].text = f"{Sim.scene.center.z:.2f}"


def widget_func_camera_WE(b):
    Sim.scene.center.x = b.value
    Sim.gui["camera_WE"].text = f"{Sim.scene.center.x:.2f}"


def widget_func_camera_pitch(b):
    Sim.gui["camera_pitch"].text = f"{b.value:.2f}"
    old_center = Sim.scene.center
    ###angle_now = vp.degrees(vp.diff_angle(Sim.test_arrow.axis, vp.vector(0,0,1)))
    angle_now = vp.degrees(vp.diff_angle(vp.vector(0, Sim.scene.forward.y, Sim.scene.forward.z), vp.vector(0, 0, 1)))
    # print("angle now:", angle_now)
    delta = angle_now - b.value
    # print("delta:", delta)
    ###Sim.test_arrow.rotate(angle=-delta/100, axis=vp.vector(1,0,0))
    # Sim.scene.camera.axis = vp.vector(0,-1,0)
    Sim.scene.camera.rotate(angle=vp.radians(-delta), axis=vp.cross(Sim.scene.forward, Sim.scene.up))
    Sim.scene.center = old_center


def widget_func_camera_cw(b):
    old_center = Sim.scene.center
    Sim.scene.camera.rotate(angle=vp.radians(1), axis=vp.vector(0, 1, 0))
    angle_now = vp.degrees(vp.diff_angle(vp.vector(Sim.scene.forward.x, 0, Sim.scene.forward.z), vp.vector(0, 0, 1)))
    Sim.gui["camera_angle"].text = f"{angle_now:.2f}"
    Sim.scene.center = old_center


def widget_func_camera_ccw(b):
    old_center = Sim.scene.center
    Sim.scene.camera.rotate(angle=vp.radians(-1), axis=vp.vector(0, 1, 0))
    angle_now = vp.degrees(vp.diff_angle(vp.vector(Sim.scene.forward.x, 0, Sim.scene.forward.z), vp.vector(0, 0, 1)))
    Sim.gui["camera_angle"].text = f"{angle_now:.2f}"
    Sim.scene.center = old_center


def widget_func_camera_angle(b):
    # TODO works bad
    Sim.gui["camera_angle"].text = f"{b.value:.2f}"
    old_center = Sim.scene.center
    ###angle_now = vp.degrees(vp.diff_angle(Sim.test_arrow.axis, vp.vector(0,0,1)))
    angle_now = vp.degrees(vp.diff_angle(vp.vector(Sim.scene.forward.x, 0, Sim.scene.forward.z), vp.vector(0, 0, 1)))
    print("angle now:", angle_now)
    delta = 180 - b.value - angle_now
    print("delta:", delta)
    ###Sim.test_arrow.rotate(angle=-delta/100, axis=vp.vector(1,0,0))
    # Sim.scene.camera.axis = vp.vector(0,-1,0)
    Sim.scene.camera.rotate(angle=vp.radians(delta) / 100, axis=vp.vector(0, 1, 0))
    Sim.scene.center = old_center


def widget_func_camera1(b):
    """reset camera to start position"""
    camera_to_topdown()
    Sim.scene.userspin = True
    # Sim.scene.camera.pos.y = 4.0 # ??


def widget_func_camera2(b):
    Sim.scene.camera.pos = Sim.camera2["pos"]
    Sim.scene.forward = Sim.camera2["forward"]
    Sim.scene.up = Sim.camera2["up"]
    Sim.scene.range = Sim.camera2["range"]
    Sim.scene.center = Sim.camera2["center"]


def widget_func_camera3(b):
    Sim.scene.camera.pos = Sim.camera3["pos"]
    Sim.scene.forward = Sim.camera3["forward"]
    Sim.scene.up = Sim.camera3["up"]
    Sim.scene.range = Sim.camera3["range"]
    Sim.scene.center = Sim.camera3["center"]


def widget_func_camera4(b):
    Sim.scene.camera.pos = Sim.camera4["pos"]
    Sim.scene.forward = Sim.camera4["forward"]
    Sim.scene.up = Sim.camera4["up"]
    Sim.scene.range = Sim.camera4["range"]
    Sim.scene.center = Sim.camera4["center"]


def widget_func_save_camera2(b):
    Sim.camera2 = {"pos": Sim.scene.camera.pos,
                   "forward": Sim.scene.forward,
                   "up": Sim.scene.up,
                   "range": Sim.scene.range,
                   "center": Sim.scene.center, }
    Sim.gui["camerapos2"].disabled = False
    Sim.gui["save_camerapos3"].disabled = False


def widget_func_save_camera3(b):
    Sim.camera3 = {"pos": Sim.scene.camera.pos,
                   "forward": Sim.scene.forward,
                   "up": Sim.scene.up,
                   "range": Sim.scene.range,
                   "center": Sim.scene.center, }
    Sim.gui["camerapos3"].disabled = False
    Sim.gui["save_camerapos4"].disabled = False


def widget_func_save_camera4(b):
    Sim.camera4 = {"pos": Sim.scene.camera.pos,
                   "forward": Sim.scene.forward,
                   "up": Sim.scene.up,
                   "range": Sim.scene.range,
                   "center": Sim.scene.center, }
    Sim.gui["camerapos4"].disabled = False


def widget_func_flying_arrows_length(b):
    """update length of flying arrows"""
    Sim.base["flying_arrows_length"] = b.number
    update_stuff()


def widget_func_factor_losses(b):
    # print("the y factor for losses is now:", b.number)
    Sim.factor["losses"] = b.number
    update_stuff()


def widget_func_animation_duration(b):
    """set new animation duration from gui"""
    # animation_duration = 2000  # seconds
    # frame_duration = animation_duration / len(Data.df)
    # sanity check
    new_number = b.number
    if new_number <= 0:
        print("new number for animation duration must be positive")
        return
    Sim.animation_duration = new_number
    Sim.frame_duration = new_number / len(Data.df)
    print("animation duration is now", new_number)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_start_simulation(b):
    # create stuff after "start simulation" button was clicked
    Sim.scene.select()
    Sim.gui["create_curves"].disabled=False
    #Sim.gui["wait_label"] = vp.label(pixel_pos=True,
    #                                 pos=vp.vector(Sim.canvas_width/2, Sim.canvas_height/2,0),
    #                                 height=48,
    #                                 color=vp.color.purple,
    #                                 text="please wait....",
    #                                 align="center",
    #                                 visible=True,
    #                                 )
    #create_stuff2_curves()
    Sim.scene.select()
    #Sim.gui["wait_label"].visible = False
    layout_save()
    # enable preset buttons
    Sim.gui["preset"].disabled = False
    #Sim.gui["preset_A"].disabled = False
    #Sim.gui["preset_B"].disabled = False
    #Sim.gui["preset_C"].disabled = False

    # Sim.gui["layout_save"].disabled = True
    Sim.mode = "simulation"
    Sim.gui["mode"].text = f"{Sim.mode}"
    # Sim.gui["arrange"].disabled = False
    Sim.gui["simulation"].disabled = True
    Sim.gui["restart"].disabled = False
    Sim.gui["end"].disabled = False
    Sim.gui["play"].disabled = False
    Sim.gui["step_back"].disabled = False
    Sim.gui["step_forward"].disabled = False
    Sim.gui["end"].disabled = False
    Sim.gui["frameslider"].disabled = False
    # update gui so that cables can be toggled
    Sim.gui["box_cables"].disabled = False

    # create glass cylinder for each generator
    for number, cyl in Sim.generators.items():
        #print(number, cyl, cyl.rating)
        Sim.generators_glass[number] = vp.cylinder(pos = cyl.pos,
                                                   radius = cyl.radius * 1.05,
                                                   axis=vp.vector(0, cyl.rating * Sim.factor["generators_h"] + Sim.base["generators_h"], 0),
                                                   color=vp.color.white,
                                                   opacity=Sim.tubes_opacity)
    # create glass cylinder for each storage
    for number, cyl in Sim.storages.items():
        print(number, cyl, cyl.rating)
        Sim.storages_glass[number] = vp.cylinder(pos=cyl.pos,
                                                 radius=cyl.radius * 1.05,
                                                 axis=vp.vector(0, cyl.rating * Sim.factor["storages_h"] + Sim.base["storages_h"], 0),
                                                 color=vp.color.white,
                                                 opacity=Sim.tubes_opacity)


    #print("middles:")
    for (i,j), disc in Sim.cables_middle.items():
        loading = Data.df[f"cable_loading_{i}_{j}"][Sim.i] # value from 0 to 100 ? (is percent?)
        loading_t = int(min(100, loading)) # restrict pie chart to 100, get value for texture
        #print(i,j, disc, loading)
        #points = [v + disc.pos + vp.vec(0, disc.axis.y,0) for v in Sim.pie_points]
        #Sim.pie_charts[(i,j)] = vp.curve(pos = points, color=vp.color.green, radius=Sim.base["middles_r"] * 0.4 )
        Sim.pie_charts[(i,j)] = vp.box(pos=disc.pos + vp.vector(0, disc.axis.y, 0),
                                       size=vp.vector(Sim.base["middles_r"]*2, Sim.base["middles_r"]/10, Sim.base["middles_r"]*2),
                                       texture=Sim.pietextures[loading_t])


    # free camera
    Sim.scene.userspin = True
    # make invisible: direct gold lines between nodes (the cables) and little pink cylinders between nodes (the sub-nodes)
    for d in (Sim.cables, Sim.sub_nodes):  # dictionaries # Sim.sub_cables
        for o in d.values():
            o.visible = False

    # turn all pink sub-cables into black shadows
    Sim.shortest_subcable = None
    for (i, j), curve in Sim.sub_cables.items():
        curve.color = vp.color.gray(0.33)
        # calculate shortest subcable distance
        pointlist = [d["pos"] for d in curve.slice(0, curve.npoints)]
        for n, point in enumerate(pointlist):
            if n == 0:
                continue
            distance = vp.mag(point - pointlist[n - 1])
            if Sim.shortest_subcable is None or distance < Sim.shortest_subcable:
                Sim.shortest_subcable = distance
    Sim.gui["bottomtext1"].text += f"shortest subcable length: {Sim.shortest_subcable}\n"

    # calculate pointlist and lengthlist for each sub-cable
    for (i, j), curve in Sim.sub_cables.items():
        # curve = Sim.sub_cables[(i, j)]
        pointlist = [d["pos"] for d in curve.slice(0, curve.npoints)]  # curve is lying on the floor
        total_length = 0
        length_list = []
        for k, pos in enumerate(pointlist):
            if k == 0:
                length_list.append(0)
            else:
                total_length += vp.mag(pointlist[k] - pointlist[k - 1])
                length_list.append(total_length)
        Sim.sub_cable_pointlist[(i, j)] = pointlist
        Sim.sub_cable_lengthlist[(i, j)] = length_list

    # update Sim.flying_arrows_length if necessary
    if Sim.base["flying_arrows_length"] < Sim.shortest_subcable:
        Sim.base["flying_arrows_length"] = Sim.shortest_subcable / 2
        Sim.gui["flying_arrows_length"].text = f"{Sim.shortest_subcable / 2:.2f}"

    # ---- start flying arrows
    for (i, j), curve in Sim.sub_cables.items():
        # print("create arrow for",i,j)
        pointlist = [d["pos"] for d in curve.slice(0, curve.npoints)]
        # print(pointlist)
        # print("pointlist:",pointlist)
        delta = 0
        overshoot = 0
        Sim.tubes_node[(i, j)] = []
        total_length = 0
        my_length = 0
        startpos = None
        for k, pos in enumerate(pointlist):
            if k == curve.npoints - 1:
                continue
            #if k == 0:
            startpos = vp.vector(pos.x, pos.y, pos.z)
            # k2 = k+1
            # if k2 == curve.npoints:
            #    k2 = 0
            pos2 = pointlist[k + 1]  # where arrow wants to fly to
            startpos += overshoot * vp.norm(pos2-pos)
            Sim.tubes_node[(i, j)].append(vp.cylinder(pos=pos,
                                                      axis=pos2 - pos,
                                                      opacity=Sim.tubes_opacity,
                                                      radius=Sim.base["cables_r"] + Sim.factor[
                                                          "cables_r"] * Data.cables_power_max * Sim.tubes_radius_factor + Sim.tubes_radius_delta,
                                                      ))
            total_length += vp.mag(pos2-pos)
            # start flying arrows TODO: hier weitermachen
            while my_length < total_length:
                FlyingArrow(i, j, k, True, pos=startpos, color=vp.color.orange, round=True)
                my_length += Sim.base["flying_arrows_length"] * Sim.base["flying_arrows_distance"]
                overshoot = my_length - total_length
                if overshoot < 0:
                    startpos += vp.norm(pos2-pos)* Sim.base["flying_arrows_length"] * Sim.base["flying_arrows_distance"]
                else:
                    break

    #  --- end flying arrows

    # --- start flying angles from generator to node ---
    #for gen_number, node_number in Data.generators.items():
    for node_number in Data.generators:
        gen_number = node_number
        generator = Sim.generators[gen_number]
        node = Sim.nodes[node_number]
        Sim.tubes_generator[gen_number] = vp.cylinder(pos=generator.pos,
                                                      axis=node.pos - generator.pos,
                                                      opacity=Sim.tubes_opacity,
                                                      radius=Sim.base["cables_r"] + Sim.factor[
                                                          "cables_r"] * Data.cables_power_max * Sim.tubes_radius_factor + Sim.tubes_radius_delta,
                                                      )
        startpos = vp.vector(generator.pos.x, generator.pos.y, generator.pos.z)
        #while vp.mag(startpos - node.pos) < (vp.mag(node.pos - load.pos) - load.radius - Sim.base["flying_arrows_length"] * Sim.base["flying_arrows_distance"]):
        while vp.mag(startpos - generator.pos) < (vp.mag(node.pos - generator.pos) - node.radius - Sim.base["flying_arrows_length"] * Sim.base["flying_arrows_distance"]):
            f = FlyingArrowFromGenerator(gen_number, pos=startpos, color=vp.color.yellow, round=True)
            startpos += vp.norm(f.axis) * Sim.base["flying_arrows_distance"] * Sim.base["flying_arrows_length"]

    # ---- start flying angles from node to load ------
    for node_number in Data.loads:  # it's a list because node_number == load_number
        load = Sim.loads[node_number]
        node = Sim.nodes[node_number]
        Sim.tubes_load[node_number] = vp.cylinder(pos=load.pos,
                                                  axis=node.pos - load.pos,
                                                  opacity=Sim.tubes_opacity,
                                                  radius=Sim.base["cables_r"] + Sim.factor[
                                                      "cables_r"] * Data.cables_power_max * Sim.tubes_radius_factor + Sim.tubes_radius_delta,
                                                  )
        startpos = vp.vector(node.pos.x, node.pos.y, node.pos.z)
        ###startpos = node.pos.clone() vectors can not be cloned
        while vp.mag(startpos - node.pos) < (vp.mag(node.pos - load.pos) - load.radius - Sim.base["flying_arrows_length"] * Sim.base["flying_arrows_distance"]):
            f = FlyingArrowToLoad(node_number, pos=startpos, color=vp.color.purple, round=True)
            startpos += vp.norm(f.axis) * Sim.base["flying_arrows_distance"] * Sim.base["flying_arrows_length"]


def layout_save():  # not a button anymore, therefore no parameter b. function get executed by widget_func_start_simulation()
    """save pos for each: generator, node, subnode, load, storage. Save pointlist for each sub_cable"""
    with open("clean_layout_data.txt", "w") as myfile:
        myfile.write("#storages\n")
        for i, sto in Sim.storages.items():
            myfile.write(f"{i} {sto.pos.x} {sto.pos.y} {sto.pos.z}\n")
        myfile.write("#generators\n")
        for i, gen in Sim.generators.items():
            myfile.write(f"{i} {gen.pos.x} {gen.pos.y} {gen.pos.z}\n")
        myfile.write("#loads\n")
        for i, loa in Sim.loads.items():
            myfile.write(f"{i} {loa.pos.x} {loa.pos.y} {loa.pos.z}\n")
        myfile.write("#nodes\n")
        for i, cyl in Sim.nodes.items():
            myfile.write(f"{i} {cyl.pos.x} {cyl.pos.y} {cyl.pos.z}\n")
        myfile.write("#curves\n")
        for (i, j), curve in Sim.sub_cables.items():
            for k in range(curve.npoints):
                point = curve.point(k)["pos"]
                myfile.write(f"{i} {j} {k} {point.x} {point.y} {point.z}\n")
        myfile.write("#middles\n")
        for (i, j), middle in Sim.cables_middle.items():
            myfile.write(f"{i} {j} {middle.pos.x} {middle.pos.y} {middle.pos.z}\n")
    print("file layout_data.txt is written")


def layout_load():
    points = {}
    # print("generators:", Sim.generators)
    """attempting to load from layout_data.txt if this file can be found"""
    try:
        with open("clean_layout_data.txt") as myfile:
            lines = myfile.readlines()
    except:
        print("problem with loading the file layout_data.txt  ... no info is loaded")
        return
    mode = None
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            mode = line[1:]
            continue
        # match mode:
        if mode is None:
            # case None:
            continue


        elif mode == "curves":
            i, j, k, x, y, z = [float(word) for word in line.split(" ")]
            i, j, k = int(i), int(j), int(k)
            points[(i, j, k)] = vp.vector(x, y, z)
            # the curves may have different number of points than originally
            # Sim.sub_cables[(i, j)].modify(k, pointpos)
            # if (i, j, k) in Sim.sub_nodes:
            #    Sim.sub_nodes[(i, j, k)].pos = pointpos
            # if k == int(Sim.number_of_sub_cables / 2):
            #    Sim.labels[f"cable {i}-{j}"].pos = pointpos
            # TODO: delete all cables and re-create cables and subdiscs from points[(i,j,k)]

        elif mode == "nodes":
            number, x, y, z = [float(word) for word in line.split(" ")]
            number = int(number)
            npos = vp.vector(x, y, z)
            Sim.nodes[number].pos = npos
            Sim.letters[f"node {number}"].pos = npos  # + Sim.nodes[number].axis + vp.vector(0, 1, 0)
            Sim.labels[f"node {number}"].pos = npos
            # node has attached generator?
            ###Data.generators = {}  # gen_number: node_number
            ###Data.nodes = {node_number: (x,z,gen_number,load_number)
            if number in Data.generators:
                #gen_number = Data.nodes[number][2]
                gen_number = number

                # if number in Sim.generator_lines:
                Sim.generator_lines[gen_number].modify(0, npos)
            if number in Sim.load_lines:
                Sim.load_lines[number].modify(0, npos)
            for (i, j), curve in Sim.cables.items():
                if i == number:
                    curve.modify(0, npos)
                if j == number:
                    curve.modify(1, npos)


        elif mode == "generators":
            number, x, y, z = [float(word) for word in line.split(" ")]
            number = int(number)
            gpos = vp.vector(x, y, z)
            Sim.generators[number].pos = gpos
            Sim.labels[f"generator {number}"].pos = gpos
            try:
                Sim.letters[f"generator {number}"].pos = gpos  # + Sim.generators[number].axis #+ vp.vector(0, 1, 0)
            except:
                print("problem with letter generator ", number)
            Sim.discs[number].pos = gpos
            Sim.pointer0[number].pos = gpos
            Sim.pointer1[number].pos = gpos
            Sim.generator_lines[number].modify(1, pos=gpos)  # 1 is the generator, 0 is the node
            # Sim.generator_lines[number].modify(0, pos=Sim.nodes[number].pos)
        elif mode == "loads":
            number, x, y, z = [float(word) for word in line.split(" ")]
            number = int(number)
            lpos = vp.vector(x, y, z)
            Sim.loads[number].pos = lpos
            Sim.labels[f"load {number}"].pos = lpos
            Sim.letters[f"load {number}"].pos = lpos + Sim.loads[number].axis
            Sim.load_lines[number].modify(1, pos=lpos)

        elif mode == "storages":
            number, x, y, z = [float(word) for word in line.split(" ")]
            number = int(number)
            spos = vp.vector(x,y,z)
            Sim.storages[number].pos = spos
            Sim.labels[f"storage {number}"].pos = spos
            Sim.letters[f"storage {number}"].pos = spos + Sim.storages[number].axis
            Sim.storage_lines[number].modify(1, pos=spos)



        elif mode == "middles":
            i, j, x, y, z = [float(word) for word in line.split(" ")]
            i, j = int(i), int(j)
            Sim.cables_middle[(i, j)].pos = vp.vector(x, y, z)
            Sim.labels[f"cable {i}-{j}"].pos = vp.vector(x, y, z)
            Sim.letters[f"cable {i}-{j}"].pos = vp.vector(x, y, z)
        else:
            print("unhandled value for mode in layout file:", mode)
    # deleting all sub-cables and sub-nodes and making them new from layout:
    # CLEAR all sub_cables, DELETE all sub-nodes
    for (i, j), cable in Sim.sub_cables.items():
        cable.clear()
    for (i, j, k), subnode in Sim.sub_nodes.items():
        subnode.visible = False
    Sim.sub_nodes = {}
    # fill cables with points
    for (i, j, k), pos in points.items():
        Sim.sub_cables[(i, j)].append(points[(i, j, k)])
    # create sub_nodes
    for (i, j, k), pos in points.items():
        cable = Sim.sub_cables[(i, j)]
        if any((k == 0, k == cable.npoints)):
            continue  # first and last point of curve has no sub-node

        subdisc = vp.cylinder(pos=pos, radius=Sim.base["nodes_r"] / 2, color=vp.color.magenta,
                              axis=vp.vector(0, Sim.base["nodes_r"] / 3, 0),
                              pickable=True)
        subdisc.number = (i, j, k)
        subdisc.what = "subnode"
        Sim.sub_nodes[(i, j, k)] = subdisc

    print("loading of layout data was sucessfull")


def hexcode_to_vector(hexcode):
    r = int(hexcode[1:3], base=16) / 256
    g = int(hexcode[3:5], base=16) / 256
    b = int(hexcode[5:7], base=16) / 256
    return vp.vector(r, g, b)


def hexcode_from_vector(rgbvector):
    # r,g,b in vector must be between 0 and 1
    r, g, b = rgbvector.x, rgbvector.y, rgbvector.z
    red = int(255 * r)
    green = int(255 * g)
    blue = int(255 * b)
    result = "#"
    for color in (red, green, blue):
        if color < 16:
            result += "0"
            result += hex(color)[-1:]
        else:
            result += hex(color)[-2:]
    return result


def is_colorstring_valid(colorstring):
    if any((len(colorstring) != 7, colorstring[0] != "#",
            len([x for x in colorstring[1:] if x not in "0123456789abcdef"]) > 0)):
        # vp.input(f"{colorstring} is not a correct hex-value for a color.\nFirst char must be a #.\nNext two chars must be a hex value for red (00 - ff).\nNext two chars must be a hex value for green (00-ff).\nThe last two chars must be a hex value for blue (00-ff).\nPlease press OK and try again.")
        print("invalid colorstring:", colorstring)
        return False
    return True


def widget_func_color_crit_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_crit_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return

    Sim.colordict["crit_low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text

    end_position = full_text.find("    crit low") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position+1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:",Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_too_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_too_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["too_low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    too low") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    low") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_good_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_good_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["good_low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    good low") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_good_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_good_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["good_high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    good high") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    high    ") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_too_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_too_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["too_high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    too high") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def widget_func_color_crit_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_crit_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["crit_high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    crit high") - 4
    start_position = end_position - 6
    # print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    # print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


# ------ nodes ------------
def widget_func_color_crit_low_nodes(b):
    Sim.colors["crit_low_nodes"] = b.number
    update_stuff()


def widget_func_color_too_low_nodes(b):
    Sim.colors["too_low_nodes"] = b.number
    update_stuff()


def widget_func_color_low_nodes(b):
    Sim.colors["low_nodes"] = b.number
    update_stuff()


def widget_func_color_good_low_nodes(b):
    Sim.colors["good_low_nodes"] = b.number
    update_stuff()


def widget_func_color_good_high_nodes(b):
    Sim.colors["good_high_nodes"] = b.number
    update_stuff()


def widget_func_color_high_nodes(b):
    Sim.colors["high_nodes"] = b.number
    update_stuff()


def widget_func_color_too_high_nodes(b):
    Sim.colors["too_high_nodes"] = b.number
    update_stuff()


def widget_func_color_crit_high_nodes(b):
    Sim.colors["crit_high_nodes"] = b.number
    update_stuff()


# ------- loads -----

def widget_func_color_crit_low_loads(b):
    Sim.colors["crit_low_loads"] = b.number
    update_stuff()


def widget_func_color_too_low_loads(b):
    Sim.colors["too_low_loads"] = b.number
    update_stuff()


def widget_func_color_low_loads(b):
    Sim.colors["low_loads"] = b.number
    update_stuff()


def widget_func_color_good_low_loads(b):
    Sim.colors["good_low_loads"] = b.number
    update_stuff()


def widget_func_color_good_high_loads(b):
    Sim.colors["good_high_loads"] = b.number
    update_stuff()


def widget_func_color_high_loads(b):
    Sim.colors["high_loads"] = b.number
    update_stuff()


def widget_func_color_too_high_loads(b):
    Sim.colors["too_high_loads"] = b.number
    update_stuff()


def widget_func_color_crit_high_loads(b):
    Sim.colors["crit_high_loads"] = b.number
    update_stuff()


# ------- generators ----------

# def widget_func_color_crit_low_generators(b):
#    Sim.colors["crit_low_generators"] = b.number
# def widget_func_color_too_low_generators(b):
#    print(b.number)
# def widget_func_color_low_generators(b):
#    print(b.number)


def widget_func_color_crit_low_generators(b):
    Sim.colors["crit_low_generators"] = b.number
    update_stuff()


def widget_func_color_too_low_generators(b):
    Sim.colors["too_low_generators"] = b.number
    update_stuff()


def widget_func_color_low_generators(b):
    Sim.colors["low_generators"] = b.number
    update_stuff


def widget_func_color_good_low_generators(b):
    Sim.colors["good_low_generators"] = b.number
    update_stuff()


def widget_func_color_good_high_generators(b):
    Sim.colors["good_high_generators"] = b.number
    update_stuff()


def widget_func_color_high_generators(b):
    Sim.colors["high_generators"] = b.number
    update_stuff()


def widget_func_color_too_high_generators(b):
    Sim.colors["too_high_generators"] = b.number
    update_stuff()


def widget_func_color_crit_high_generators(b):
    Sim.colors["crit_high_generators"] = b.number
    update_stuff()


# ------- generator angle -------


def widget_func_color_crit_low_generators_angle(b):
    Sim.colors["crit_low_generators_angle"] = b.number
    update_stuff()


def widget_func_color_too_low_generators_angle(b):
    Sim.colors["too_low_generators_angle"] = b.number
    update_stuff()


def widget_func_color_low_generators_angle(b):
    Sim.colors["low_generators_angle"] = b.number
    update_stuff()


def widget_func_color_good_low_generators_angle(b):
    Sim.colors["good_low_generators_angle"] = b.number
    update_stuff()


def widget_func_color_good_high_generators_angle(b):
    Sim.colors["good_high_generators_angle"] = b.number
    update_stuff()


def widget_func_color_high_generators_angle(b):
    Sim.colors["high_generators_angle"] = b.number
    update_stuff()


def widget_func_color_too_high_generators_angle(b):
    Sim.colors["too_high_generators_angle"] = b.number
    update_stuff()


def widget_func_color_crit_high_generators_angle(b):
    Sim.colors["crit_high_generators_angle"] = b.number
    update_stuff()


# ---- cables ----

def widget_func_color_crit_low_cables(b):
    Sim.colors["crit_low_cables"] = b.number
    update_stuff()


def widget_func_color_too_low_cables(b):
    Sim.colors["too_low_cables"] = b.number
    update_stuff()


def widget_func_color_low_cables(b):
    Sim.colors["low_cables"] = b.number
    update_stuff()


def widget_func_color_good_low_cables(b):
    Sim.colors["good_low_cables"] = b.number
    update_stuff()


def widget_func_color_good_high_cables(b):
    Sim.colors["good_high_cables"] = b.number
    update_stuff()


def widget_func_color_high_cables(b):
    Sim.colors["high_cables"] = b.number
    update_stuff()


def widget_func_color_too_high_cables(b):
    Sim.colors["too_high_cables"] = b.number
    update_stuff()


def widget_func_color_crit_high_cables(b):
    Sim.colors["crit_high_cables"] = b.number
    update_stuff()


# --------- losses ------------

def widget_func_color_too_low_losses(b):
    print(b.number)


def widget_func_color_low_losses(b):
    print(b.number)


def widget_func_color_losses(b):
    print(b.number)


def widget_func_color_high_losses(b):
    print(b.number)


def widget_func_color_too_high_losses(b):
    print(b.number)


def create_widgets():
    # ---- widgets above window in title area -------
    # Sim.scene.append_to_title("mode:")
    # Sim.gui["arrange"] = vp.button(bind=widget_func_arrange, text="arrange", pos=Sim.scene.title_anchor, disabled=True)
    # Sim.gui["layout_save"] = vp.button(bind=widget_func_layout_save, text="save layout", pos=Sim.scene.title_anchor,
    #                                   disabled=False)
    # Sim.gui["testflip"] = vp.button(bind=widget_func_testflip, text="flip", pos=Sim.scene.title_anchor)
    Sim.gui["subnodes_add"] = vp.button(bind=widget_func_subnodes_add, text="+", pos=Sim.scene.title_anchor,
                                        disabled=True)
    Sim.gui["subnodes_remove"] = vp.button(bind=widget_func_subnodes_remove, text="-", pos=Sim.scene.title_anchor,
                                           disabled=True)
    Sim.gui["mode"] = vp.wtext(pos=Sim.scene.title_anchor, text=f"{Sim.mode}")
    Sim.gui["simulation"] = vp.button(bind=widget_func_start_simulation, text="start simulation",
                                      pos=Sim.scene.title_anchor,
                                      disabled=False)
    Sim.gui["create_curves"] = vp.button(pos=Sim.scene.title_anchor,
                                         bind=widget_func_create_curves,
                                         text="create_curves",
                                         disabled=True)
    Sim.gui["restart"] = vp.button(bind=widget_func_restart, text="|<", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["step_back"] = vp.button(bind=widget_func_step_back, text="<", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["play"] = vp.button(bind=widget_func_play, text="play >", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["step_forward"] = vp.button(bind=widget_func_step_forward, text=">", pos=Sim.scene.title_anchor,
                                        disabled=True)
    Sim.gui["end"] = vp.button(bind=widget_func_end, text=">|", pos=Sim.scene.title_anchor, disabled=True)
    # Sim.button_end = vp.button(bind=widget_func_end, text=">|", pos=Sim.scene.title_anchor)

    # Sim.label1 = vp.wtext(pos=Sim.scene.title_anchor, text="---hallo---")
    # Sim.scene.append_to_title("\n")
    Sim.gui[" timeframe"] = vp.wtext(pos=Sim.scene.title_anchor, text="timeframe:  ")
    Sim.gui["frameslider"] = vp.slider(pos=Sim.scene.title_anchor, bind=widget_func_time_slider, min=0,
                                       max=len(Data.df),
                                       length=600, step=1, disabled=True)
    Sim.gui["label_frame"] = vp.wtext(pos=Sim.scene.title_anchor, text=f"0/0 time: {Data.df['time'][Sim.i]}")
    # Sim.gui["label_last_frame"] = vp.wtext(pos=Sim.scene.title_anchor, text=f"/{len(Data.df)}")
    Sim.gui["quit"] = vp.button(pos=Sim.scene.title_anchor,
                                bind=widget_func_quit,
                                text="quit")
    Sim.scene.append_to_title("\n")

    # Sim.scene.append_to_caption("<code>losses:      |  </code>")
    # Sim.gui["color_too_low_losses"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_low_losses, width=100,
    #                                            type="numeric", text="-10.0")  # TODO : get default value
    # Sim.scene.append_to_caption("<code> | </code>")
    # Sim.gui["color_low_losses"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_low_losses, width=100,
    #                                        type="numeric", text="-5.0")  # TODO : get default value
    # Sim.scene.append_to_caption("<code> | </code>")
    # Sim.gui["color_losses"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_losses, width=100,
    #                                    type="numeric", text="0.0")  # TODO : get value
    # Sim.scene.append_to_caption("<code> | </code>")
    # Sim.gui["color_high_losses"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_high_losses, width=100,
    #                                         type="numeric", text="5.0")  # TODO : get value
    # Sim.scene.append_to_caption("<code> | </code>")
    # Sim.gui["color_too_high_losses"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_high_losses,
    #                                             width=100,
    #                                             type="numeric", text="10.0")  # TODO : get value
    # Sim.scene.append_to_caption("<code>| </code>")
    # Sim.gui["min_max_losses"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="? / ?")
    # Sim.scene.append_to_caption("\n")
    # Sim.scene.append_to_caption("<code>  gliders:   |  </code>")
    # Sim.gui["box_gliders"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=False, disabled=True,
    #                              bind=widget_func_toggle_gliders)
    Sim.scene3.append_to_caption("\n")
    # -------------------------------------------------------
    Sim.scene3.append_to_caption("load presets: ")
    #Sim.gui["preset"] = vp.button(pos=Sim.scene3.caption_anchor,text=" default ", bind=widget_func_load_preset_default, disabled=True)
    Sim.gui["preset"] = vp.menu(pos=Sim.scene3.caption_anchor,bind=widget_func_load_preset, choices=["none", "default","Yokoyama A", "Yokoyama B", "Yokoyama C", "Yokoyama D"], index=0, disabled=True)
    #Sim.gui["preset_A"] = vp.button(pos=Sim.scene3.caption_anchor, text=" Yokoyama A ", bind=widget_func_load_preset_A, disabled=True)
    #Sim.gui["preset_B"] = vp.button(pos=Sim.scene3.caption_anchor, text=" Yokoyama B ", bind=widget_func_load_preset_B, disabled=True)
    #Sim.gui["preset_C"] = vp.button(pos=Sim.scene3.caption_anchor, text=" Yokoyama C ", bind=widget_func_load_preset_C, disabled=True)
    Sim.scene3.append_to_caption("map texture: ")
    Sim.gui["map"] = vp.menu(pos=Sim.scene3.caption_anchor, bind=widget_func_map, choices=["google map", "borders", "nothing"], index=0)


    Sim.scene3.append_to_caption("\n")
    #Sim.scene3.append_to_caption("save presets: ")

    #Sim.scene3.append_to_caption("\n")
    # ------------
    Sim.scene3.append_to_caption(
        "|  entity   |  visible  |       letter               |       label       | decimals |  radius factor  | radius base   | height factor | height base  | dynamic color | set camera to position: ")
    Sim.gui["camerapos1"] = vp.button(pos=Sim.scene3.caption_anchor, text=" original ", bind=widget_func_camera1)
    Sim.gui["camerapos2"] = vp.button(pos=Sim.scene3.caption_anchor, text=" A ", bind=widget_func_camera2, disabled=True)
    Sim.gui["camerapos3"] = vp.button(pos=Sim.scene3.caption_anchor, text=" B ", bind=widget_func_camera3, disabled=True)
    Sim.gui["camerapos4"] = vp.button(pos=Sim.scene3.caption_anchor, text=" C ", bind=widget_func_camera4, disabled=True)
    Sim.scene3.append_to_caption("camera goto:")
    node_numbers = [f"{n} {Data.node_names[n]}" for n in Sim.nodes]
    node_numbers.insert(0, "center")
    Sim.gui["goto"] = vp.menu(pos=Sim.scene3.caption_anchor,
                              selected="center",
                              bind=widget_func_camera_goto,
                              choices=node_numbers)
    Sim.scene3.append_to_caption("\n")
    Sim.scene3.append_to_caption("<code>Nodes:       | </code>")
    Sim.gui["box_node"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=True,
                                      bind=widget_func_toggle_nodes)
    #Sim.gui["box_node_letter"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=True,
    #                                         bind=widget_func_toggle_nodes_letters)
    Sim.gui["menu_node_letter"] = vp.menu(bind=widget_func_toggle_nodes_letters,
                                          choices=["none","names","numbers","both"],
                                          index=1,
                                          pos=Sim.scene3.caption_anchor)
    #Sim.gui["box_node_labels"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=False,
    #                                         bind=widget_func_toggle_nodes_labels)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["menu_node_labels"] = vp.menu(bind=widget_func_toggle_nodes_labels,
                                          choices = ["none", "Volt"],
                                          index=0,
                                          pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["winput_decimals_node"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_nodes_decimal,
                                                width=25,
                                                type="numeric",
                                                text="1")
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["nodes_factor_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_nodes_factor_r, width=50,
                                          # prompt="nodes:",       # prompt does not work with python yet
                                          type="numeric", text=f"{Sim.factor['nodes_r']}")
    Sim.scene3.append_to_caption("<code>       | </code>")
    Sim.gui["nodes_base_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_nodes_base_r, width=50,
                                        # prompt="nodes:",       # prompt does not work with python yet
                                        type="numeric", text=f"{Sim.base['nodes_r']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["nodes_factor_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_nodes_factor_h, width=50,
                                          # prompt="nodes:",       # prompt does not work with python yet
                                          type="numeric", text=f"{Sim.factor['nodes_h']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["nodes_base_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_nodes_base_h, width=50,
                                        # prompt="nodes:",       # prompt does not work with python yet
                                        type="numeric", text=f"{Sim.base['nodes_h']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_nodes"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="",
                                               checked=Sim.dynamic_colors["nodes"],
                                               bind=widget_func_toggle_dynamic_nodes)
    Sim.scene3.append_to_caption(f"<code>{Data.nodes_min:.2f}/{Data.nodes_max:.2f}</code>")
    Sim.scene3.append_to_caption("<code>           | </code>save camera position to:               ")
    Sim.gui["save_camerapos2"] = vp.button(pos=Sim.scene3.caption_anchor, text=" A ", bind=widget_func_save_camera2,
                                           disabled=False)
    Sim.gui["save_camerapos3"] = vp.button(pos=Sim.scene3.caption_anchor, text=" B ", bind=widget_func_save_camera3,
                                           disabled=True)
    Sim.gui["save_camerapos4"] = vp.button(pos=Sim.scene3.caption_anchor, text=" C ", bind=widget_func_save_camera4,
                                           disabled=True)

    Sim.scene3.append_to_caption("\n")
    # --------------------------------
    Sim.scene3.append_to_caption("<code>Storages:    | </code>")
    Sim.gui["box_storages"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=True,
                                        disabled=True,
                                        bind=widget_func_toggle_storages)
    #Sim.gui["box_storages_letter"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=True,
    #                                           bind=widget_func_toggle_storages_letters)
    Sim.gui["menu_storages_letter"] = vp.menu(bind=widget_func_toggle_storages_letters,
                                          choices=["none","names","numbers","both"],
                                          index=1,
                                          pos=Sim.scene3.caption_anchor)
    #Sim.gui["box_storages_labels"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=False,
    #                                           bind=widget_func_toggle_storages_labels)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["menu_storage_labels"] = vp.menu(bind=widget_func_toggle_storages_labels,
                                          choices=["none", "p", "loading"],
                                          index=0,
                                          pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["winput_decimals_storage"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_storage_decimal,
                                                width=25,
                                                type="numeric",
                                                text="1")
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["storages_factor_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_storages_factor_r, width=50,
                                           # prompt="nodes:",       # prompt does not work with python yet
                                           type="numeric", text=f"{Sim.factor['storages_r']}")
    Sim.scene3.append_to_caption("<code>       | </code>")
    Sim.gui["storages_base_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_storages_base_r, width=50,
                                         # prompt="nodes:",       # prompt does not work with python yet
                                         type="numeric", text=f"{Sim.base['storages_r']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["storages_factor_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_storages_factor_h, width=50,
                                           # prompt="nodes:",       # prompt does not work with python yet
                                           type="numeric",
                                           text=f"{Sim.factor['storages_h']}")  # disabled does not work for winput
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["storages_base_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_storages_base_h, width=50,
                                         # prompt="nodes:",       # prompt does not work with python yet
                                         type="numeric",
                                         text=f"{Sim.base['storages_h']}")  # disabled does not work for winput

    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_storages"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="",
                                                checked=Sim.dynamic_colors["storages"],
                                                bind=widget_func_toggle_dynamic_storages)
    Sim.scene3.append_to_caption(f"<code>{Data.cables_power_min:.2f}/{Data.cables_power_max:.2f}</code>")
    Sim.scene3.append_to_caption("<code>      |  </code>camera pitch: ")
    Sim.gui["camera_pitch"] = vp.wtext(pos=Sim.scene3.caption_anchor, text=f"{Sim.camera_pitch:.2f}")
    Sim.gui["camera_pitch_slider"] = vp.slider(pos=Sim.scene3.caption_anchor, bind=widget_func_camera_pitch, min=90,
                                               max=180, value=90, length=300)
    Sim.scene3.append_to_caption("\n")
    # --------------------------------

    Sim.scene3.append_to_caption("<code>Cables:      | </code>")
    Sim.gui["box_cables"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=True,
                                        disabled=True,
                                        bind=widget_func_toggle_cables)
    #Sim.gui["box_cables_letter"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=True,
    #                                           bind=widget_func_toggle_cable_letters)
    Sim.gui["menu_cables_letter"] = vp.menu(bind=widget_func_toggle_cable_letters,
                                          choices=["none","names","numbers","both"],
                                          index=1,
                                          pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    #Sim.gui["box_cables_labels"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=False,
    #                                           bind=widget_func_toggle_cable_labels)
    Sim.gui["menu_cables_labels"] = vp.menu(pos=Sim.scene3.caption_anchor,
                                            choices=["none", "p", "loading", "p + loading", "mva"],
                                            bind=widget_func_toggle_cable_labels,
                                            index=0,)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["winput_decimals_cable"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_cable_decimal,
                                                width=25,
                                                type="numeric",
                                                text="1")
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["cables_factor_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_cables_factor_r, width=50,
                                           # prompt="nodes:",       # prompt does not work with python yet
                                           type="numeric", text=f"{Sim.factor['cables_r']}")
    Sim.scene3.append_to_caption("<code>       | </code>")
    Sim.gui["cables_base_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_cables_base_r, width=50,
                                         # prompt="nodes:",       # prompt does not work with python yet
                                         type="numeric", text=f"{Sim.base['cables_r']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["cables_factor_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_cables_factor_h, width=50,
                                           # prompt="nodes:",       # prompt does not work with python yet
                                           type="numeric",
                                           text=f"{Sim.factor['cables_h']}")  # disabled does not work for winput
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["cables_base_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_cables_base_h, width=50,
                                         # prompt="nodes:",       # prompt does not work with python yet
                                         type="numeric",
                                         text=f"{Sim.base['cables_h']}")  # disabled does not work for winput

    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_cables"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="",
                                                checked=Sim.dynamic_colors["cables"],
                                                bind=widget_func_toggle_dynamic_cables)
    Sim.scene3.append_to_caption(f"<code>{Data.cables_power_min:.2f}/{Data.cables_power_max:.2f}</code>")
    #Sim.scene3.append_to_caption("<code>      |  </code>camera pitch: ")
    #Sim.gui["camera_pitch"] = vp.wtext(pos=Sim.scene3.caption_anchor, text=f"{Sim.camera_pitch:.2f}")
    #Sim.gui["camera_pitch_slider"] = vp.slider(pos=Sim.scene3.caption_anchor, bind=widget_func_camera_pitch, min=90,
    #                                           max=180, value=90, length=300)
    Sim.scene3.append_to_caption("\n")
    # ------------------------------------------------------------
    # Sim.scene3.append_to_caption("<code>Losses:      | </code>")
    # Sim.gui["box_losses"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=False,
    #                                    disabled=True, bind=widget_func_toggle_losses)
    # Sim.scene3.append_to_caption("<code>     | </code>")  # because no labels for losses (it's in the cable lable)
    # Sim.gui["factor_losses"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_factor_losses, width=50,
    #                                     type="numeric", text="1.0")
    # Sim.scene3.append_to_caption("<code> | </code>\n")
    # --------------------------------------
    Sim.scene3.append_to_caption("<code>Generators:  | </code>")
    Sim.gui["box_generator"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=True,
                                           bind=widget_func_toggle_generators)
    #Sim.gui["box_generator_letter"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=True,
    #                                              bind=widget_func_toggle_generator_letters)
    Sim.gui["menu_generator_letter"] = vp.menu(bind=widget_func_toggle_generator_letters,
                                               choices=["none", "names", "numbers", "both"],
                                               index=1,
                                               pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    #Sim.gui["box_generator_labels"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=False,
    #                                              bind=widget_func_toggle_generator_labels)
    Sim.gui["menu_generator_labels"] = vp.menu(bind=widget_func_toggle_generator_labels,
                                                choices=["none", "p", "angle", "p+angle", "loading"],
                                                index=0,
                                                pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["winput_decimals_generator"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_generator_decimal,
                                                width=25,
                                                type="numeric",
                                                text="1")
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["generators_factor_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_generators_factor_r,
                                               width=50,
                                               # prompt="generators:", # prompt does not work with python yet
                                               type="numeric", text=f"{Sim.factor['generators_r']}")
    Sim.scene3.append_to_caption("<code>       | </code>")
    Sim.gui["generators_base_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_generators_base_r, width=50,
                                             # prompt="generators:", # prompt does not work with python yet
                                             type="numeric", text=f"{Sim.base['generators_r']}")

    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["generators_factor_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_generators_factor_h,
                                               width=50,
                                               # prompt="generators:", # prompt does not work with python yet
                                               type="numeric", text=f"{Sim.factor['generators_h']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["generators_base_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_generators_base_h, width=50,
                                             # prompt="generators:", # prompt does not work with python yet
                                             type="numeric", text=f"{Sim.base['generators_h']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_generators"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="",
                                                    checked=Sim.dynamic_colors["generators"],
                                                    bind=widget_func_toggle_dynamic_generators)
    Sim.scene3.append_to_caption(f"<code>{Data.generators_power_min:.2f}/{Data.generators_power_max:.2f}</code>")
    # Sim.scene3.append_to_caption("<code>      | </code>\n")


    Sim.scene3.append_to_caption("\n")

    # -------------------------------------------------------
    Sim.scene3.append_to_caption("<code>Loads:       | </code>")
    Sim.gui["box_loads"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=True,
                                       bind=widget_func_toggle_loads)
    #Sim.gui["box_loads_letter"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=True,
    #                                          bind=widget_func_toggle_loads_letters)
    Sim.gui["menu_loads_letter"] = vp.menu(bind=widget_func_toggle_loads_letters,
                                           choices=["none", "names", "numbers", "both"],
                                           index=1,
                                           pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    #Sim.gui["box_loads_labels"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> | </code>", checked=False,
    #                                          bind=widget_func_toggle_loads_labels)
    Sim.gui["menu_loads_labels"] = vp.menu(bind=widget_func_toggle_loads_labels,
                                           choices=["none", "p"],
                                           index=0,
                                           pos=Sim.scene3.caption_anchor)
    Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["winput_decimals_load"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                 bind=widget_func_load_decimal,
                                                 width=25,
                                                 type="numeric",
                                                 text="1")
    Sim.scene3.append_to_caption("<code>      | </code>")
    # Sim.scene3.append_to_caption("<code> | </code>")
    Sim.gui["loads_factor_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_loads_factor_r, width=50,
                                          # prompt="generators:", # prompt does not work with python yet
                                          type="numeric", text=f"{Sim.factor['loads_r']}")
    Sim.scene3.append_to_caption("<code>       | </code>")
    Sim.gui["loads_base_r"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_loads_base_r, width=50,
                                        # prompt="generators:", # prompt does not work with python yet
                                        type="numeric", text=f"{Sim.base['loads_r']}")

    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["loads_factor_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_loads_factor_h, width=50,
                                          # prompt="generators:", # prompt does not work with python yet
                                          type="numeric", text=f"{Sim.factor['loads_h']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["loads_base_h"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_loads_base_h, width=50,
                                        # prompt="generators:", # prompt does not work with python yet
                                        type="numeric", text=f"{Sim.base['loads_h']}")
    Sim.scene3.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_loads"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="",
                                               checked=Sim.dynamic_colors["loads"],
                                               bind=widget_func_toggle_dynamic_loads)
    Sim.scene3.append_to_caption(f"<code>{Data.loads_min:.2f}/{Data.loads_max:.2f}</code>")
    Sim.scene3.append_to_caption("<code>      |  </code>camera angle: ")
    Sim.gui["camera_angle"] = vp.wtext(pos=Sim.scene3.caption_anchor, text=f"{Sim.camera_pitch:.2f}")
    # Sim.gui["camera_angle_slider"] = vp.slider(pos=Sim.scene3.caption_anchor, bind=widget_func_camera_angle, min=-180, max=180, value=0, length=300)
    Sim.gui["button_cw"] = vp.button(pos=Sim.scene3.caption_anchor, text="rotate clockwise", bind=widget_func_camera_cw)
    Sim.gui["button_ccw"] = vp.button(pos=Sim.scene3.caption_anchor, text="rotate couter clockwise",
                                      bind=widget_func_camera_ccw)
    Sim.scene3.append_to_caption("\n")
    # Sim.scene3.append_to_caption("<code>      | </code>\n")
    # ---------------------------------------------
    # -- - - -- -- - - - -
    Sim.scene3.append_to_caption("\nToggle:\n ")
    Sim.scene3.append_to_caption("<code>Generator angle: </code>")
    Sim.gui["box_generators_angle"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="", checked=True,
                                                  bind=widget_func_toggle_generators_angle)
    Sim.scene3.append_to_caption("<code> | cable shadow: </code>")
    Sim.gui["box_cable_shadow"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="", checked=True,
                                              # disabled=True,
                                              bind=widget_func_toggle_cable_shadow)
    Sim.scene3.append_to_caption("<code> | arrow shadow: ")
    Sim.gui["box_arrow_shadow"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="", checked=True,
                                              # disabled=True,
                                              bind=widget_func_toggle_arrow_shadow)
    Sim.scene3.append_to_caption("<code> | grid: </code>")
    Sim.gui["box_grid"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="", checked=True,
                                      bind=widget_func_toggle_grid)
    Sim.scene3.append_to_caption("<code> | green cursor brackets: </code>")
    Sim.gui["box_brackets"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="", checked=True,
                                          bind=widget_func_toggle_cursor_brackets)
    Sim.scene3.append_to_caption("<code> | sloped cables: </code>")
    Sim.gui["box_sloped_cables"] = vp.checkbox(pos=Sim.scene3.caption_anchor,
                                               text="", checked=False,
                                               bind=widget_func_toggle_sloped_cables)
    Sim.scene3.append_to_caption("<code> | arrows fly during pause: </code>")
    Sim.gui["flying_while_paused"] = vp.checkbox(pos=Sim.scene3.caption_anchor,
                                                 text="", checked=False,
                                                 bind=widget_func_toggle_flying_while_paused)
    Sim.scene3.append_to_caption("<code> | arrows visible: </code>")
    Sim.gui["arrows_visible"] = vp.checkbox(pos=Sim.scene3.caption_anchor,
                                            text="", checked=True,
                                            bind=widget_func_toggle_arrows)
    Sim.scene3.append_to_caption("\n")
    # Sim.scene3.append_to_caption("<code>letters:     |  </code>")
    # Sim.gui["box_letters"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=True,
    #                                     bind=widget_func_toggle_letters)
    # Sim.scene3.append_to_caption("\n")
    # Sim.scene3.append_to_caption("<code>legend:      |  </code>")
    # Sim.gui["box_legend"] = vp.checkbox(pos=Sim.scene3.caption_anchor, text="<code> |  </code>", checked=False,
    #                                    bind=widget_func_toggle_legend)
    # Sim.scene3.append_to_caption("\n")
    Sim.scene3.append_to_caption("Flying Arrows:      | ")
    Sim.scene3.append_to_caption("length: ")
    Sim.gui["flying_arrows_length"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                text=f"{Sim.base['flying_arrows_length']}",
                                                type="numeric", width=50, bind=widget_func_flying_arrows_length)
    Sim.scene3.append_to_caption(" | speed (min): ")
    Sim.gui["flying_arrows_speed_min"] = vp.winput(pos=Sim.scene3.caption_anchor, text=f"{Sim.arrows_speed_min}",
                                                   type="numeric", width=50, bind=widget_func_flying_arrows_speed_min)
    Sim.scene3.append_to_caption(" | speed (max): ")
    Sim.gui["flying_arrows_speed_max"] = vp.winput(pos=Sim.scene3.caption_anchor, text=f"{Sim.arrows_speed_max}",
                                                   type="numeric", width=50, bind=widget_func_flying_arrows_speed_max)

    Sim.scene3.append_to_caption("\n")
    Sim.scene3.append_to_caption("Animation (full Simulation) Duration [seconds]: ")
    Sim.gui["animation_duration"] = vp.winput(pos=Sim.scene3.caption_anchor, text=f"{Sim.animation_duration}",
                                              type="numeric", width=50, bind=widget_func_animation_duration)
    Sim.scene3.append_to_caption(" Tube opacity (0-1): ")
    Sim.gui["tube_opacity"] = vp.wtext(pos=Sim.scene3.caption_anchor, text=f"{Sim.tubes_opacity:.2f} ")
    Sim.gui["tube_opacity_slider"] = vp.slider(bind=widget_func_tube_opacity, min=0.0, max=1.0,
                                               pos=Sim.scene3.caption_anchor,
                                               value=f"{Sim.tubes_opacity}", length=300)
    Sim.scene3.append_to_caption(" 'Glass half full' visible: ")
    Sim.gui["glass_visible"] = vp.checkbox(pos=Sim.scene3.caption_anchor,
                                           bind=widget_func_toggle_glass_visible,
                                           checked = True
                                           )

    Sim.scene3.append_to_caption("\n")
    # pie charts
    Sim.scene3.append_to_caption("Pie charts: visible: ")
    Sim.gui["pie_charts_visible"] = vp.checkbox(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_pie_charts_visible,
                                                checked=True,
                                                #text="visible"
                                                )
    Sim.scene3.append_to_caption(" size: ")
    Sim.gui["pie_charts_size"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                           type="numeric",
                                           text=str(Sim.base["middles_r"]*2),
                                           bind=widget_func_pie_chart_size,
                                           )

    Sim.scene3.append_to_caption(" legend height: ")
    h = Sim.canvas_height / len(Sim.legend)
    Sim.gui["legend_height"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                         type="numeric",
                                         text= str(h),
                                         bind=widget_func_legend_height,
                                         )
    Sim.scene3.append_to_caption("graph dimension in pixel: width: ")

    # changing width of graphs (dia) dynamically can only shrink them, but not expand them
    #Sim.gui["dia_width"] = vp.winput(pos=Sim.scene3.caption_anchor,
    #                                 bind=widget_func_dia_width,
    #                                   type="numeric",
    #                                   text=Sim.dia_width,
    #                                   )
    #Sim.scene3.append_to_caption(" text: ")
    #Sim.gui["pie_charts_text"] = vp.menu(pos=Sim.scene3.caption_anchor,
    #                                     bind=widget_func_pie_chart_text,
    #                                     choices = ["no label",
    #                                                "P",
    #                                                "MVA",
    #                                                "% loading",
    #                                                ],
    #                                     selected="no label",
    #                                     )
    Sim.scene3.append_to_caption("\n")
    # ------------------------
    # ---- widgets below window in caption area --------------
    t = "<code>entinity:    |    unit       |" \
        "<span style='color:#FFFFFF;font-weight: bold;background-color:#0000FF;'>    crit low   </span>|" \
        "<span style='font-weight: bold;background-color:#00FFFF;'>    too low    </span>|" \
        "<span style='font-weight: bold;background-color:#00FF80;'>    low         </span>|" \
        "<span style='font-weight: bold;background-color:#00FF00;'>    good low   </span>|" \
        "<span style='font-weight: bold;background-color:#00FF00;'>    good high   </span>|" \
        "<span style='font-weight: bold;background-color:#80FF00;'>    high       </span>|" \
        "<span style='font-weight: bold;background-color:#FFFF00;'>    too high   </span>|" \
        "<span style='font-weight: bold;color:#FFFFFF;background-color:#FF0000;'>    crit high   </span>|" \
        " min / max    </code>\n"
    Sim.gui["color_headings"] = vp.wtext(pos=Sim.scene3.caption_anchor, text=t)
    # ---------------------------
    Sim.scene3.append_to_caption("<code>color:       |      RGB      |</code>")
    Sim.gui["color_crit_low"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_crit_low,
                                          width=100,
                                          type="string", text=hexcode_from_vector(Sim.colordict["crit_low"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_low,
                                         width=100,
                                         type="string", text=hexcode_from_vector(Sim.colordict["too_low"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_low"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_low,
                                     width=100,
                                     type="string", text=hexcode_from_vector(Sim.colordict["low"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_good_low,
                                          width=100,
                                          type="string", text=hexcode_from_vector(Sim.colordict["good_low"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_good_high,
                                           width=100,
                                           type="string", text=hexcode_from_vector(Sim.colordict["good_high"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_high"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_high,
                                      width=100,
                                      type="string", text=hexcode_from_vector(Sim.colordict["high"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_high,
                                          width=100,
                                          type="string", text=hexcode_from_vector(Sim.colordict["too_high"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_crit_high,
                                           width=100,
                                           type="string", text=hexcode_from_vector(Sim.colordict["crit_high"]))
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.scene3.append_to_caption("\n")
    # ---------------------------
    Sim.scene3.append_to_caption("<code>nodes:       | Voltage pu    |</code>")
    Sim.gui["color_crit_low_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_crit_low_nodes,
                                                width=100,
                                                type="numeric", text="999")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_low_nodes,
                                               width=100,
                                               type="numeric", text="999")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_low_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_low_nodes, width=100,
                                           type="numeric", text="0.95")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_good_low_nodes,
                                                width=100,
                                                type="numeric", text="0.975")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_good_high_nodes,
                                                 width=100,
                                                 type="numeric", text="1.025")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_high_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_high_nodes, width=100,
                                            type="numeric", text="1.05")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_high_nodes,
                                                width=100,
                                                type="numeric", text="1.075")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_nodes"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_crit_high_nodes,
                                                 width=100,
                                                 type="numeric", text="1.1")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["min_max_nodes"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="? / ?")
    Sim.scene3.append_to_caption("\n")
    # --------------------------- per unit on 100MVA
    Sim.scene3.append_to_caption("<code>generators:  | loading % MVA |</code>")
    Sim.gui["color_crit_low_generators"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                     bind=widget_func_color_crit_low_generators,
                                                     width=100,
                                                     type="numeric", text="-100")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_generators"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                    bind=widget_func_color_too_low_generators,
                                                    width=100,
                                                    type="numeric", text="-100")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_low_generators"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_low_generators,
                                                width=100,
                                                type="numeric", text="0")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_generators"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                     bind=widget_func_color_good_low_generators, width=100,
                                                     type="numeric", text="60")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_generators"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                      bind=widget_func_color_good_high_generators, width=100,
                                                      type="numeric", text="70")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_high_generators"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_high_generators,
                                                 width=100,
                                                 type="numeric", text="80")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_generators"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                     bind=widget_func_color_too_high_generators,
                                                     width=100,
                                                     type="numeric", text="100")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_generators"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                      bind=widget_func_color_crit_high_generators,
                                                      width=100,
                                                      type="numeric", text="120")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["min_max_generators"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="? / ?")
    Sim.scene3.append_to_caption("\n")
    # -----------------------------------------------------
    Sim.scene3.append_to_caption("<code>    - angle: | ° Degrees     |</code>")
    Sim.gui["color_crit_low_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                           bind=widget_func_color_crit_low_generators_angle, width=100,
                                                           type="numeric", text="0.9")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                          bind=widget_func_color_too_low_generators_angle, width=100,
                                                          type="numeric", text="0.925")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_low_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                      bind=widget_func_color_low_generators_angle, width=100,
                                                      type="numeric", text="0.95")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                           bind=widget_func_color_good_low_generators_angle, width=100,
                                                           type="numeric", text="0.975")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                            bind=widget_func_color_good_high_generators_angle,
                                                            width=100,
                                                            type="numeric", text="1.025")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_high_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                       bind=widget_func_color_high_generators_angle, width=100,
                                                       type="numeric", text="1.05")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                           bind=widget_func_color_too_high_generators_angle, width=100,
                                                           type="numeric", text="1.075")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_generators_angle"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                            bind=widget_func_color_crit_high_generators_angle,
                                                            width=100,
                                                            type="numeric", text="1.1")
    Sim.scene3.append_to_caption("<code>|</code>")

    Sim.gui["min_max_generators_angle"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="? / ?")
    Sim.scene3.append_to_caption("\n")
    # ----------------------------------------------------- actuals
    Sim.scene3.append_to_caption("<code>cables:      | loading % MVA |</code>")
    Sim.gui["color_crit_low_cables"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_crit_low_cables,
                                                 width=100,
                                                 type="numeric", text="-100")

    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_cables"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_color_too_low_cables, width=100,
                                                type="numeric", text="-100")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_low_cables"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                            bind=widget_func_color_low_cables, width=100,
                                            type="numeric", text="0")  #

    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_cables"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                 bind=widget_func_color_good_low_cables, width=100,
                                                 type="numeric", text="60")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_cables"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                  bind=widget_func_color_good_high_cables, width=100,
                                                  type="numeric", text="70")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_high_cables"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_high_cables,
                                             width=100,
                                             type="numeric", text="80")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_cables"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_high_cables,
                                                 width=100,
                                                 type="numeric", text="100")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_cables"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                  bind=widget_func_color_crit_high_cables,
                                                  width=100,
                                                  type="numeric", text="120")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["min_max_cables"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="? / ?")
    Sim.scene3.append_to_caption("\n")
    # ------------------------------------
    Sim.scene3.append_to_caption("<code>loads:       |       MW      |</code>")
    Sim.gui["color_crit_low_loads"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_crit_low_loads,
                                                width=100,
                                                type="numeric", text="0")

    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_loads"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                               bind=widget_func_color_too_low_loads, width=100,
                                               type="numeric", text="0")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_low_loads"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                           bind=widget_func_color_low_loads, width=100,
                                           type="numeric", text="0")  #

    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_loads"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                bind=widget_func_color_good_low_loads, width=100,
                                                type="numeric", text="0")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_loads"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                 bind=widget_func_color_good_high_loads, width=100,
                                                 type="numeric", text="2000")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_high_loads"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_high_loads,
                                            width=100,
                                            type="numeric", text="2000")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_loads"] = vp.winput(pos=Sim.scene3.caption_anchor, bind=widget_func_color_too_high_loads,
                                                width=100,
                                                type="numeric", text="2000")  #
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_loads"] = vp.winput(pos=Sim.scene3.caption_anchor,
                                                 bind=widget_func_color_crit_high_loads,
                                                 width=100,
                                                 type="numeric", text="2000")
    Sim.scene3.append_to_caption("<code>|</code>")
    Sim.gui["min_max_loads"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="? / ?")
    Sim.scene3.append_to_caption("\n")
    # ------------------------------------
    Sim.gui["bottomtext1"] = vp.wtext(pos=Sim.scene3.caption_anchor, text="")
    displaydict = {k: v for k, v in Data.__dict__.items() if any((k.endswith("_min"), k.endswith("_max")))}
    for k, v in displaydict.items():
        Sim.gui["bottomtext1"].text += f"{k}: {v}\n"
    # -----------------------
    Sim.gui["cursor"] = vp.label(text="mouse pos", pixel_pos=True, pos=vp.vector(10, 10, 0), color=vp.color.black,
                                 align="left", box=False, visible=True, opacity=0.5)
    Sim.gui["camera"] = vp.label(text="camera pos", pixel_pos=True, pos=vp.vector(Sim.canvas_width, 10, 0),
                                 color=vp.color.black, align="right", box=False, visible=True, opacity=0.5)
    Sim.gui["version"] = vp.label(text=f"version:{VERSION}", pixel_pos=True,
                                  pos=vp.vector(Sim.canvas_width - 10, Sim.canvas_height - 10, 0), align="right",
                                  color=vp.color.black, box=False, opacity=0)
    # Sim.gui["help1"] = vp.label(text="click on a node, hold down the left mouse button and move the mouse to drag the node\n"
    #                                 "use mousewheel to zoom\n"
    #                                 "pan the camera by pressing down the SHIFT key and pressing the left mouse button down (not on a node) and moving the mouse\n",
    #                            pixel_pos=True, pos=vp.vector(10, Sim.canvas_height-10,0), color=vp.color.black, align="left", box=False, visible=True, opacity=0)
    Sim.gui["help2"] = vp.label(text="center of screen", pixel_pos=True, pos=vp.vector(10, Sim.canvas_height - 10, 0),
                                color=vp.color.green, align="left", box=False, visible=True, opacity=0)
    Sim.gui["help3"] = vp.label(text="no data", pixel_pos=True, pos=vp.vector(10, Sim.canvas_height - 30, 0),
                                color=vp.color.green, align="left", box=False, visible=False, opacity=0)
    Sim.gui["bracket_left"] = vp.label(text="[", pos=Sim.center, xoffset=-20, height=48, visible=True,
                                       color=vp.color.green, opacity=0, line=False, box=False)
    Sim.gui["bracket_right"] = vp.label(text="]", pos=Sim.center, xoffset=20, height=48, visible=True,
                                        color=vp.color.green, opacity=0, line=False, box=False)
    # legend:


def mousebutton_down():
    if Sim.mode == "arrange":
        # ------------- arrange mode ------------------
        Sim.selected_object = Sim.scene.mouse.pick
        if Sim.selected_object is None:
            Sim.dragging = False
            Sim.gui["bracket_left"].visible = False
            Sim.gui["bracket_right"].visible = False
            Sim.gui["help2"].visible = False
            Sim.gui["subnodes_add"].disabled = True
            Sim.gui["subnodes_remove"].disabled = True
        else:
            Sim.dragging = True
            Sim.gui["bracket_left"].pos = Sim.selected_object.pos
            Sim.gui["bracket_right"].pos = Sim.selected_object.pos
            Sim.gui["bracket_left"].visible = True
            Sim.gui["bracket_right"].visible = True

            Sim.gui["help2"].visible = True
            Sim.gui["help2"].text = f"{Sim.selected_object.what} {Sim.selected_object.number}"
            if Sim.selected_object.what == "subnode":
                Sim.gui["help2"].text += " press [+] or [-] buttons above to add or remove subnodes."
                Sim.gui["subnodes_add"].disabled = False
                Sim.gui["subnodes_remove"].disabled = False
            else:
                Sim.gui["subnodes_add"].disabled = True
                Sim.gui["subnodes_remove"].disabled = True
    else:
        # ------- simulation mode ----
        # old_object = Sim.selected_object
        # Sim.selected_object = Sim.scene.mouse.pick
        if Sim.scene.mouse.pick is None:
            pass
        # if Sim.selected_object is None:
        # Sim.gui["bracket_left"].visible = False
        # Sim.gui["bracket_right"].visible = False
        # Sim.gui["help2"].visible = False
        else:
            try:
                what = Sim.scene.mouse.pick.what
            except:
                print("clicked on too difficult object:", Sim.scene.mouse.pick)
                return
            # number =Sim.scene.mouse.pick.number

            if what in ("generator", "node", "middle", "load"):
                Sim.selected_object = Sim.scene.mouse.pick
                Sim.gui["bracket_left"].pos = Sim.selected_object.pos
                Sim.gui["bracket_right"].pos = Sim.selected_object.pos
                if Sim.gui["box_brackets"].checked:
                    Sim.gui["bracket_left"].visible = True
                    Sim.gui["bracket_right"].visible = True
                Sim.gui["help2"].visible = True
                Sim.gui["help2"].text = f"{Sim.selected_object.what} {Sim.selected_object.number}"
                Sim.gui["help3"].visible = True
            # TODO: what is arrow or shadow arrow or something else
            if (Sim.mode == "simulation") and (
            not Sim.animation_running):  # simulation is paused, therefore no call to update_stuff, have to do it here
                so = Sim.selected_object
                if so is not None:
                    if so.what == "node":
                        Sim.gui["help3"].text = Sim.labels[f"node {so.number}"].text
                    elif so.what == "generator":
                        Sim.gui["help3"].text = Sim.labels[f"generator {so.number}"].text
                    elif so.what == "load":
                        Sim.gui["help3"].text = Sim.labels[f"load {so.number}"].text
                    elif so.what == "middle":
                        Sim.gui["help3"].text = Sim.labels[f"middle {so.number}"].text


def mousebutton_up():
    if Sim.mode != "arrange":
        return
    Sim.dragging = False
    Sim.selected_object = None


def mouse_move():
    if Sim.mode != "arrange":
        return

    if not Sim.dragging:
        return
    o = Sim.selected_object
    o.pos = vp.vector(Sim.scene.mouse.pos.x, 0, Sim.scene.mouse.pos.z)
    Sim.gui["bracket_left"].visible = False
    Sim.gui["bracket_right"].visible = False
    Sim.gui["help2"].visible = False
    # keep inside of grid
    # if not (-Sim.grid_max_x / 2 <= Sim.scene.mouse.pos.x <= Sim.grid_max_x / 2):
    #    o.pos.x = max(-Sim.grid_max_x / 2, o.pos.x)
    #    o.pos.x = min(Sim.grid_max_x / 2, o.pos.x)
    # if not (-Sim.grid_max_z / 2 <= Sim.scene.mouse.pos.z <= Sim.grid_max_z / 2):
    #    o.pos.z = max(-Sim.grid_max_z / 2, o.pos.z)
    #    o.pos.z = min(Sim.grid_max_z / 2, o.pos.z)
    # match o.what:
    if o.what == "node":
        # print("node dragged")
        Sim.labels[f"node {o.number}"].pos = o.pos
        Sim.letters[f"node {o.number}"].pos.x = o.pos.x
        Sim.letters[f"node {o.number}"].pos.z = o.pos.z
        # re-arrange all cables that are connected to this node
        i = o.number
        for (a, b), cable in Sim.cables.items():
            if a == i:
                cable.modify(0, pos=Sim.nodes[i].pos)
                cable.modify(1, pos=Sim.nodes[b].pos)
            if b == i:
                cable.modify(0, pos=Sim.nodes[a].pos)
                cable.modify(1, pos=Sim.nodes[i].pos)

        # sub-discs
        # how many now?

        for (i2, j2, k2), subdisc in Sim.sub_nodes.items():
            if (i2 != i) and (j2 != i):
                continue
            n = Sim.sub_cables[(i2, j2)].npoints
            start = Sim.nodes[i2].pos
            end = Sim.nodes[j2].pos
            diff = end - start
            mpos = start + diff / 2
            Sim.cables_middle[(i2, j2)].pos = mpos
            Sim.labels[f"cable {i2}-{j2}"].pos = mpos

            pointlist = []
            pointlist.append(start)
            for k in range(1, n):  # 6 subnodes
                p = start + k * vp.norm(diff) * vp.mag(diff) / (n - 1)  # divide by number of subcables
                if (i2, j2, k) not in Sim.sub_nodes:
                    continue
                Sim.sub_nodes[(i2, j2, k)].pos = p
                pointlist.append(p)
                # TODO: sub-optimal code, iterates more often then necessary over all subdiscs
                # if k == int(Sim.number_of_sub_cables / 2):
                #
            pointlist.append(end)
            for number, point in enumerate(pointlist):
                # print("number:", number, "points:", Sim.sub_cables[(i2,j2)].npoints)
                if Sim.sub_cables[(i2, j2)].npoints > number:
                    Sim.sub_cables[(i2, j2)].modify(number, pos=point)
                # TODO: last point?

        # exist connected generator?
        # find out generator number: Data.generators: {gen_number:node_number}
        #if o.number in Data.generators.values():
        if o.number in Data.generators:
            #gen_number = list({g for g in Data.generators if Data.generators[g] == o.number})[0]
            gen_number = o.number
            # print("node", o.number, "-connected to generator", gen_number)

            # if o.number in Sim.generator_lines.keys():
            #    Sim.generator_lines[o.number].modify(0, pos=o.pos)
            if gen_number in Sim.generator_lines.keys():
                Sim.generator_lines[gen_number].modify(0, pos=o.pos)
        # exist connected load ?
        if o.number in Sim.load_lines.keys():
            Sim.load_lines[o.number].modify(0, pos=o.pos)
        # exist connected storage ?
        if o.number in Sim.storage_lines.keys():
            Sim.storage_lines[o.number].modify(0, pos=o.pos)


    elif o.what == "generator":
        # connected node:
        node_number = o.number
        Sim.labels[f"generator {o.number}"].pos = o.pos
        Sim.letters[f"generator {o.number}"].pos.x = o.pos.x
        Sim.letters[f"generator {o.number}"].pos.z = o.pos.z
        # mouve both pointers and disc
        Sim.pointer0[o.number].pos = o.pos
        Sim.pointer1[o.number].pos = o.pos
        Sim.discs[o.number].pos = o.pos
        # update generator_line
        Sim.generator_lines[o.number].modify(1, pos=o.pos)
    elif o.what == "subnode":
        # change only the attached sub-cables
        i, j, k = o.number
        Sim.sub_cables[i, j].modify(k, pos=o.pos)
        # if k == int(Sim.number_of_sub_cables / 2):
        #    Sim.labels[f"cable {i}-{j}"].pos = o.pos
    elif o.what == "storage":
        Sim.labels[f"storage {o.number}"].pos = o.pos
        Sim.letters[f"storage {o.number}"].pos.x = o.pos.x
        Sim.letters[f"storage {o.number}"].pos.z = o.pos.z
        Sim.storage_lines[o.number].modify(1, pos=o.pos)

    elif o.what == "load":
        Sim.labels[f"load {o.number}"].pos = o.pos
        Sim.letters[f"load {o.number}"].pos.x = o.pos.x
        Sim.letters[f"load {o.number}"].pos.z = o.pos.z
        Sim.load_lines[o.number].modify(1, pos=o.pos)
    elif o.what == "middle":
        (i, j) = o.number
        # print("moving middle")
        Sim.labels[f"cable {i}-{j}"].pos = o.pos
        Sim.letters[f"cable {i}-{j}"].pos = o.pos

    else:
        pass  # something else got dragged
        # elif o.what == "subdisc":
        #    i,j,k = o.number
        #    for subdisc in Sim.sub_discs[i,j].values():


# def mouseclick(event):
#    Sim.selected_object = Sim.scene.mouse.pick

def create_stuff2_curves():
    # fill all those curves for xy diagrams
    # ============ frequency ===========
    #minmax_y = int(Data.frequency_max) + 1 - int(Data.frequency_min)
    minmax_x = int(Data.time_max) + 1 - int(Data.time_min)

    #Sim.graph_dia1
    #gdata = [(v.x, v.y) for v in fdata]
    gdata=list(zip(Data.df["time"],Data.df["frequency"]))
    gc = vp.gcurve(data=gdata, color=vp.color.red, graph=Sim.graph_dia1)


    #Sim.graph_dia2
    Sim.gui["node_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("VOLT_")]:
        node_number = int(col_name.split("_")[1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["node_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia2,
                                                        color=Sim.legend_nodes[node_number],
                                                        data=gdata)



    Sim.gui["load_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("load_power_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["load_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia3,
                                                    color=Sim.legend_nodes[node_number],
                                                    data=gdata)

    # print(Sim.gui["node_c"])
    Sim.gui["generator_angle_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("generator_angle_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["generator_angle_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia4,
                                                                   color=Sim.legend_nodes[node_number],
                                                                   data=gdata)


    Sim.gui["generator_power_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("generator_power_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["generator_power_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia5,
                                                                   color=Sim.legend_nodes[node_number],
                                                                   data=gdata)

    Sim.gui["generator_loading_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("generator_loading_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["generator_loading_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia6,
                                                                   color=Sim.legend_nodes[node_number],
                                                                   data=gdata)


    Sim.gui["storage_power_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("storage_power_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["storage_power_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia7,
                                                                     color=Sim.legend_nodes[node_number],
                                                                     data=gdata)


    Sim.gui["cable_loading_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("cable_loading_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["cable_loading_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia8,
                                                                     color=Sim.legend_nodes[node_number],
                                                                     data=gdata)


    Sim.gui["cable_power_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("cable_power_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["cable_power_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia9,
                                                                     color=Sim.legend_nodes[node_number],
                                                                     data=gdata)


    Sim.gui["storage_loading_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("storage_loading_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["storage_loading_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia10,
                                                                     color=Sim.legend_nodes[node_number],
                                                                     data=gdata)


    Sim.gui["storage_state_curves"] = {}  # node_number: curve
    for col_name in [name for name in Data.col_names if name.startswith("storage_state_")]:
        node_number = int(col_name.split("_")[-1])
        gdata = list(zip(Data.df["time"], Data.df[col_name]))
        Sim.gui["storage_state_curves"][node_number] = vp.gcurve(graph=Sim.graph_dia11,
                                                                     color=Sim.legend_nodes[node_number],
                                                                     data=gdata)


def create_stuff2():
    """create stuff (tachometer needles) inside canvas for network frequency and inside canvas for generator angles """
    Sim.scene_dia_needle_frequency.select()

    x= 0
    vp.cylinder(pos=vp.vector(x,0,0),radius=30, axis=vp.vector(0,0,1))
    Sim.gui["frequency_text"] = vp.label(pos=vp.vector(0,-10,0), text="50 Hz", color=vp.color.black, height=36,
                                     box=False, opacity=0)
    ##Sim.gui["time_text"] = vp.label(pos=vp.vector(0, -25,0), text="time: 0 sec", color=vp.vector(0,0.5,0), height=25,
    ##                                box=False, opacity=0, align="center")
    vp.label(pos=vp.vector(0,28,0), text="50.0", align="center", box=False, opacity=0, color=vp.color.black)
    vp.label(pos=vp.vector(-27,0,0), text="49.9", align="right", box=False, opacity=0, color=vp.color.black)
    vp.label(pos=vp.vector(27,0,0), text="50.1", align="left", box=False, opacity=0, color=vp.color.black)
    vp.label(pixel_pos=True, pos=vp.vector(Sim.dia_height*1.2 /2,10,0), align="center", box=False, text="network frequency", color=vp.color.black)

    Sim.needle_frequency = vp.arrow(pos=vp.vector(x,0,0), axis=vp.vector(0,25,0), color=vp.vector(0.25+ 0.2,0,1))

    # ----------- generator angles ------
    Sim.scene_dia_needle_angle.select()
    vp.cylinder(pos=vp.vector(x, 0, 0), radius=30, axis=vp.vector(0, 0, 1))
    vp.label(pixel_pos=True, pos=vp.vector(10, 10, 0), align="left", box=False,
             text="Gen. angles", color=vp.color.black)
    vp.label(pos=vp.vector(0, 28, 0), text="90°", align="center", box=False, opacity=0, color=vp.color.black)
    vp.label(pos=vp.vector(-27, 0, 0), text="180°", align="right", box=False, opacity=0, color=vp.color.black)
    vp.label(pos=vp.vector(28, 0, 0), text="0°", align="left", box=False, opacity=0, color=vp.color.black)
    vp.label(pos=vp.vector(0, -28, 0), text="-90°", align="center", box=False, opacity=0, color=vp.color.black)

    Sim.needles = {}
    for col_name in [name for name in Data.col_names if name.startswith("generator_angle_")]:
        node_number = int(col_name.split("_")[-1])
        Sim.needles[node_number] = vp.arrow(pos=vp.vector(0, 0, 0), axis=vp.vector(25, 0, 0), color=Sim.legend_nodes[node_number])


    #--------------
    #vp.box()
    #Sim.scene_dia11.append_to_caption("legend:")
    Sim.scene.append_to_caption("legend:")
    Sim.gui["legend_combo"] = vp.menu(pos=Sim.scene.caption_anchor,
                                      bind=widget_func_legend_combo,
                                      choices=["show","hide"], ) # half?

    Sim.scene.append_to_caption(" Filter: ")
    Sim.gui["filter_combo"] = vp.menu(pos=Sim.scene.caption_anchor,
                                      bind=widget_func_filter_combo,
                                      choices=["Nodes", "Generators", "Loads","Storages" ,"Cables", ])
    Sim.scene.append_to_caption("\n")
    Sim.gui["filter_text"] = vp.winput(pos=Sim.scene.caption_anchor,
                                       bind=widget_func_filter_text,
                                       type="string",
                                       width=Sim.dia_width*2,  # because 2 columns of diagrams at the right
                                       text="all nodes",
                                       )


def create_stuff():
    # right side legend
    #Sim.gui["legend_box"] =
    Sim.gui["legend"] = []
    #print(Sim.legend)
    h = Sim.canvas_height / len(Sim.legend)
    for i, (legend_text, colorvector) in enumerate(Sim.legend.items()):
        Sim.gui["legend"].append(vp.label(pixel_pos=True,
                 pos=vp.vector(Sim.canvas_width,Sim.canvas_height - i * h-(h/2),0),
                 text=legend_text,
                 height=h-2,
                 color=colorvector,
                 align="right",
                 font="monospace",
                 line=False,
                 box=False,
                 opacity=1,
                 background=vp.color.white,
                ))


    # axis arrows with letters
    ### Sim.test_arrow = vp.arrow(pos=Sim.center + vp.vector(0,1,0), axis=vp.vector(0,-1,0), color=vp.color.black)
    Sim.axis_x = vp.arrow(pos=Sim.center, axis=vp.vector(0.1, 0, 0), color=vp.color.red, pickable=False)
    Sim.axis_y = vp.arrow(pos=Sim.center, axis=vp.vector(0, 0.1, 0), color=vp.color.green, pickable=False)
    Sim.axis_z = vp.arrow(pos=Sim.center, axis=vp.vector(0, 0, 0.1), color=vp.color.blue, pickable=False)
    # ---- create ground floor ----
    # Sim.scene.visible=False
    Sim.mapbox = vp.box(  # pos=vp.vector(Sim.grid_max / 2, -0.05, Sim.grid_max / 2),
        pos=Sim.center + vp.vector(0, -0.01, 0),
        size=vp.vector(Sim.grid_max_x, 0.015, Sim.grid_max_z),
        # color=vp.color.cyan,
        # opacity=0.5,
        texture={'file': Sim.mapname1,
                 # 'bumpmap':bumpmaps.stucco,
                 # 'place':'left',
                 # 'flipx':True,
                 # 'flipy':True,
                 'turn': 0,
                 },
        pickable=False)

    # Sim.scene.waitfor("textures")
    # Sim.scene.visible = True
    # Create grid
    # Create grid
    Sim.labels["grid_legend"] = []
    for lon in range(int(Sim.x1), int(Sim.x2) + 1, 1):
        Sim.grid.append(vp.curve(pos=[vp.vector(lon, 0, geo_to_local(Sim.z1)),
                                      vp.vector(lon, 0, geo_to_local(Sim.z2))],
                                 color=vp.color.black,
                                 pickable=False,
                                 radius=0.0))
        Sim.labels["grid_legend"].append(vp.label(pos=vp.vector(lon, 0, geo_to_local(Sim.z1)), text=f"lon:{lon:.0f}",
                                                  box=False, yoffset=-30, line=False, opacity=0, color=vp.color.black))

    for lat in range(int(Sim.z1)+1, int(Sim.z2) + 1, 1):
        Sim.grid.append(vp.curve(pos=[vp.vector(Sim.x1, 0, geo_to_local(lat)),
                                      vp.vector(Sim.x2, 0, geo_to_local(lat))],
                                 color=vp.color.black,
                                 pickable=False,
                                 radius=0.0))
        Sim.labels["grid_legend"].append(vp.label(pos=vp.vector(Sim.x2, 0, geo_to_local(lat)), text=f"lat:{lat:.0f}",
                                                  box=False, xoffset=30, line=False, color=vp.color.black,
                                                  opacity=0))

    # ============== create nodes (busbars) according to geodata =============
    for node_number in Data.node_numbers:
        # print("create stuff: node # ", number, type(number), Data.nodes[number])
        # move node objects on map
        z,x = Data.node_geo[node_number]
        z = geo_to_local(z)
        y = 0
        name = Data.node_names[node_number]
        npos = vp.vector(x, 0, z)
        Sim.nodes[node_number] = vp.cylinder(pos=npos,
                                        color=Sim.colors["nodes"],
                                        radius=Sim.base["nodes_r"],
                                        axis=vp.vector(0, Sim.base["nodes_r"], 0),
                                        pickable=True,
                                        # texture={'file': os.path.join("assets", 'energy1.png'),
                                        #         # 'bumpmap': bumpmaps.stucco,
                                        #         'place': 'right',
                                        #         'flipx': False,
                                        #         'flipy': False,
                                        #         'turn': -1,
                                        #         },
                                        )
        Sim.nodes[node_number].what = "node"
        Sim.nodes[node_number].number = node_number
        Sim.letters[f"node {node_number}"] = vp.label(text=f"{name}", color=vp.color.white,
                                                 pos=npos,  # + vp.vector(0, Sim.base["nodes_r"], 0),
                                                 opacity=0.0,
                                                 box=False,
                                                 # billboard=True, emissive=True,
                                                 pickable=False, align="center")
        Sim.labels[f"node {node_number}"] = vp.label(pos=npos,
                                                text="?", height=10,
                                                color=vp.color.white,
                                                yoffset=-30,
                                                line=False,
                                                visible=False,
                                                pickable=False,
                                                opacity=0)

        if node_number in Data.storages:
            spos = npos+ vp.norm(npos - Sim.center) * Sim.base["storages_r"] * 5 # TODO 5 should be parameter
            Sim.storages[node_number] = vp.cylinder(pos=spos,
                                                    color= Sim.colors["storages"],
                                                    radius=Sim.base["storages_r"],
                                                    axis=vp.vector(0, Sim.base["storages_r"], 0),
                                                    pickable=True,
                                                    )
            Sim.storages[node_number].what = "storage"
            Sim.storages[node_number].number = node_number  # storage number
            Sim.storages[node_number].rating = Data.df_locations["storage_rating"][node_number - 1]
            #print("storage:", node_number, "rating:", Data.df_locations["storage_rating"][node_number - 1])
            # gnumber = Data.nodes_to_generators[number]
            # Sim.generators[is_generator].node_number = number  # corresponding node number
            Sim.letters[f"storage {node_number}"] = vp.label(text=f"{name.lower()}", color=vp.color.white,
                                                               pos=spos + vp.vector(0, Sim.base["storages_r"], 0),
                                                               opacity=0.0, box=False,
                                                               # billboard=True, emissive=True,
                                                               pickable=False, align="center")

            Sim.labels[f"storage {node_number}"] = vp.label(pos=spos,
                                                              text=f"s",
                                                              height=10,
                                                              color=vp.color.white,
                                                              visible=False,
                                                              yoffset=-40,
                                                              line=False,
                                                              opacity=0,
                                                              )
            # make automatic connection from storage to node
            Sim.storage_lines[node_number] = vp.curve(pos=[npos, spos],
                                                        radius=0,
                                                        color=Sim.colors["storage_lines"],
                                                        pickable=False)

        #if is_generator: -------------------- generator ------------------------
        if node_number in Data.generators:
            # gpos is on a line from the center to the  connected node pos and a bit more
            gpos = npos + vp.norm(npos - Sim.center) * Sim.base["generators_r"] * 3  # TODO: 3 should be parameter!
            # print("create generator ", number)
            Sim.generators[node_number] = vp.cylinder(pos=gpos,
                                                       color=Sim.colors["generators"],
                                                       radius=Sim.base["generators_r"],
                                                       axis=vp.vector(0, Sim.base["generators_r"], 0),
                                                       pickable=True,
                                                       # texture={'file': os.path.join("assets", 'energy2.png'),
                                                       #         # 'bumpmap': bumpmaps.stucco,
                                                       #         'place': 'right',
                                                       #         'flipx': False,
                                                       #         'flipy': False,
                                                       #         'turn': -1,
                                                       #         },
                                                       )
            Sim.generators[node_number].what = "generator"
            Sim.generators[node_number].number = node_number  # generator_number
            Sim.generators[node_number].rating = Data.df_locations["generator_rating"][node_number-1]
            print("generator:", node_number, "rating:", Data.df_locations["generator_rating"][node_number-1])
            # gnumber = Data.nodes_to_generators[number]
            #Sim.generators[is_generator].node_number = number  # corresponding node number
            Sim.letters[f"generator {node_number}"] = vp.label(text=f"{name.lower()}", color=vp.color.white,
                                                                pos=gpos + vp.vector(0, Sim.base["generators_r"], 0),
                                                                opacity=0.0, box=False,
                                                                # billboard=True, emissive=True,
                                                                pickable=False, align="center")

            Sim.labels[f"generator {node_number}"] = vp.label(pos=gpos,
                                                               text="g",
                                                               height=10,
                                                               color=vp.color.white,
                                                               visible=False,
                                                               yoffset=-40,
                                                               line=False,
                                                               opacity=0,
                                                               )
            # pointers look both north
            # ------- pointers for angle ------
            # ------- pointers for angle ------
            start = vp.vector(gpos.x, gpos.y, gpos.z)
            end1 = start + vp.vector(0, 0, -Sim.base["generators_r"] * Sim.factor["pointer1"], )  # 1.5
            end2 = start + vp.vector(0, 0, -Sim.base["generators_r"] * Sim.factor["pointer2"], )  # 2.0
            Sim.pointer0[node_number] = vp.arrow(pos=start,
                                                  axis=end1 - start,
                                                  color=vp.color.red,
                                                  # shaftwidth=1.0,
                                                  # headwidth= 3,
                                                  pickable=False,
                                                  )
            Sim.pointer1[node_number] = vp.arrow(pos=start,
                                                  axis=end2 - start,
                                                  color=vp.color.orange,
                                                  round=True,
                                                  # shaftwidth=0.5,
                                                  pickable=False,
                                                  # headwidth = 0.5
                                                  )
            # ---- disc ----
            Sim.discs[node_number] = vp.extrusion(path=[start, vp.vector(start.x, start.y + 0.001, start.z)],
                                                   shape=vp.shapes.circle(radius=Sim.base["generators_r"] * 1.25,
                                                                          # 0.05 SHOould be parameter!
                                                                          angle1=vp.radians(170),
                                                                          angle2=vp.radians(-170)),
                                                   pickable=False)
            # make automatic connection from generator to node
            Sim.generator_lines[node_number] = vp.curve(pos=[npos, gpos],
                                                         radius=0,
                                                         color=Sim.colors["generator_lines"],
                                                         pickable=False)

        #if is_load: ------------------------- load ---------------------
        if node_number in Data.loads:
            # create load
            # lpos is on a line from the center to the  connected node pos but a bit less
            lpos = npos + vp.norm(npos - Sim.center) * Sim.base["loads_r"] * -3  # TODO: -3 should be parameter!
            Sim.loads[node_number] = vp.cylinder(pos=lpos,
                                            radius=Sim.base["loads_r"],
                                            axis=vp.vector(0, Sim.base["loads_r"], 0),
                                            color=vp.color.red,
                                            pickable=True)
            Sim.loads[node_number].what = "load"
            Sim.loads[node_number].number = node_number
            Sim.letters[f"load {node_number}"] = vp.label(text=f"{name.lower()}", color=vp.color.white,
                                                     pos=lpos + vp.vector(0, Sim.base["loads_r"], 0),
                                                     opacity=0.0,
                                                     box=False,
                                                     # billboard=True, emissive=True,
                                                     pickable=False, align="center")
            Sim.labels[f"load {node_number}"] = vp.label(pos=npos,
                                                    text="l", height=10,
                                                    color=vp.color.white,
                                                    yoffset=-30,
                                                    line=False,
                                                    visible=False,
                                                    opacity=0,
                                                    pickable=False)
            Sim.load_lines[node_number] = vp.curve(pos=[npos, lpos],
                                              radius=0,
                                              color=Sim.colors["load_lines"],
                                              pickable=False)
    # ----- create CABLES ---- --------------------------------------------------------------------
    for i, to_number_list in Data.cables_dict.items():
        for j in to_number_list:
            from_node = Sim.nodes[i]
            to_node = Sim.nodes[j]
            # if (j, i) in Sim.cables.keys():
            #    continue  # create only one direction
            # Sim.cables is the direct connection. will NOT be moved by mouse
            Sim.cables[(i, j)] = vp.curve(radius=0.0, color=vp.color.orange, pos=[from_node.pos, to_node.pos],
                                          pickable=False)
            Sim.cables[(i, j)].number = (i, j)  # tuple of both node numbers
            Sim.cables[(i, j)].what = "cable"
            # divide each  cable (0,1) into several subcables by creating  subnodes (first and last subnodes are the cable nodes)
            start = from_node.pos
            end = to_node.pos
            diff = end - start
            # create middle
            mpos = start + diff / 2
            Sim.cables_middle[(i, j)] = vp.cylinder(pos=mpos,
                                                    radius=Sim.base["middles_r"],
                                                    color=Sim.colors["middles"],
                                                    axis=vp.vector(0, Sim.base["middles_r"], 0))
            Sim.cables_middle[(i, j)].what = "middle"
            Sim.cables_middle[(i, j)].number = (i, j)
            Sim.letters[f"cable {i}-{j}"] = vp.label(pos=mpos,
                                                     text=f"{i}-{j}",
                                                     height=10,
                                                     box=False,
                                                     opacity=0,
                                                     line=False,
                                                     color=vp.color.white,
                                                     visible=True,
                                                     )
            Sim.labels[f"cable {i}-{j}"] = vp.label(pos=mpos,
                                                    line=False,
                                                    text="c",
                                                    height=10,
                                                    yoffset=-20,
                                                    box=False,
                                                    opacity=0,
                                                    color=vp.color.white,
                                                    visible=False,
                                                    )
            # create sub-discs to move around with mouse
            # p = vp.vector(start.x, start.y, start.z)
            pointlist = []  # for sub-cables
            pointlist.append(start)
            for k in range(1, Sim.number_of_sub_cables):  # 6 subnodes
                p = start + k * vp.norm(diff) * vp.mag(diff) / (Sim.number_of_sub_cables)  # divide by
                subdisc = vp.cylinder(pos=p, radius=Sim.base["nodes_r"] / 2, color=vp.color.magenta,
                                      axis=vp.vector(0, Sim.base["nodes_r"] / 3, 0),
                                      pickable=True)
                subdisc.number = (i, j, k)
                subdisc.what = "subnode"
                Sim.sub_nodes[(i, j, k)] = subdisc
                pointlist.append(subdisc.pos)
                # label in the middle subnode
                # if k == int(Sim.number_of_sub_cables / 2):
                #    Sim.labels[f"cable {i}-{j}"] = vp.label(pos=subdisc.pos,
                #                                            text=f"c {i}-{j}",
                #                                            height=10,
                #                                            color=vp.color.white,
                #                                            visible=False,
                #                                            )
            pointlist.append(end)
            # -- create sub-cables between sub-discs
            Sim.sub_cables[(i, j)] = vp.curve(color=vp.color.magenta, radius=0.0, pos=pointlist, pickable=False)


def get_Data_min_max():
    # ---- nodes -----
    Sim.gui["color_crit_low_nodes"].text = f"{0.9:.2f}"
    Sim.colors["crit_low_nodes"] = 0.9
    Sim.gui["color_too_low_nodes"].text = f"{0.925:.2f}"
    Sim.colors["too_low_nodes"] = 0.925
    Sim.gui["color_low_nodes"].text = f"{0.95:.2f}"
    Sim.colors["low_nodes"] = 0.95
    Sim.gui["color_good_low_nodes"].text = f"{0.975:.2f}"
    Sim.colors["good_low_nodes"] = 0.975
    Sim.gui["color_good_high_nodes"].text = f"{1.025:.2f}"
    Sim.colors["good_high_nodes"] = 1.025
    Sim.gui["color_high_nodes"].text = f"{1.05:.2f}"
    Sim.colors["high_nodes"] = 1.05
    Sim.gui["color_too_high_nodes"].text = f"{1.075:.2f}"
    Sim.colors["too_high_nodes"] = 1.075
    Sim.gui["color_crit_high_nodes"].text = f"{1.1:.2f}"
    Sim.colors["crit_high_nodes"] = 1.1
    Sim.gui["min_max_nodes"].text = f"<code>{Data.nodes_min:.2f} / {Data.nodes_max:.2f}</code>"
    # ---- generator angle ----
    # -180 - 170 - 160 - 150  150     160     170     180
    Sim.gui["color_crit_low_generators_angle"].text = "-180"
    Sim.colors["crit_low_generators_angle"] = -180
    Sim.gui["color_too_low_generators_angle"].text = "-170"
    Sim.colors["too_low_generators_angle"] = -170
    Sim.gui["color_low_generators_angle"].text = "-160"
    Sim.colors["low_generators_angle"] = -160
    Sim.gui["color_good_low_generators_angle"].text = "-150"
    Sim.colors["good_low_generators_angle"] = -150
    Sim.gui["color_good_high_generators_angle"].text = "150"
    Sim.colors["good_high_generators_angle"] = 150
    Sim.gui["color_high_generators_angle"].text = "160"
    Sim.colors["high_generators_angle"] = 160
    Sim.gui["color_too_high_generators_angle"].text = "170"
    Sim.colors["too_high_generators_angle"] = 170
    Sim.gui["color_crit_high_generators_angle"].text = "180"
    Sim.colors["crit_high_generators_angle"] = 180
    Sim.gui[
        "min_max_generators_angle"].text = f"<code>{Data.generators_angle_min:.2f} / {Data.generators_angle_max:.2f}</code>"
    # ----- generators: 60 ,  80 ,  100, 120
    Sim.gui["color_crit_low_generators"].text = "0"
    Sim.colors["crit_low_generators"] = 0
    Sim.gui["color_too_low_generators"].text = "60"
    Sim.colors["too_low_generators"] = 60
    Sim.gui["color_low_generators"].text = "60"
    Sim.colors["low_generators"] = 60
    Sim.gui["color_good_low_generators"].text = "60"
    Sim.colors["good_low_generators"] = 60
    Sim.gui["color_good_high_generators"].text = 60
    Sim.colors["good_high_generators"] = 60
    Sim.gui["color_high_generators"].text = "80"
    Sim.colors["high_generators"] = 80
    Sim.gui["color_too_high_generators"].text = "100"
    Sim.colors["too_high_generators"] = 100
    Sim.gui["color_crit_high_generators"].text = "120"
    Sim.colors["crit_high_generators"] = 120
    Sim.gui[
        "min_max_generators"].text = f"<code>{Data.generators_loading_min:.2f} / {Data.generators_loading_max:.2f}</code>"
    # -------- cables: 60, 80, 100, 120 ------------
    Sim.gui["color_crit_low_cables"].text = "0"
    Sim.colors["crit_low_cables"] = 0
    Sim.gui["color_too_low_cables"].text = "0"
    Sim.colors["too_low_cables"] = 0
    Sim.gui["color_low_cables"].text = "0"
    Sim.colors["low_cables"] = 0
    Sim.gui["color_good_low_cables"].text = "30"
    Sim.colors["good_low_cables"] = 30
    Sim.gui["color_good_high_cables"].text = "60"
    Sim.colors["good_high_cables"] = 60
    Sim.gui["color_high_cables"].text = "80"
    Sim.colors["high_cables"] = 80
    Sim.gui["color_too_high_cables"].text = "100"
    Sim.colors["too_high_cables"] = 100
    Sim.gui["color_crit_high_cables"].text = "120"
    Sim.colors["crit_high_cables"] = 120
    Sim.gui["min_max_cables"].text = f"<code>{Data.cables_loading_min:.2f} / {Data.cables_loading_max:.2f}</code>"

    # ---- loads ----
    # -------- cables: 0,50,100, 200, 400, 1000 ------------
    Sim.gui["color_crit_low_loads"].text = "0"
    Sim.colors["crit_low_loads"] = 0
    Sim.gui["color_too_low_loads"].text = "50"
    Sim.colors["too_low_loads"] = 50
    Sim.gui["color_low_loads"].text = "100"
    Sim.colors["low_loads"] = 100
    Sim.gui["color_good_low_loads"].text = "200"
    Sim.colors["good_low_loads"] = 200
    Sim.gui["color_good_high_loads"].text = "400"
    Sim.colors["good_high_loads"] = 400
    Sim.gui["color_high_loads"].text = "600"
    Sim.colors["high_loads"] = 600
    Sim.gui["color_too_high_loads"].text = "800"
    Sim.colors["too_high_loads"] = 800
    Sim.gui["color_crit_high_loads"].text = "1000"
    Sim.colors["crit_high_loads"] = 1000
    Sim.gui["min_max_loads"].text = f"<code>{Data.loads_min:.2f} / {Data.loads_max:.2f}</code>"


def update_color(value, what="nodes"):
    """to calculate and return a conditional color based on a value. Looks into Sim.colors and Sim.colordict"""
    if value <= Sim.colors["crit_low_" + what]:
        return Sim.colordict["crit_low"]
    elif value >= Sim.colors["crit_high_" + what]:
        return Sim.colordict["crit_high"]
    elif value <= Sim.colors["too_low_" + what]:
        # between crit_low and too_low
        low = Sim.colors["crit_low_" + what]
        high = Sim.colors["too_low_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["crit_low"]
        delta = Sim.colordict["too_low"] - Sim.colordict["crit_low"]
        return basecolor + vp.norm(delta) * v
    elif value <= Sim.colors["low_" + what]:
        # between too_low and low
        low = Sim.colors["too_low_" + what]
        high = Sim.colors["low_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["too_low"]
        delta = Sim.colordict["low"] - Sim.colordict["too_low"]
        return basecolor + vp.norm(delta) * v
    elif value <= Sim.colors["good_low_" + what]:
        # between low and good_low
        low = Sim.colors["low_" + what]
        high = Sim.colors["good_low_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["low"]
        delta = Sim.colordict["good_low"] - Sim.colordict["low"]
        return basecolor + vp.norm(delta) * v
    elif value <= Sim.colors["good_high_" + what]:
        # between good_low and good_high
        low = Sim.colors["good_low_" + what]
        high = Sim.colors["good_high_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["good_low"]
        delta = Sim.colordict["good_high"] - Sim.colordict["good_low"]
        return basecolor + vp.norm(delta) * v
    elif value <= Sim.colors["high_" + what]:
        # between good_high and high
        low = Sim.colors["good_high_" + what]
        high = Sim.colors["high_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["good_high"]
        delta = Sim.colordict["high"] - Sim.colordict["good_high"]
        return basecolor + vp.norm(delta) * v
    elif value <= Sim.colors["too_high_" + what]:
        # between high and too_high
        low = Sim.colors["high_" + what]
        high = Sim.colors["too_high_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["high"]
        delta = Sim.colordict["too_high"] - Sim.colordict["high"]
        return basecolor + vp.norm(delta) * v
    elif value < Sim.colors["crit_high_" + what]:
        low = Sim.colors["too_high_" + what]
        high = Sim.colors["crit_high_" + what]
        v = (value - low) / (high - low)
        basecolor = Sim.colordict["too_high"]
        delta = Sim.colordict["crit_high"] - Sim.colordict["too_high"]
        return basecolor + vp.norm(delta) * v
    else:
        # strange value, paint it black
        return vp.vector(0, 0, 0)


def update_stuff():
    # return
    # if not Sim.animation_running:
    #    return
    # ---- frequency
    f = Data.df["frequency"][Sim.i]
    sec = Data.df["time"][Sim.i]
    Sim.scene_dia_needle_frequency.select()
    Sim.gui["frequency_text"].text = f"{f:.2f} Hz"
    #Sim.gui["time_text"].text = f"time: {sec:.2f} sec"
    # 50 hz...needle points north.
    # 49.9 ...neelde points west
    # 50.1 ...needle points east
    delta = f-50
    needle = Sim.needle_frequency
    needle.axis = vp.vector(0, 25, 0)
    if delta != 0:
        degree = 90 * delta/0.1
        needle.rotate(axis=vp.vector(0,0,-1), origin=vp.vector(0,0,0), angle=vp.radians(degree))
    Sim.scene_dia_needle_angle.select()
    radius = 30
    for number, cyl in Sim.generators.items():
        g_angle = Data.df[f"generator_angle_{number}"][Sim.i]
        ##print("gen number, angle:", number, g_angle)
        needle = Sim.needles[number]
        needle.axis = vp.vector(0,radius,0)  # point to right (0°)
        needle.rotate(axis=vp.vector(0,0,1), angle=vp.radians(-g_angle))

    Sim.scene.select()

    # ------- storages -----
    for number, cyl in Sim.storages.items():
        #storage_loading_3,storage_power_3,storage_state_3
        try:
            loading = Data.df[f"storage_loading_{number}"][Sim.i]
            power = Data.df[f"storage_power_{number}"][Sim.i]
            state = Data.df[f"storage_state_{number}"][Sim.i]
            #print("storage", number, ":", loading, power, state)
        except KeyError:
            print("could not found storage data for ", number)
            continue
        if number in Sim.tubes_storage:
            tube = Sim.tubes_storage[number]
            if not Sim.sloped_cables:
                tube.pos.y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
            else:
                tube.pos.y = Sim.nodes[number].axis.y
        cyl.power = power
        cyl.radius = Sim.base["storages_r"] + power * Sim.factor["storages_r"]
        cyl.axis = vp.vector(0, Sim.base["storages_h"] + power * Sim.factor["storages_h"], 0)
        Sim.letters[f"storage {number}"].pos.y = cyl.axis.y
        if Sim.label_storage == "p":
            ff = "p: {" + f":.{Sim.decimals_storage}f" + "}"
            Sim.labels[f"storage {number}"].text = ff.format(power)
        elif Sim.label_storage == "loading":
            ff = "loading: {" + f":.{Sim.decimals_storage}f" + "}"
            Sim.labels[f"storage {number}"].text = ff.format(loading)
        if Sim.dynamic_colors["storages"]:
            cyl.color = update_color(power, "storages")
        else:
            cyl.color = Sim.colors["storages"]
        so = Sim.selected_object
        if so is not None and so.what == "storage" and so.number == number:
            Sim.gui["help3"].text = f"storage: p: {power:.2f} loading: {loading:.2f} state: {state:.2f}"  # TODO: unit

    # -------- loads --------
    # if Sim.gui["box_loads"].checked:
    for number, cyl in Sim.loads.items():
        try:
            power = Data.df[f"load_power_{number}"][Sim.i]
            #loading = Data.df[f"load_loading_{number}"][Sim.i]
        except KeyError:
            # print(f"could not find data: column load_power_{number}, line {Sim.i})")
            continue
            # print("i skip this")
            # print(p, Sim.base["loads_r"], Sim.factor["loads_r"])
        # print(Sim.tubes_load)
        if number in Sim.tubes_load:
            tube = Sim.tubes_load[number]
            if not Sim.sloped_cables:
                tube.pos.y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
            else:
                tube.pos.y = Sim.nodes[number].axis.y
        cyl.power = power
        cyl.radius = Sim.base["loads_r"] + power * Sim.factor["loads_r"]
        cyl.axis = vp.vector(0, Sim.base["loads_h"] + power * Sim.factor["loads_h"], 0)
        Sim.letters[f"load {number}"].pos.y = cyl.axis.y
        if Sim.label_load == "p":
            ff = "p: {" + f":.{Sim.decimals_load}f" + "}"
            Sim.labels[f"load {number}"].text = ff.format(power)
        # loading for loads? where to get value?
        #elif Sim.label_storage == "loading":
        #    ff = "% loading: {" + f":.{Sim.decimals_load}f" + "}"
        #    Sim.labels[f"load {number}"].text = ff.format(loading)
        #text=
        #Sim.labels[f"load {number}"].text = text
        if Sim.dynamic_colors["loads"]:
            cyl.color = update_color(power, "loads")
        else:
            cyl.color = Sim.colors["loads"]
        so = Sim.selected_object
        if so is not None and so.what == "load" and so.number == number:
            Sim.gui["help3"].text = f"load: {power:.2f}"  # TODO: unit

    # --------- generators ----------------
    for number, cyl in Sim.generators.items():
        # try:
        #    power = Data.df[col_name_power(number)][Sim.i]
        #    g_angle = Data.df[col_name_angle(number)][Sim.i]
        # except KeyError:
        #    print(
        #        f"KeyError: could not find power / angle value in line {Sim.i} for columns {col_name_power(number)} / {col_name_angle(number)}")
        #    continue
        power = Data.df[f"generator_power_{number}"][Sim.i]
        # tube
        tube = Sim.tubes_generator[number]
        if not Sim.sloped_cables:
            tube.pos.y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
        else:
            tube.pos.y = Sim.nodes[cyl.number].axis.y

        cyl.power = power
        loading = Data.df[f"generator_loading_{number}"][Sim.i]
        g_angle = Data.df[f"generator_angle_{number}"][Sim.i]
        cyl.axis = vp.vector(0, power * Sim.factor["generators_h"] + Sim.base["generators_h"], 0)
        cyl.radius = power * Sim.factor["generators_r"] + Sim.base["generators_r"]
        # ------- pointers for angle --------
        # Sim.pointer0[number].y = cyl.pos.y + cyl.axis.y + 1
        # Sim.pointer1[number].y = cyl.pos.y + cyl.axis.y + 1
        # TODO: compare with angle from previous frame, only move when necessary
        # reset pointer1
        p0 = Sim.pointer0[number]
        p1_axis_vector = vp.vector(0, 0, -Sim.base["generators_r"] * Sim.factor["pointer1"])
        p1_axis_vector = vp.rotate(p1_axis_vector, angle=vp.radians(-g_angle), axis=vp.vector(0, 1, 0))
        Sim.pointer1[number].axis = vp.vector(p1_axis_vector.x, p1_axis_vector.y, p1_axis_vector.z)
        Sim.pointer1[number].pos.y = cyl.axis.y
        Sim.pointer0[number].pos.y = cyl.axis.y
        # Sim.discs[number].color = update_color(g_angle, "generators_angle")
        Sim.pointer1[number].color = update_color(g_angle, "generators_angle")


        Sim.letters[f"generator {number}"].pos.y = cyl.axis.y
        # ["none", "p", "angle", "p+angle", "loading"],
        ###Sim.labels[f"generator {number}"].text = f"{power} MW, {g_angle}°"

        if Sim.label_generator == "p":
            ff = "p: {" + f":.{Sim.decimals_generator}f" + "}"
            Sim.labels[f"generator {number}"].text = ff.format(power)
        elif Sim.label_generator == "angle":
            ff = "angle: {" + f":.{Sim.decimals_generator}f" + "}"
            Sim.labels[f"generator {number}"].text = ff.format(g_angle)
        elif Sim.label_generator == "p+angle":
            ff = "p: {" + f":.{Sim.decimals_generator}f" + "}" + " angle: {" + f":.{Sim.decimals_generator}f" + "}"
            Sim.labels[f"generator {number}"].text = ff.format(power, g_angle)
        elif Sim.label_generator == "loading":
            ff = "loading: {" + f":.{Sim.decimals_generator}f" + "}"
            Sim.labels[f"generator {number}"].text = ff.format(loading)

        # print(Sim.i, number, power)
        # color for generator, calculate % mva value
        """
        loading = % of MVA -> its for color coding the cables (* 100)
        # MVA calculation:
        % loading = sqrt (P^2 + Q^2) / MVArating
        """
        # p = power
        # q = 0
        # mva_node_number = Data.nodes_to_generators[number]
        # loading = ((p**2 + q**2)**0.5)/Data.mva_generators[mva_node_number] * 100
        # loading = Data.df[f"loading_gen_{number}"][Sim.i]

        # print(f"loading % of Mva for generator {number}: p = {power}, q=0, mva_number= {mva_node_number} mva= {Data.mva_generators[mva_node_number]} loading is: {loading}")
        # assume that loading must be multiplied by 100 again...
        if Sim.dynamic_colors["generators"]:
            cyl.color = update_color(loading, "generators")
        else:
            cyl.color = Sim.colors["generators"]
        so = Sim.selected_object
        if so is not None and so.what == "generator" and so.number == number:
            Sim.gui["help3"].text = f"power: {power:.2f} angle: {g_angle:.2f} loading: {loading:.2f}"  # TODO: unit

    # -------- nodes --------
    for number, cyl in Sim.nodes.items():
        # try:
        #    volt = Data.df[col_name_node(number)][Sim.i]
        # except KeyError:
        #    print("node number:", number, "col_name_node:", col_name_node(number))
        #    print(f"KeyError: could not found Volt in line {Sim.i} column {Data.df[col_name_node(number)]}")
        #    continue
        volt = Data.df[f"VOLT_{number}"][Sim.i]
        cyl.axis = vp.vector(0, volt * Sim.factor["nodes_h"] + Sim.base["nodes_h"], 0)
        cyl.radius = volt * Sim.factor["nodes_r"] + Sim.base["nodes_r"]
        # conditional color
        if Sim.dynamic_colors["nodes"]:
            cyl.color = update_color(volt, "nodes")
        else:
            cyl.color = Sim.colors["nodes"]
        ## Sim.labels[f"node {number}"].text = f"{volt:.1f} V"
        ff = "{" + f":.{Sim.decimals_node}f"+"} V"
        #print(ff, ff.format(volt))
        Sim.labels[f"node {number}"].text = ff.format(volt)
        Sim.letters[f"node {number}"].pos.y = cyl.axis.y
        # Sim.letters[f"node {number}"].pos.y = cyl.axis.y
        so = Sim.selected_object
        if so is not None and so.what == "node" and so.number == number:
            Sim.gui["help3"].text = f"volt: {volt:.2f}"  # TODO: unit

    # ------ cables -----
    #
    for number, targetlist in Data.cables_dict.items():
        for target in targetlist:


            try:
                mva = Data.df_locations.iloc[number-1][f"to_{target}"]
            except IndexError:
                mva = 0

            power = Data.df[f"cable_power_{number}_{target}"][Sim.i]
            Sim.cablepower[(number, target)] = power  # for speed of floating arrow
            loss = Data.df[f"cable_loss_{number}_{target}"][Sim.i]
            loading = Data.df[f"cable_loading_{number}_{target}"][Sim.i]
            flow = Data.df[f"cable_flow_{number}_{target}"][Sim.i]
            numtar = True if flow == 1 else False
            tubelist = Sim.tubes_node[(number, target)]
            deltay = Sim.nodes[number].axis.y - Sim.nodes[target].axis.y
            total_length = Sim.sub_cable_lengthlist[(number, target)][-1]
            old_y = Sim.nodes[number].axis.y

            for nr, tube in enumerate(tubelist):
                if not Sim.sloped_cables:
                    tube.pos.y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
                else:
                    # pass # TODO sloped cables!!!!!
                    # if nr == len(tubelist)-1:
                    #    continue
                    length = Sim.sub_cable_lengthlist[(number, target)][nr + 1]
                    tube.pos.y = old_y
                    # tube.axis.y = Sim.nodes[number].axis.y + length / total_length * deltay
                    tube.axis.y = 0 + length / total_length * deltay
                    oldy = tube.axis.y


            if f"cable {number}-{target}" in Sim.labels:
                # print(f"updating cable {number} {target}..")
                if Sim.label_cable == "p":
                    ff = "p: {" + f":.{Sim.decimals_cable}f" + "}"
                    text = ff.format(power)
                elif Sim.label_cable == "loading":
                    ff = "loading: {" + f":.{Sim.decimals_cable}f" + "}"
                    text = ff.format(loading)
                elif Sim.label_cable == "p+loading":
                    ff = "p: {" + f":.{Sim.decimals_cable}f" + "}" + " loading: {" + f":.{Sim.decimals_cable}f" + "}"
                    text = ff.format(power, loading)
                elif Sim.label_cable == "mva":
                    ff = "mva: {" + f":.{Sim.decimals_cable}f" + "}"
                    text = ff.format(mva)

                #Sim.labels[
                #    f"cable {number}-{target}"].text = f"power: {power:.2f} loss: {loss:.2f} loading: {loading:.2f} flow:{flow}"
                Sim.labels[f"cable {number}-{target}"].text = text

                # update pie chart
                disc = Sim.cables_middle[(number, target)]
                #points = [v + disc.pos + vp.vec(0, disc.axis.y, 0) for v in Sim.pie_points]
                l = int(min(loading,100))
                pie_box = Sim.pie_charts[(number, target)]
                pie_box.texture = Sim.pietextures[l]



                so = Sim.selected_object
                if so is not None and so.what == "middle" and so.number == (number, target):
                    # Sim.labels[f"cable {number}-{target}"].text
                    Sim.gui["help3"].text = Sim.labels[f"cable {number}-{target}"].text

                # ---- new- --
                # if (number,target) not in Sim.arrows:
                #    continue
                try:
                    arrowlist = Sim.arrows[(number, target)]
                except KeyError:
                    continue
                # print(number, target, "found arrowlist")

                for arrow in arrowlist:
                    if not Sim.sloped_cables:
                        # change y value of all arrows
                        arrow.pos.y = Sim.base["cables_h"] + power * Sim.factor["cables_h"]
                    else:
                        # sloped cables
                        ystart = Sim.nodes[number].axis.y
                        yend = Sim.nodes[target].axis.y
                        ydiff = yend - ystart
                        arrow.pos.y = ystart + arrow.calculate_sloped_y(ydiff)

                    # change radius
                    sw = Sim.base["cables_r"] + power * Sim.factor["cables_r"]
                    if arrow.shaftwidth != sw:
                        arrow.shaftwidth = Sim.base["cables_r"] + power * Sim.factor["cables_r"]
                        arrow.headwidth = 1.15 * arrow.shaftwidth
                    if vp.mag(arrow.axis) != Sim.base["flying_arrows_length"]:
                        arrow.axis = vp.norm(arrow.axis) * Sim.base["flying_arrows_length"]
                        Sim.shadows[arrow.number].axis = vp.norm(Sim.shadows[arrow.number].axis) * Sim.base[
                            "flying_arrows_length"]
                    # dynamic color
                    if Sim.dynamic_colors["cables"]:
                        arrow.color = update_color(loading, "cables")
                    else:
                        arrow.color = Sim.colors["cables"]
                    if power == 0:
                        arrow.color = vp.color.black
                    # flip direction?
                    if numtar != arrow.i2j:
                        arrow.flip_direction()
    return


def flying_discs():
    # storage?
    for i, cyl in Sim.storages.items():
        name = f"storage_power_{i}"
        try:
            power = cyl.power
        except AttributeError:
            continue # cylinder object has no power value yet (waiting for udpate_stuff or "play" button)
        if power != 0:
            if name not in FlyingDisc.container:
                FlyingDisc(name, power)
            else:
                # distance big enough for new arrow?
                distance_i, distance_j = FlyingDisc.distances[name]
                if power > 0:
                    if distance_i > Sim.base["flying_arrows_distance"]:
                        FlyingDisc(name, power)
                elif power < 0:
                    if distance_j > Sim.base["flying_arrows_distance"]:
                        FlyingDisc(name, power)
        for fd in [f for f in FlyingDisc.container if f.boss == name]:
            fd.update(power)


def flying_arrows():
    # flying arrows
    for (i, j), arrowlist in Sim.arrows.items():
        power = Data.df[f"cable_power_{i}_{j}"][Sim.i]
        for arrow in arrowlist:
            if power == 0:
                arrow.color = vp.color.gray(0.5)
            else:
                arrow.color = Sim.colors["cables"]
                arrow.update(Sim.dt)
    for number, arrow in Sim.generator_arrows.items():
        power = Data.df[f"generator_power_{arrow.gen_number}"][Sim.i]
        #except KeyError:
        #    continue
        if power == 0:
            arrow.color = vp.color.gray(0.5)
        else:
            arrow.color = vp.color.yellow
            arrow.update(Sim.dt)
    for number, arrow in Sim.load_arrows.items():
        #try:
        power = Data.df[f"load_power_{arrow.load_number}"][Sim.i]
        #except KeyError:
        #    continue
        if power == 0:
            arrow.color = vp.color.gray(0.5)
        else:
            arrow.color = vp.color.orange
            arrow.update(Sim.dt)



def main():
    # Sim.scene.bind("click", mouseclick )
    Sim.scene.bind("mousedown", mousebutton_down)
    Sim.scene.bind("mousemove", mouse_move)
    Sim.scene.bind("mouseup", mousebutton_up)

    Sim.scene_dia_needle_frequency.userzoom = False
    Sim.scene_dia_needle_frequency.userspin = False
    Sim.scene_dia_needle_frequency.userpan = False

    Sim.scene_dia_needle_angle.userzoom = False
    Sim.scene_dia_needle_angle.userspin = False
    Sim.scene_dia_needle_angle.userpan = False

    #Sim.scene_dia1.userspin = False

    Sim.scene3.userzoom = False
    Sim.scene3.userspin = False
    Sim.scene3.userpan = False

    camera_to_topdown()
    simtime = 0
    time_since_framechange = 0
    # frame_number = 0  # Sim.i
    while Sim.running:
        vp.rate(Sim.fps)
        simtime += Sim.dt
        time_since_framechange += Sim.dt
        Sim.gui["cursor"].text = f"long: {Sim.scene.mouse.pos.x:.2f}, lat: {geo_to_local(Sim.scene.mouse.pos.z):.2f}"
        Sim.gui["camera"].text = f"camera: {Sim.scene.camera.pos} axis: {Sim.scene.forward} center: {Sim.scene.center} range: {Sim.scene.range:.2f} fov: {Sim.scene.fov:.2f}"
        angle_now = vp.degrees(vp.diff_angle(vp.vector(0, Sim.scene.forward.y, Sim.scene.forward.z), vp.vector(0, 0, 1)))
        Sim.gui["camera_pitch"].text = f"{angle_now:.2f}"
        Sim.gui["camera_pitch_slider"].value = angle_now


        # ----- move camera with wasd keys?
        #pressed_keys = vp.keysdown()
        #if "w" in pressed_keys:
        #    Sim.scene.select()
        #    Sim.scene.center.z += 0.1
        #    Sim.scene.camera.pos.z += 0.1

        #    print("w pressed")
        #    #print("camera pos, scene center:", Sim.scene.camera.pos, Sim.scene.center)
        # ----------
        # print("simtime", simtime)
        # Sim.status.text = f"mouse: {Sim.scene.mouse.pos} discs: "
        # Sim.status2.text = f"selected obj: {Sim.selected_object}, drag: {Sim.dragging},"
        # play animation
        if not Sim.animation_running:
            if Sim.flying_while_paused:
                # flying arrows
                flying_arrows()

            continue
        flying_discs()
        flying_arrows()
        if time_since_framechange > Sim.frame_duration:
            time_since_framechange = 0
            Sim.old_i = Sim.i
            Sim.i += 1
            if Sim.i >= len(Data.df):
                Sim.i = 0

            # update widgets
            Sim.gui["label_frame"].text = f"{Sim.i}/{len(Data.df)} time: {Data.df['time'][Sim.i]}"
            Sim.gui["frameslider"].value = Sim.i
            ## get the data from df (for y values)
            update_stuff()
    print("bye bye")
    # close browser window
    os.kill(os.getpid(), signal.SIGINT)


if __name__ == "__main__":

    Sim.scene.select()
    #Sim.legend = create_color_legend() # for Sim.legend
    create_color_legend()  # for Sim.legend, Sim.legend_nodes, Sim.legend_cables
    create_stuff()

    create_stuff2() #

    Sim.scene.select()
    layout_load()

    Sim.scene3.select()

    create_widgets()
    Sim.scene.select()
    get_Data_min_max()
    main()
