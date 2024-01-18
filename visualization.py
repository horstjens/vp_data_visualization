import os.path
import csv
#import random
# non-standard-lib
import pandas as pd    # install with pip install pandas
import vpython as vp   # install with pip install vpython

VERSION = "0.19.1 "


"""
improved Prototype
generators (circles in diagram)
        >angle (for windmills) (-180° to 180°)
        >power 
nodes or busbars(small networks)
       get power from generators. send power to other networks. 
       recive power from other networks (negative numbers).
       send power to consumers
       > volt


cables connect nodes with each powers 
       > power from/to

color coding:       bad     crit     toler   ok     ok    toler    crit      bad
Angle	deg	        -180	-170	-160	-150	  150	 160	  170	  180   (gen.) 
Voltage	pu	        0.9	   0.925	0.95	0.975	1.025	1.05	1.075	    1.1 (nodes)
Circuits% of MVA 	                                   60	  80	  100	  120   (cables)
Generators of MVA                                      60	  80	  100	  120   (generators)
Losses	%	                                            2	   3	    4	    5 (low prio)

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


see MVA tables: 
mva_bus.csv
mva_generator.csv


# DONE: wind, node: cylinder grows in y axis
# DONE: cables: cylinder radius grows (xz axis)
# TODO: cables: connect top y value of their connected cylinders. arrows between each subnode. 
# losses: ? arrows up/down?

WONTFIX: +use different extruded shapes (Star etc.) instead of cylinders 

"""


class Data:
    """Data contains variables taken from the excel/csv file"""
    # create a pandas dataframe from csv
    df = pd.read_csv("raw_data.csv")

    # take some interesting columns (called 'series' in pandas)
    nodes_min = None
    nodes_max = None
    generators_min = None
    generators_max = None
    generators_angle_min = None
    generators_angle_max = None
    cables_min = None
    cables_max = None
    losses_min = None
    losses_max = None
    time_col_name = "Time(s)"
    generator_numbers = [i for i in range(30, 40)]  # numbers from 30 to 39

    # col_name for generator 30 angle: "ANGL 30[30 1.0000]1"
    # col_name for generator 30 power: "POWR 30[30 1.0000]1"
    # angle 39 is the reference angle (0)

    node_numbers = [i for i in range(1, 40)]  # numbers from 1 to 39
    cable_col_names = [raw_name for raw_name in df if raw_name.startswith("POWR ") and (" TO " in raw_name)]
    cables_dict = {}  # {from_number: [to_number, to_number, to_number], ...}
    # read mva data from csv
    mva_generators = {}
    mva_cables = {}
    nodes_to_generators = {}

class Sim:
    mode = "arrange"
    # glider_number = 1
    selected_object = None
    animation_running = False
    dragging = False
    scene = vp.canvas(title=f'version {VERSION}',
                      # caption="coordinates: ",
                      width=1200, height=800,
                      center=vp.vector(0, 0, 0),
                      background=vp.color.gray(0.8),
                      #align="left",  # caption is to the right?
                      )
    grid_max = 200
    grid_step = 10
    number_of_sub_cables = 6  # sub-nodes = sub_cables -1
    fps = 60
    dt = 1 / fps
    i = 1  # line in data sheet
    gui = {}  # widgets for gui
    # status = vp.label(text="nothing", pos=vp.vector(10, 10, 0), color=vp.color.green, pixel_pos=True, align="left")
    # status2 = vp.label(text="nada", pos=vp.vector(10, 50, 0), color=vp.color.green, pixel_pos=True, align="left")
    # colors = (vp.color.red, vp.color.green, vp.color.blue, vp.color.yellow)
    colordict = {"crit_low": vp.vector(0, 0, 1),  # dark blue,
                 "too_low": vp.vector(0, 0.5, 1),  # blue,
                 "low": vp.vector(0, 1, 1),  # cyan
                 "good_low": vp.vector(0, 1, 0.5),  # light green
                 "good_high": vp.vector(0, 1, 0),  # green
                 "high": vp.vector(0.5, 1, 0),  # green-yellow
                 "too_high": vp.vector(1, 1, 0),  # yellow
                 "crit_high": vp.vector(1, 0, 0),  # red
                 }
    colors = {"nodes": vp.color.blue,
              "generators": vp.color.yellow,
              "cables": vp.color.gray(0.5),
              # "mini_arrow": vp.color.purple,
              # "flyers1": vp.color.magenta,
              # "flyers2": vp.color.purple,
              "disc": vp.color.gray(0.75),
              "grid": vp.color.black,
              "ground": vp.color.green,
              "pointer0": vp.color.orange,
              "pointer1": vp.color.red,
              "generator_lines": vp.color.gray(0.25),
              "losses": vp.color.red,
              }
    factor = {"generators_h": 1.0,
              "nodes_h": 1.0,
              "generators_r": 0.0,
              "nodes_r": 0.0,
              "cables_r": 0.01,
              "arrows": 0.01,
              "arrows_x": 0.01,
              "arrows_z": 0.01,
              "losses": 1.0,
              }
    base = {"generators_h": 0.0,
            "nodes_h": 0.0,
            "generators_r": 5.0,
            "nodes_r": 4.0,
            "cables_r": 0.0,
            }

    visible = {"generators": True,
               "nodes": True,
               "cables": True,
               "flyers": False,
               }
    radius = {  # "generators": 5,
        # "nodes": 4,
        "pointer0": 8 + 0,  # for wind angle
        "pointer1": 8 + 0,  # for wind angle
        "geo1": grid_max / 2 - 25,
        "geo2": grid_max / 2 - 1,
    }
    textures = {  # "generators": os.path.join("energy2.png"),
        # "nodes": os.path.join("energy1.png"),
        "map": os.path.join("map001.png"),
    }
    animation_duration = 20  # seconds
    frame_duration = animation_duration / len(Data.df)
    # mini_arrow_length = 2
    # mini_arrow_base1 = 1
    # mini_arrow_base2 = 1
    # mini_arrow_distance = 20
    # mini_arrow_speed = 8

    # cursor = vp.cylinder(radius = 1, color=vp.color.white, pos = vp.vector(0,0,0), axis=vp.vector(0,0.2,0),
    # opacity=0.5, pickable=False)
    sloped_cables = True   # cables are sloped depending on the height of the connected node cylinders
    # --- vpython objects -----
    grid = []
    nodes = {}
    cables = {}  # direct connections (gold), only visible when in arrange mode
    generators = {}
    pointer0 = {}  # to display angle at each generator
    pointer1 = {}  # to display angle at each generator
    discs = {}
    generator_lines = {}
    sub_nodes = {}  # pink cylinders, draggable by mouse, only visible when in arrange mode
    sub_cables = {}  # pink curve for cable, connecting the sub_nodes. will be transformed into black shadows at simulation start
    #shadows = {}   # black shadows on y position 0, a clone from the sub-cable curve
    labels = {}  # 2d text label
    letters = {}  # 3d billboard letters for nodes and generators
    # mini_arrows = {}  # flying along the path, only visible when in simulation mode
    # mini_shadows = {}  # shadow for each glider
    mini_losses = {}  # stalagtites below each glider
    # arrows indication flow in cables
    arrows_ij = {}  # arrows along sub_nodes, pointing from lower node number to higher node number
    arrows_ji = {}  # arrows along sub_nodes, pointing from hight node number to lower node number


# ---------- helper functions for Data -----------

def read_mva_values():
    with open("mva_generator.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            #print(row)
            Data.mva_generators[int(row["generator_number"])] = int(row["mva"])

    print("loaded values of mva_generators:", Data.mva_generators)
    with open("mva_bus.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fb = int(row["from_bus"])
            tb = int(row["to_bus"])
            mva = int(row["mva"])
            Data.mva_cables[(fb, tb)] = mva
    print("loaded values of mva_cables:", Data.mva_cables)

def read_nodes_to_generators():
    with open("mva_nodes_generators.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Data.nodes_to_generators[int(row["node_number"])] = int(row["generator_number"])
    print("loaded values of nodes_to_generators:", Data.nodes_to_generators)

# helper functions for calculating loading value

def cable_loading(p,q,mva):
    return (p**2 + q**2)**0.5 / mva * 100

def calculate_loading():
    """Create new columns for each generator and each cable with the loading value and for each cable a loss value.

    The formula is for generators: sqrt(p²+q²) / mva * 100 * 100
    The formula is for cables:     sqrt(p²+q²) / mva * 100 # p is the bigger of the 2 power values
    The formula for loss: abs(active_power + reactive_power)

    q can be set to 0
    mva value from mva_generators / mva_cables
    generator_number for mva_generators from mva_nodes_generators
    #mva_generators = {}
    #mva_cables = {}
    #nodes_to_generators = {}
    """

    try:
        Data.df = pd.read_csv("enhanced_data.csv")
        print("enchanced_data.csv sucessfully loaded from disk!")
        return
    except:
        Data.df = pd.read_csv("raw_data.csv")


    print("please wait a bit, I calculate loss values and loading values for each cable / generator....")
    #print("Sim.generators", Sim.generators)
    #print("Data cables_dict:",Data.cables_dict)
    #print("Data.generator_numbers", Data.generator_numbers)
    #input("weiter mit Enter")
    for generator_number in Data.generator_numbers:
        new_name = f"loading_gen_{generator_number}"
        g = Data.nodes_to_generators[generator_number]
        mva = Data.mva_generators[g]
        colname = col_name_power(generator_number)
        #power = Data.df[col_name_power(number)][Sim.i]
        #df['C'] = df.apply(lambda row: row['A'] * row['B'], axis=1)
        # def generator_loading(p,q,mva):
        #     return (p**2 + q**2)**0.5 / mva * 100 * 100
        Data.df[new_name] = Data.df.apply(lambda row: row[colname]/mva * 100 * 100, axis=1)
    # ------
    for start_node, end_nodes in Data.cables_dict.items():
        for end_node in end_nodes:
            new_name = f"loading_cable_{start_node}_{end_node}"
            colname1 = col_name_cable(start_node, end_node)
            colname2 = col_name_cable(end_node, start_node)
            if (start_node, end_node) in Data.mva_cables:
                mva = Data.mva_cables[(start_node, end_node)]
            elif (end_node, start_node) in Data.mva_cables:
                mva = Data.mva_cables[(end_node, start_node)]
            else:
                print(f"mva value not found for cable {start_node} {end_node} or vice versa")
                continue
            #     return (p**2 + q**2)**0.5 / mva * 100 * 100
            Data.df[new_name] = Data.df.apply(lambda row: max(row[colname1],row[colname2]) / mva * 100, axis=1)
            # create loss column
            new_name = f"loss_cable_{start_node}_{end_node}"
            Data.df[new_name] = Data.df.apply(lambda row: abs(row[colname1]+row[colname2]), axis=1)
    # write back new dataframe
    print("Please wait a bit, writing new csv file .... ")
    Data.df.to_csv("enhanced_data.csv")
    print("enchanced csv file saved to disk")



def col_name_angle(generator_number):
    return f"ANGL {generator_number}[{generator_number} 1.0000]1"


def col_name_power(generator_number):
    return f"POWR {generator_number}[{generator_number} 1.0000]1"


def col_name_node(node_number):
    # col_name for node 1: "VOLT 1 [1 1.0000]"
    return f"VOLT {node_number} [{node_number} 1.0000]"


def col_name_cable(from_number, to_number):
    return f"POWR {from_number} TO {to_number} CKT '1 '"


def create_data():
    # cable connections (only one direction is necessary for now)
    # SOME COL NAMES SEEM TO EXIST TWICE OR MORE OFTEN IN THE SPREADSHEET
    # NODE 261 does not exist but connection to it exist
    # NODE 281 does not exist but connection to it exist

    duplicate_colnames = []
    for colname in Data.cable_col_names:
        words = colname.split(" ")
        c_from = int(words[1])
        c_to = int(words[3])
        if c_from not in Data.node_numbers:
            continue
        if c_to not in Data.node_numbers:
            continue
        print(colname, c_from, c_to)
        if c_from in Data.cables_dict:
            if c_to in Data.cables_dict[c_from]:
                print("strange error: duplicate column:", colname)
                duplicate_colnames.append(colname)
            else:
                Data.cables_dict[c_from].append(c_to)
        else:
            Data.cables_dict[c_from] = [c_to]

    # print(cables1)  # a set of 48 connections ( 96 for both directions, including the losses )
    print("duplicate colnames:", duplicate_colnames)

    print("Data.generator_numbers", Data.generator_numbers)
    print("Data.node_numbers", Data.node_numbers)
    print("Data.cables.dict:", Data.cables_dict)

    # --------------------- location of nodes and generators -------------
    # idea: arrange all nodes in a big circle
    # arrange the generators in an even bigger circle with the sam origin


# ------------ helper function for GUI ------------

def camera_to_topdown():
    Sim.scene.camera.pos = vp.vector(0, 2, 0)
    Sim.scene.forward = vp.vector(0.0, -1, 0)
    Sim.scene.up = vp.vector(0, 0, -1)
    Sim.scene.range = Sim.grid_max / 2
    Sim.scene.autoscale = True
    Sim.scene.autoscale = False
    # Sim.scene.userzoom = False
    Sim.scene.userspin = False


def func_restart(b):
    """stop and rewind"""
    # print("start was pressed", b.text)
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    Sim.i = 0
    Sim.gui["frameslider"].value = 0
    Sim.gui["label_frame"].text = str(0)


def func_step_back(b):
    """one step back in time"""
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    if Sim.i > 0:
        Sim.i -= 1
        Sim.gui["frameslider"].value = Sim.i
        Sim.gui["label_frame"].text = str(Sim.i)
        print("now at Step", Sim.i)
        update_stuff()
    else:
        print("Already at first step")


def func_step_forward(b):
    """one step forward in time"""
    """one step back in time"""
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    if Sim.i < len(Data.df):
        Sim.i += 1
        Sim.gui["frameslider"].value = Sim.i
        Sim.gui["label_frame"].text = str(Sim.i )
        print("now at Step", Sim.i)
        update_stuff()
    else:
        print("already at first step")


def func_end(b):
    """go to last step"""
    # print("start was pressed", b.text)
    Sim.animation_running = False
    Sim.gui["play"].text = "Play >"
    Sim.i = len(Data.df)
    Sim.gui["frameslider"].value = len(Data.df)
    Sim.gui["label_frame"].text = str(len(Data.df))


def func_play(b):
    # print("play button was pressed", b.text)
    if "play" in b.text.lower():
        Sim.animation_running = True
        Sim.gui["play"].text = "Pause ||"
    else:
        Sim.animation_running = False
        Sim.gui["play"].text = "Play >"


def func_time_slider(b):
    """jump to a specific frame in the dataset """
    # print("slider is set to ", b.value)
    # Sim.connAB.pos.y = power_ab[b.value]
    Sim.gui["label_frame"].text = str(b.value)
    Sim.i = b.value
    update_stuff()


def func_toggle_dynamic_nodes(b):
    if b.checked:
        pass

def func_toggle_dynamic_generators(b):
    if b.checked:
        pass

def func_toggle_dynamic_cables(b):
    if b.checked:
        pass

def func_toggle_nodes_labels(b):
    """toggles labels for nodes"""
    for name, value in Sim.labels.items():
        if name.startswith("node"):
            Sim.labels[name].visible = b.checked


def func_toggle_generator_labels(b):
    """toggles labels for generators"""
    for name, value in Sim.labels.items():
        if name.startswith("generator"):
            Sim.labels[name].visible = b.checked


def func_toggle_cable_labels(b):
    """toggles labels for cables"""
    for name, value in Sim.labels.items():
        if name.startswith("cable"):
            Sim.labels[name].visible = b.checked


def func_toggle_cables(b):
    """toggles visibility for sub-cables on floor"""
    #print("setting subcables to:", b.checked)
    for curve in Sim.sub_cables.values():
        curve.visible = b.checked
    #for a in Sim.arrows_ji.values():
    #        a.visible=b.checked
    #for a in Sim.arrows_ji.values():
    #        a.visible=b.checked
    update_stuff()


def func_toggle_nodes(b):
    """toggle visibility for nodes (busbars)"""
    for i, cyl in Sim.nodes.items():
        cyl.visible = b.checked


def func_toggle_generators(b):
    """toggle visibility for wind generators """
    for i in Sim.generators:
        Sim.generators[i].visible = b.checked
        # Sim.discs[i].visible = b.checked
        # Sim.pointer0[i].visible = b.checked
        # Sim.pointer1[i].visible = b.checked
        Sim.generator_lines[i].visible = b.checked


def func_toggle_generators_angle(b):
    """toggle visibility for wind generators disc and pointers"""
    for i in Sim.generators:
        # Sim.generators[i].visible = b.checked
        Sim.discs[i].visible = b.checked
        Sim.pointer0[i].visible = b.checked
        Sim.pointer1[i].visible = b.checked
        # Sim.generator_lines[i].visible = b.checked


def func_toggle_shadows(b):
    for curve in Sim.sub_cables.values():
        for k in range(curve.npoints):
            curve.modify(k, visible=b.checked)
        #pass
        # if (i, j) in Sim.mini_shadows:
        #    for n, shadow in Sim.mini_shadows[(i, j)].items():
        #        shadow.visible = b.checked


def func_toggle_losses(b):
    """toggles loss rectangles for cables"""
    for (i, j) in Sim.cables:
        if (i, j) in Sim.mini_losses:
            for n, loss_arrow in Sim.mini_losses[(i, j)].items():
                loss_arrow.visible = b.checked


def func_toggle_grid(b):
    """toggles grid lines"""
    for line in Sim.grid:
        line.visible = b.checked


def func_toggle_letters(b):
    """toggle billboard letters"""
    for bb in Sim.letters.values():
        bb.visible = b.checked


def func_toggle_sloped_cables(b):
    Sim.sloped_cables = b.checked
    if not b.checked:
        # return all subcable curve points to y value zero:
        #for (i, j), curve in Sim.sub_cables.items():
            #yi = Sim.nodes[i].axis.y
            #yj = Sim.nodes[j].axis.y
        #    n = Sim.number_of_sub_cables
            #delta = (yj - yi) / n
        #    for k in range(curve.npoints):
        #        oldpos = curve.point(k)["pos"]
        #        curve.modify(k, pos=vp.vector(oldpos.x, 0, oldpos.z))
        for arrow in Sim.arrows_ij.values():
            arrow.pos.y = 0
            arrow.axis.y = 0
        for arrow in Sim.arrows_ji.values():
            arrow.pos.y = 0
            arrow.axis.y = 0
    update_stuff()

#def func_toggle_legend(b):
#    """toggle visibility of legend"""
#    for l in Sim.gui["legend"]:
#        l.visible = b.checked


def func_generators_factor_h(b):
    # print("the y factor for generators is now:", b.number)
    Sim.factor["generators_h"] = b.number
    update_stuff()


def func_generators_factor_r(b):
    Sim.factor["generators_r"] = b.number
    update_stuff()


def func_generators_base_h(b):
    Sim.base["generators_h"] = b.number
    update_stuff()


def func_generators_base_r(b):
    Sim.base["generators_r"] = b.number
    update_stuff()


def func_nodes_factor_h(b):
    # print("the y factor for nodes is now:", b.number)
    Sim.factor["nodes_h"] = b.number
    update_stuff()


def func_nodes_factor_r(b):
    Sim.factor["nodes_r"] = b.number
    update_stuff()


def func_nodes_base_h(b):
    Sim.base["nodes_h"] = b.number
    update_stuff()


def func_nodes_base_r(b):
    Sim.base["nodes_r"] = b.number
    update_stuff()


def func_cables_factor_r(b):
    Sim.factor["cables_r"] = b.number
    update_stuff()


def func_cables_base_r(b):
    Sim.base["cables_r"] = b.number
    update_stuff()


def func_factor_losses(b):
    # print("the y factor for losses is now:", b.number)
    Sim.factor["losses"] = b.number
    update_stuff()


# def func_arrange():  # not a button anymore, therefore no parameter b.
#     #Sim.gui["save_layout"].disabled = False
#     Sim.gui["mode"].text = "mode is now: arrange"
#     Sim.mode = "arrange"
#     #Sim.gui["arrange"].disabled = True
#     Sim.gui["simulation"].disabled = False
#     Sim.gui["restart"].disabled = True
#     Sim.gui["play"].disabled = True
#     Sim.gui["frameslider"].disabled = True
#     camera_to_topdown()  # TODO: pick coordinates are broken if coming back from siumlation mode
#     # make visible
#     for d in (Sim.cables, Sim.sub_nodes, Sim.sub_cables):  # dictionaries
#         for o in d.values():
#             o.visible = True

def func_animation_duration(b):
    """set new animation duration from gui"""
    # animation_duration = 20  # seconds
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


def func_simulation(b):
    save_layout()
    Sim.gui["mode"].text = "mode is now: simulation"
    # Sim.gui["save_layout"].disabled = True
    Sim.mode = "simulation"
    # Sim.gui["arrange"].disabled = False
    Sim.gui["simulation"].disabled = True
    Sim.gui["restart"].disabled = False
    Sim.gui["end"].disabled = False
    Sim.gui["play"].disabled = False
    Sim.gui["step_back"].disabled = False
    Sim.gui["step_forward"].disabled = False
    Sim.gui["end"].disabled=False
    Sim.gui["frameslider"].disabled = False
    # update gui so that cables can be toggled
    Sim.gui["box_cables"].disabled = False
    # update gui so that gliders are visible and not anymore disabled
    # Sim.gui["box_gliders"].disabled = False
    Sim.gui["box_losses"].disabled = False
    Sim.gui["box_shadows"].disabled = False
    # Sim.gui["box_gliders"].checked = True
    Sim.gui["box_losses"].checked = True
    Sim.gui["box_shadows"].checked = True

    # free camera
    Sim.scene.userspin = True
    # make invisible
    for d in (Sim.cables, Sim.sub_nodes):  # dictionaries # Sim.sub_cables
        for o in d.values():
            o.visible = False
    # make visible
    # ----------- delete ALL mini_arrows ----------
    # for arrowlist in Sim.mini_arrows.values():
    #    for o in arrowlist:
    #        o.visible = False
    # Sim.mini_arrows = {}
    # ---- delete all shadows ---
    # for shadowlist in Sim.mini_shadows.values():
    #    for o in shadowlist:
    #        o.visible = False
    # Sim.mini_shadows = {}
    # ---- delete all mini-losses ----
    # for losslist in Sim.mini_losses.values():
    #    for o in losslist:
    #        o.visible = False
    Sim.mini_losses = {}
    # ----- new: ---



    ## create ij and ji arrows along subcable pointlist
    # TODO: make more than one arrow per subcable
    Sim.arrows_ij = {}
    Sim.arrows_ji = {}
    for (i, j), curve in Sim.sub_cables.items():
        pointlist = [p["pos"] for p in curve.slice(0, curve.npoints)]
        for k, point1 in enumerate(pointlist):
            color_ij = vp.color.gray(0.4) if k % 2 == 0 else vp.color.gray(0.2)  # TODO: better color cycling
            color_ji = vp.color.gray(0.8) if k % 2 == 0 else vp.color.gray(0.6)  # TODO: better color cycling
            if k == (len(pointlist) - 1):
                continue  # already at last point in pointlist
            point2 = pointlist[k + 1]
            diff = point2 - point1

            Sim.arrows_ij[(i, j, k)] = vp.arrow(pos=point1, axis=diff, round=True, shaftwidth=1, headwidth=2,
                                                color=color_ij, visible=True, pickable=False)
            Sim.arrows_ji[(i, j, k)] = vp.arrow(pos=point2, axis=-diff, round=True, shaftwidth=1, headwidth=2,
                                                color=color_ji, visible=False, pickable=False)
    # transform the sub-cables into shadows (black, on floor)
    for (i,j), snake in Sim.sub_cables.items():
    #    # TODO: find out why a curve object cannot be cloned or improve official documentation
        #pointlist = snake.slice(0, snake.npoints)  # pointlist is a list of dicts
        #pointlist2 = []
        for k in range(snake.npoints):
            snake.modify(k, color=vp.color.black)
            #p2["color"]=vp.color.black       # change the pink color of each point to black
            #pointlist2.append(p2)
        #print("pointlist is:", pointlist)

        #Sim.shadows[(i,j)] = vp.curve(pos=pointlist2, color=vp.color.black, pickable=False,visible=True)



    # ----- old: ---
    # ------------ create NEW mini_Arrows, one at each subnode------------
    # create little (moving) gliders for cable, loss, shadow
    # for (i, j), curve in Sim.sub_cables.items():
    #     plist = [p["pos"] for p in curve.slice(0, curve.npoints)]
    #     #Sim.mini_arrows[(i, j)] = {}
    #     #Sim.mini_shadows[(i, j)] = {}
    #     #Sim.mini_losses[(i, j)] = {}
    #     for number, point in enumerate(plist):
    #         new_number = number + 1
    #         if number == len(plist) - 1:
    #             p2 = plist[-1] + (plist[-1] - plist[-2])
    #         else:
    #             p2 = plist[new_number]
    #         big_diff = vp.mag(p2 - point)
    #         space_between = Sim.mini_arrow_length + Sim.mini_arrow_distance
    #         n = 0
    #         while n * space_between < big_diff:
    #             startpoint = point + vp.norm(p2 - point) * n * space_between
    #             #g = Glider(i, j, number, new_number,
    #             #           startpoint)  # is putting himself into Sim.mini_arrows[(i,j)][g.number]
    #             #shadow = vp.cylinder(pos=vp.vector(startpoint.x, 0, startpoint.z),
    #             #                     opacity=0.5,
    #             #                     color=vp.color.black,
    #             #                     radius=Sim.mini_arrow_base1,
    #             #                     axis=vp.vector(0, 0.02, 0),
    #             #                     pickable=False)
    #             #Sim.mini_shadows[(i, j)][g.number] = shadow
    #             #losspin = vp.arrow(pos=startpoint,
    #             #                   pickable=False,
    #             #                   axis=vp.vector(0, -0.1, 0),
    #             #                   color=Sim.colors["losses"],
    #             #                   size=vp.vector(1, 0.1, 0.1))
    #             #Sim.mini_losses[(i, j)][g.number] = losspin
    #             n += 1


def save_layout():  # not a button anymore, therefore no parameter b. function get executed by func_simulation()
    """save pos for each: generator, node, subnode. Save pointlist for each sub_cable"""
    with open("layout_data.txt", "w") as myfile:
        myfile.write("#generators\n")
        for i, gen in Sim.generators.items():
            myfile.write(f"{i} {gen.pos.x} {gen.pos.y} {gen.pos.z}\n")
        myfile.write("#nodes\n")
        for i, cyl in Sim.nodes.items():
            myfile.write(f"{i} {cyl.pos.x} {cyl.pos.y} {cyl.pos.z}\n")
        myfile.write("#curves\n")
        for (i, j), curve in Sim.sub_cables.items():
            for k in range(curve.npoints):
                point = curve.point(k)["pos"]
                myfile.write(f"{i} {j} {k} {point.x} {point.y} {point.z}\n")
    print("file layout_data.txt is written")


def load_layout():
    # print("generators:", Sim.generators)
    """attempting to load from layout_data.txt if this file can be found"""
    try:
        with open("layout_data.txt") as myfile:
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
        #match mode:
        if mode is None:
            #case None:
                continue

        elif mode == "curves":
                i, j, k, x, y, z = [float(word) for word in line.split(" ")]
                i, j, k = int(i), int(j), int(k)
                pointpos = vp.vector(x, y, z)
                Sim.sub_cables[(i, j)].modify(k, pointpos)
                if (i, j, k) in Sim.sub_nodes:
                    Sim.sub_nodes[(i, j, k)].pos = pointpos
                if k == int(Sim.number_of_sub_cables / 2):
                    Sim.labels[f"cable {i}-{j}"].pos = pointpos

        elif mode == "nodes":
                number, x, y, z = [float(word) for word in line.split(" ")]
                number = int(number)
                npos = vp.vector(x, y, z)
                Sim.nodes[number].pos = npos
                Sim.letters[f"node {number}"].pos = npos + Sim.nodes[number].axis + vp.vector(0, 1, 0)
                Sim.labels[f"node {number}"].pos = npos
                if number in Sim.generator_lines:
                    Sim.generator_lines[number].modify(0, npos)
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
                Sim.letters[f"generator {number}"].pos = gpos + Sim.generators[number].axis + vp.vector(0, 1, 0)
                Sim.discs[number].pos = gpos
                Sim.pointer0[number].pos = gpos
                Sim.pointer1[number].pos = gpos
                Sim.generator_lines[number].modify(1, pos=gpos)  # 1 is the generator, 0 is the node
                # Sim.generator_lines[number].modify(0, pos=Sim.nodes[number].pos)

        else :
                print("unhandled value for mode in layout file:", mode)
    print("loading of layout data was sucessfull")


def hexcode_to_vector(hexcode):
    r = int(hexcode[1:3], base=16) / 256
    g = int(hexcode[3:5], base=16) / 256
    b = int(hexcode[5:7], base=16) / 256
    return vp.vector(r, g, b)

def is_colorstring_valid(colorstring):
    if any((len(colorstring) != 7, colorstring[0] != "#", len([x for x in colorstring[1:] if x not in "0123456789abcdef"])>0)):
        #vp.input(f"{colorstring} is not a correct hex-value for a color.\nFirst char must be a #.\nNext two chars must be a hex value for red (00 - ff).\nNext two chars must be a hex value for green (00-ff).\nThe last two chars must be a hex value for blue (00-ff).\nPlease press OK and try again.")
        print("invalid colorstring:", colorstring)
        return False
    return True

def func_color_crit_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_crit_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return

    Sim.colordict["crit_low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text

    end_position = full_text.find("    crit low") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position+1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position+1:]
    print("new:",Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_too_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_too_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["too_low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    too low") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    low") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_good_low(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_good_low"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["good_low"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    good low") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_good_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_good_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["good_high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    good high") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    high    ") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_too_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_too_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["too_high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    too high") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()


def func_color_crit_high(b):
    # sanity check for new color value
    new_colorstring = Sim.gui["color_crit_high"].text.lower().strip()
    if not is_colorstring_valid(new_colorstring):
        return
    Sim.colordict["crit_high"] = hexcode_to_vector(b.text)
    full_text = Sim.gui["color_headings"].text
    end_position = full_text.find("    crit high") - 4
    start_position = end_position - 6
    print("old:", full_text[start_position:end_position + 1])
    Sim.gui["color_headings"].text = full_text[:start_position] + new_colorstring + full_text[end_position + 1:]
    print("new:", Sim.gui["color_headings"].text)
    if Sim.mode == "simulation":
        update_stuff()

# ------ nodes ------------
def func_color_crit_low_nodes(b):
    Sim.colors["crit_low_nodes"] = b.number
    update_stuff()


def func_color_too_low_nodes(b):
    Sim.colors["too_low_nodes"] = b.number
    update_stuff()


def func_color_low_nodes(b):
    Sim.colors["low_nodes"] = b.number
    update_stuff()


def func_color_good_low_nodes(b):
    Sim.colors["good_low_nodes"] = b.number
    update_stuff()


def func_color_good_high_nodes(b):
    Sim.colors["good_high_nodes"] = b.number
    update_stuff()


def func_color_high_nodes(b):
    Sim.colors["high_nodes"] = b.number
    update_stuff()


def func_color_too_high_nodes(b):
    Sim.colors["too_high_nodes"] = b.number
    update_stuff()


def func_color_crit_high_nodes(b):
    Sim.colors["crit_high_nodes"] = b.number
    update_stuff()

# ------- generators ----------

#def func_color_crit_low_generators(b):
#    Sim.colors["crit_low_generators"] = b.number
#def func_color_too_low_generators(b):
#    print(b.number)
#def func_color_low_generators(b):
#    print(b.number)


def func_color_crit_low_generators(b):
    Sim.colors["crit_low_generators"] = b.number
    update_stuff()


def func_color_too_low_generators(b):
    Sim.colors["too_low_generators"] = b.number
    update_stuff()


def func_color_low_generators(b):
    Sim.colors["low_generators"] = b.number
    update_stuff

def func_color_good_low_generators(b):
    Sim.colors["good_low_generators"] = b.number
    update_stuff()
def func_color_good_high_generators(b):
    Sim.colors["good_high_generators"] = b.number
    update_stuff()


def func_color_high_generators(b):
    Sim.colors["high_generators"] = b.number
    update_stuff()


def func_color_too_high_generators(b):
    Sim.colors["too_high_generators"] = b.number
    update_stuff()


def func_color_crit_high_generators(b):
    Sim.colors["crit_high_generators"] = b.number
    update_stuff()

# ------- generator angle -------


def func_color_crit_low_generators_angle(b):
    Sim.colors["crit_low_generators_angle"] = b.number
    update_stuff()


def func_color_too_low_generators_angle(b):
    Sim.colors["too_low_generators_angle"] = b.number
    update_stuff()


def func_color_low_generators_angle(b):
    Sim.colors["low_generators_angle"] = b.number
    update_stuff()


def func_color_good_low_generators_angle(b):
    Sim.colors["good_low_generators_angle"] = b.number
    update_stuff()


def func_color_good_high_generators_angle(b):
    Sim.colors["good_high_generators_angle"] = b.number
    update_stuff()


def func_color_high_generators_angle(b):
    Sim.colors["high_generators_angle"] = b.number
    update_stuff()


def func_color_too_high_generators_angle(b):
    Sim.colors["too_high_generators_angle"] = b.number
    update_stuff()


def func_color_crit_high_generators_angle(b):
    Sim.colors["crit_high_generators_angle"] = b.number
    update_stuff()
# ---- cables ----

def func_color_crit_low_cables(b):
    Sim.colors["crit_low_cables"] = b.number
    update_stuff()

def func_color_too_low_cables(b):
    Sim.colors["too_low_cables"] = b.number
    update_stuff()

def func_color_low_cables(b):
    Sim.colors["low_cables"] = b.number
    update_stuff()

def func_color_good_low_cables(b):
    Sim.colors["good_low_cables"] = b.number
    update_stuff()

def func_color_good_high_cables(b):
    Sim.colors["good_high_cables"] = b.number
    update_stuff()

def func_color_high_cables(b):
    Sim.colors["high_cables"] = b.number
    update_stuff()

def func_color_too_high_cables(b):
    Sim.colors["too_high_cables"] = b.number
    update_stuff()

def func_color_crit_high_cables(b):
    Sim.colors["crit_high_cables"] = b.number
    update_stuff()


# --------- losses ------------

def func_color_too_low_losses(b):
    print(b.number)


def func_color_low_losses(b):
    print(b.number)


def func_color_losses(b):
    print(b.number)


def func_color_high_losses(b):
    print(b.number)


def func_color_too_high_losses(b):
    print(b.number)


def create_widgets():
    # ---- widgets above window in title area -------
    # Sim.scene.append_to_title("mode:")
    # Sim.gui["arrange"] = vp.button(bind=func_arrange, text="arrange", pos=Sim.scene.title_anchor, disabled=True)
    # Sim.gui["save_layout"] = vp.button(bind=func_save_layout, text="save layout", pos=Sim.scene.title_anchor,
    #                                   disabled=False)
    Sim.gui["mode"] = vp.wtext(pos=Sim.scene.title_anchor, text="mode is now: arrange nodes by dragging with mouse")
    Sim.gui["simulation"] = vp.button(bind=func_simulation, text="start simulation", pos=Sim.scene.title_anchor,
                                      disabled=False)
    Sim.gui["restart"] = vp.button(bind=func_restart, text="|<", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["step_back"] = vp.button(bind=func_step_back, text="<", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["play"] = vp.button(bind=func_play, text="play >", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["step_forward"] = vp.button(bind=func_step_forward, text=">", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["end"] = vp.button(bind=func_end, text=">|", pos=Sim.scene.title_anchor, disabled=True)
    # Sim.button_end = vp.button(bind=func_end, text=">|", pos=Sim.scene.title_anchor)

    # Sim.label1 = vp.wtext(pos=Sim.scene.title_anchor, text="---hallo---")
    # Sim.scene.append_to_title("\n")
    Sim.gui[" timeframe"] = vp.wtext(pos=Sim.scene.title_anchor, text="timeframe:  ")
    Sim.gui["frameslider"] = vp.slider(pos=Sim.scene.title_anchor, bind=func_time_slider, min=0, max=len(Data.df),
                                       length=700, step=1, disabled=True)
    Sim.gui["label_frame"] = vp.wtext(pos=Sim.scene.title_anchor, text=" 0")
    Sim.gui["label_last_frame"] = vp.wtext(pos=Sim.scene.title_anchor, text=f" of {len(Data.df)} ")
    Sim.scene.append_to_title("\n")
    # ---- widgets below window in caption area --------------
    # Sim.gui["color_crit_low_nodes"].text = f"{0.9:.2f}"
    # Sim.gui["color_too_low_nodes"].text = f"{0.925:.2f}"
    # Sim.gui["color_low_nodes"].text = f"{0.95:.2f}"
    # Sim.gui["color_good_low_nodes"].text = f"{0.975:.2f}"
    # Sim.gui["color_good_high_nodes"].text = f"{1.025:.2f}"
    # Sim.gui["color_high_nodes"].text = f"{1.05:.2f}"
    # Sim.gui["color_too_high_nodes"].text = f"{1.075:.2f}"
    # Sim.gui["color_crit_high_nodes"].text= f"{1.1:.2f}"
    # Sim.scene.append_to_caption("<code>entinity:    |    unit       |"
    # IMPORTANT ! background-color must always be the last style command (8 chars distance) before the "too low" etc.
    # TODO: use regex instead?
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
    Sim.gui["color_headings"] = vp.wtext(pos=Sim.scene.caption_anchor, text=t)
    Sim.scene.append_to_caption("<code>color:       |      RGB      |</code>")
    # colordict = {"crit_low": vp.vector(0,0,1),     # dark blue,
    #             "too_low":  vp.vector(0,0.5,1 ),  # blue,
    #             "low":      vp.vector(0,1,1),     # cyan
    #             "good_low": vp.vector(0,1,0.5),   # light green
    #             "good_high":vp.vector(0,1,0),     # green
    #             "high":     vp.vector(0.5,1,0),   # green-yellow
    #             "too_high": vp.vector(1,1,0),     # yellow
    #             "crit_high":vp.vector(1,0,0),     # red
    #             }
    Sim.gui["color_crit_low"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_low,
                                          width=100,
                                          type="string", text="#0000FF")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low,
                                         width=100,
                                         type="string", text="#0080FF")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_low"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low,
                                     width=100,
                                     type="string", text="#00FFFF")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_good_low,
                                          width=100,
                                          type="string", text="#00FF80")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_good_high,
                                           width=100,
                                           type="string", text="#00FF00")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_high"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high,
                                      width=100,
                                      type="string", text="#80FF00")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high,
                                          width=100,
                                          type="string", text="#FFFF00")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_high,
                                           width=100,
                                           type="string", text="#FF0000")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.scene.append_to_caption("\n")

    Sim.scene.append_to_caption("<code>nodes:       | Voltage pu    |</code>")
    Sim.gui["color_crit_low_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_low_nodes, width=100,
                                                type="numeric", text="0.9")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_nodes, width=100,
                                               type="numeric", text="0.925")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_low_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_nodes, width=100,
                                           type="numeric", text="0.95")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_good_low_nodes, width=100,
                                                type="numeric", text="0.975")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_good_high_nodes,
                                                 width=100,
                                                 type="numeric", text="1.025")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_high_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_nodes, width=100,
                                            type="numeric", text="1.05")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_nodes, width=100,
                                                type="numeric", text="1.075")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_high_nodes,
                                                 width=100,
                                                 type="numeric", text="1.1")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["min_max_nodes"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>generators:  | loading % MVA |</code>")
    Sim.gui["color_crit_low_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_low_generators,
                                                     width=100,
                                                     type="numeric", text="60")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_generators,
                                                    width=100,
                                                    type="numeric", text="60")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_low_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_generators, width=100,
                                                type="numeric", text="60")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_generators"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                      bind=func_color_good_low_generators, width=100,
                                                      type="numeric", text="60")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_good_high_generators, width=100,
                                            type="numeric", text="60")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_high_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_generators,
                                                 width=100,
                                                 type="numeric", text="80")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_generators,
                                                     width=100,
                                                     type="numeric", text="100")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_high_generators,
                                                      width=100,
                                                      type="numeric", text="120")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["min_max_generators"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>    - angle: | ° Degrees     |</code>")
    Sim.gui["color_crit_low_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                           bind=func_color_crit_low_generators_angle, width=100,
                                                           type="numeric", text="0.9")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                          bind=func_color_too_low_generators_angle, width=100,
                                                          type="numeric", text="0.925")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_low_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                      bind=func_color_low_generators_angle, width=100,
                                                      type="numeric", text="0.95")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                           bind=func_color_good_low_generators_angle, width=100,
                                                           type="numeric", text="0.975")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                            bind=func_color_good_high_generators_angle,
                                                            width=100,
                                                            type="numeric", text="1.025")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_high_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                       bind=func_color_high_generators_angle, width=100,
                                                       type="numeric", text="1.05")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                           bind=func_color_too_high_generators_angle, width=100,
                                                           type="numeric", text="1.075")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                            bind=func_color_crit_high_generators_angle,
                                                            width=100,
                                                            type="numeric", text="1.1")
    Sim.scene.append_to_caption("<code>|</code>")

    Sim.gui["min_max_generators_angle"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")

    Sim.scene.append_to_caption("<code>cables:      | loading % MVA |</code>")
    Sim.gui["color_crit_low_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_crit_low_cables,
                                                     width=100,
                                                     type="numeric", text="0")

    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_low_cables"] = vp.winput(pos=Sim.scene.caption_anchor,
                                            bind=func_color_too_low_cables, width=100,
                                            type="numeric", text="60")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_low_cables"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                 bind=func_color_low_cables, width=100,
                                                 type="numeric", text="60")  #

    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_low_cables"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                  bind=func_color_good_low_cables, width=100,
                                                  type="numeric", text="60")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_good_high_cables"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                      bind=func_color_good_high_cables, width=100,
                                                      type="numeric", text="60")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_high_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_cables,
                                                 width=100,
                                                 type="numeric", text="80")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_too_high_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_cables,
                                                     width=100,
                                                     type="numeric", text="100")  #
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["color_crit_high_cables"] = vp.winput(pos=Sim.scene.caption_anchor,
                                                      bind=func_color_crit_high_cables,
                                                      width=100,
                                                      type="numeric", text="120")
    Sim.scene.append_to_caption("<code>|</code>")
    Sim.gui["min_max_cables"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")
    #Sim.scene.append_to_caption("<code>losses:      |  </code>")
    #Sim.gui["color_too_low_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_losses, width=100,
    #                                            type="numeric", text="-10.0")  # TODO : get default value
    #Sim.scene.append_to_caption("<code> | </code>")
    #Sim.gui["color_low_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_losses, width=100,
    #                                        type="numeric", text="-5.0")  # TODO : get default value
    #Sim.scene.append_to_caption("<code> | </code>")
    #Sim.gui["color_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_losses, width=100,
    #                                    type="numeric", text="0.0")  # TODO : get value
    #Sim.scene.append_to_caption("<code> | </code>")
    #Sim.gui["color_high_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_losses, width=100,
    #                                         type="numeric", text="5.0")  # TODO : get value
    #Sim.scene.append_to_caption("<code> | </code>")
    #Sim.gui["color_too_high_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_losses,
    #                                             width=100,
    #                                             type="numeric", text="10.0")  # TODO : get value
    #Sim.scene.append_to_caption("<code>| </code>")
    #Sim.gui["min_max_losses"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    #Sim.scene.append_to_caption("\n")
    # Sim.scene.append_to_caption("<code>  gliders:   |  </code>")
    # Sim.gui["box_gliders"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False, disabled=True,
    #                              bind=func_toggle_gliders)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption(
        "entinity   |  visible  |  label  |  radius factor  | radius base  | height factor | height base | dynamic color\n")
    Sim.scene.append_to_caption("<code>Nodes:       | </code>")
    Sim.gui["box_node"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                      bind=func_toggle_nodes)
    Sim.gui["box_node_labels"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=False,
                                             bind=func_toggle_nodes_labels)
    # Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["nodes_factor_r"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_nodes_factor_r, width=50,
                                          # prompt="nodes:",       # prompt does not work with python yet
                                          type="numeric", text="0.0")
    Sim.scene.append_to_caption("<code>       | </code>")
    Sim.gui["nodes_base_r"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_nodes_base_r, width=50,
                                        # prompt="nodes:",       # prompt does not work with python yet
                                        type="numeric", text="4.0")
    Sim.scene.append_to_caption("<code>      | </code>")
    Sim.gui["nodes_factor_h"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_nodes_factor_h, width=50,
                                          # prompt="nodes:",       # prompt does not work with python yet
                                          type="numeric", text="1.0")
    Sim.scene.append_to_caption("<code>      | </code>")
    Sim.gui["nodes_base_h"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_nodes_base_h, width=50,
                                        # prompt="nodes:",       # prompt does not work with python yet
                                        type="numeric", text="0.0")
    Sim.scene.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_nodes"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="", checked=True, bind=func_toggle_dynamic_nodes)
    Sim.scene.append_to_caption("<code>      | </code>\n")
    Sim.scene.append_to_caption("<code>Cables:      | </code>")
    Sim.gui["box_cables"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                        disabled=True,
                                        bind=func_toggle_cables)
    Sim.gui["box_cables_labels"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=False,
                                               bind=func_toggle_cable_labels)
    Sim.gui["factor_cables_r"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_cables_factor_r, width=50,
                                           # prompt="nodes:",       # prompt does not work with python yet
                                           type="numeric", text="0.01")
    Sim.scene.append_to_caption("<code>       | </code>")
    Sim.gui["base_cables_r"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_cables_base_r, width=50,
                                         # prompt="nodes:",       # prompt does not work with python yet
                                         type="numeric", text="0.00")
    Sim.scene.append_to_caption("<code>       | </code>")
    Sim.gui["box_dynamic_cables"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="", checked=True, bind=func_toggle_dynamic_cables)
    Sim.scene.append_to_caption("<code>      | </code>\n")
    Sim.scene.append_to_caption("<code>Losses:      | </code>")
    Sim.gui["box_losses"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False,
                                        disabled=True, bind=func_toggle_losses)
    Sim.scene.append_to_caption("<code>     | </code>")  # because no labels for losses (it's in the cable lable)
    Sim.gui["factor_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_factor_losses, width=50,
                                         type="numeric", text="1.0")
    Sim.scene.append_to_caption("<code> | </code>\n")
    Sim.scene.append_to_caption("<code>Generators:  | ")
    Sim.gui["box_generator"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                           bind=func_toggle_generators)
    Sim.gui["box_generator_labels"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=False,
                                                  bind=func_toggle_generator_labels)
    # Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["generators_factor_r"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_generators_factor_r, width=50,
                                               # prompt="generators:", # prompt does not work with python yet
                                               type="numeric", text="0.0")
    Sim.scene.append_to_caption("<code>       | </code>")
    Sim.gui["generators_base_r"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_generators_base_r, width=50,
                                             # prompt="generators:", # prompt does not work with python yet
                                             type="numeric", text="5.0")

    Sim.scene.append_to_caption("<code>      | </code>")
    Sim.gui["generators_factor_h"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_generators_factor_h, width=50,
                                               # prompt="generators:", # prompt does not work with python yet
                                               type="numeric", text="1.0")
    Sim.scene.append_to_caption("<code>      | </code>")
    Sim.gui["generators_base_h"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_generators_base_h, width=50,
                                             # prompt="generators:", # prompt does not work with python yet
                                             type="numeric", text="0.0")
    Sim.scene.append_to_caption("<code>      | </code>")
    Sim.gui["box_dynamic_generators"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="", checked=True, bind=func_toggle_dynamic_generators)
    Sim.scene.append_to_caption("<code>      | </code>\n")
    Sim.scene.append_to_caption("<code>    -angle:  |")
    Sim.gui["box_generators_angle"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=True,
                                                  bind=func_toggle_generators_angle)
    Sim.scene.append_to_caption("<code>                 |\n </code>")

    Sim.scene.append_to_caption("<code>shadows:   |  </code>")
    Sim.gui["box_shadows"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False,
                                         disabled=True,
                                         bind=func_toggle_shadows)
    Sim.scene.append_to_caption("\n")

    Sim.scene.append_to_caption("<code>grid:        |  </code>")
    Sim.gui["box_grid"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                      bind=func_toggle_grid)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>letters:     |  </code>")
    Sim.gui["box_letters"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                         bind=func_toggle_letters)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>legend:      |  </code>")
    #Sim.gui["box_legend"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False,
    #                                    bind=func_toggle_legend)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>sloped cables|  </code>")
    Sim.gui["box_sloped_cables"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                               bind=func_toggle_sloped_cables)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("Animation (full Simulation) Duration [seconds]:  | ")
    Sim.gui["animation_duration"] = vp.winput(pos=Sim.scene.caption_anchor, text="20", type="numeric", width=50, bind=func_animation_duration)


    # legend:
    #Sim.gui["legend"] = [
    #    vp.label(text="nodes (busbars)", pixel_pos=True, pos=vp.vector(10, 790, 0), color=vp.color.blue, align="left",
    #             box=False, visible=False),
    #    vp.label(text="generators", pixel_pos=True, pos=vp.vector(10, 770, 0), color=vp.color.yellow, align="left",
    #             box=False, visible=False),
    #    vp.label(text="cables (connections)", pixel_pos=True, pos=vp.vector(10, 750, 0), color=vp.color.magenta,
    #             align="left", box=False, visible=False),
    #    vp.label(text="losses (connections)", pixel_pos=True, pos=vp.vector(10, 730, 0), color=vp.color.red,
    #             align="left",
    #             box=False, visible=False)
    #]
    # vp.label(text="hold right mouse button and move to tilt camera. Use mouse wheel to zoom. Use shift and mouse button to pan",
    #         pixel_pos=True, pos=vp.vector(50,790,0), color=vp.color.white, align="left", box=False")


def mousebutton_down():
    if Sim.mode != "arrange":
        return
    Sim.selected_object = Sim.scene.mouse.pick
    if Sim.selected_object is None:
        Sim.dragging = False
    else:
        Sim.dragging = True


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
    # keep inside of grid
    if not (-Sim.grid_max / 2 <= Sim.scene.mouse.pos.x <= Sim.grid_max / 2):
        o.pos.x = max(-Sim.grid_max / 2, o.pos.x)
        o.pos.x = min(Sim.grid_max / 2, o.pos.x)
    if not (-Sim.grid_max / 2 <= Sim.scene.mouse.pos.z <= Sim.grid_max / 2):
        o.pos.z = max(-Sim.grid_max / 2, o.pos.z)
        o.pos.z = min(Sim.grid_max / 2, o.pos.z)
    #match o.what:
    if o.what ==  "node":
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
            for (i2, j2, k2), subdisc in Sim.sub_nodes.items():
                if (i2 != i) and (j2 != i):
                    continue
                start = Sim.nodes[i2].pos
                end = Sim.nodes[j2].pos
                diff = end - start
                pointlist = []
                pointlist.append(start)
                for k in range(1, Sim.number_of_sub_cables):  # 6 subnodes
                    p = start + k * vp.norm(diff) * vp.mag(diff) / (Sim.number_of_sub_cables)  # divide by
                    Sim.sub_nodes[(i2, j2, k)].pos = p
                    pointlist.append(p)
                    # TODO: sub-optimal code, iterates more often then necessary over all subdiscs
                    if k == int(Sim.number_of_sub_cables / 2):
                        Sim.labels[f"cable {i2}-{j2}"].pos = p
                pointlist.append(end)
                for number, point in enumerate(pointlist):
                    Sim.sub_cables[(i2, j2)].modify(number, pos=point)
            # exist connected generator?
            if o.number in Sim.generator_lines.keys():
                Sim.generator_lines[o.number].modify(0, pos=o.pos)
    elif o.what == "generator":
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
            if k == int(Sim.number_of_sub_cables / 2):
                Sim.labels[f"cable {i}-{j}"].pos = o.pos
    else:
            pass  # something else got dragged
            # elif o.what == "subdisc":
            #    i,j,k = o.number
            #    for subdisc in Sim.sub_discs[i,j].values():


# def mouseclick(event):
#    Sim.selected_object = Sim.scene.mouse.pick


def create_stuff():
    # axis arrows with letters
    vp.arrow(axis=vp.vector(1, 0, 0), color=vp.color.red, pickable=False)
    vp.arrow(axis=vp.vector(0, 1, 0), color=vp.color.green, pickable=False)
    vp.arrow(axis=vp.vector(0, 0, 1), color=vp.color.blue, pickable=False)
    vp.text(pos=vp.vector(1.5, 0, 0), color=vp.color.red, text="x", height=0.25, pickable=False)
    vp.text(pos=vp.vector(0, 1.5, 0), color=vp.color.green, text="y", height=0.25, pickable=False)
    vp.text(pos=vp.vector(0, 0, 1.5), color=vp.color.blue, text="z", height=0.25, pickable=False)
    # ---- create ground floor ----
    # Sim.scene.visible = False
    vp.box(  # pos=vp.vector(Sim.grid_max / 2, -0.05, Sim.grid_max / 2),
        pos=vp.vector(0, -0.1, 0),
        size=vp.vector(Sim.grid_max, 0.15, Sim.grid_max),
        # color=vp.color.cyan,
        # opacity=0.5,
        texture={'file': os.path.join("assets", 'map001.png'),

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
    for x in range(-Sim.grid_max // 2, Sim.grid_max // 2, Sim.grid_step):
        Sim.grid.append(vp.curve(pos=[vp.vector(x, 0, -Sim.grid_max // 2), vp.vector(x, 0, Sim.grid_max // 2)],
                                 color=vp.color.black, radius=0.01, pickable=False))
    for z in range(-Sim.grid_max // 2, Sim.grid_max // 2, Sim.grid_step):
        Sim.grid.append(vp.curve(pos=[vp.vector(-Sim.grid_max // 2, 0, z), vp.vector(Sim.grid_max // 2, 0, z)],
                                 color=vp.color.black, radius=0.01, pickable=False))
    # ====
    # create an inner circle with all nodes (busbars, blue cylinder)
    pointer = vp.vector(Sim.radius["geo1"], 0, 0)
    for i, number in enumerate(Data.node_numbers):
        # CREATE NODE
        end_point_1 = vp.vector(0, 0, 0) + pointer  # origin of cylinder for node
        end_point_2 = vp.vector(0, 0, 0) + pointer.norm() * (
                Sim.radius["geo1"] + 5)  # origin of label for node # TODO: 5 should be parameter
        Sim.nodes[number] = vp.cylinder(pos=vp.vector(end_point_1.x, 0, end_point_1.z),
                                        color=Sim.colors["nodes"],
                                        radius=Sim.base["nodes_r"],
                                        axis=vp.vector(0, 2, 0),
                                        pickable=True,
                                        # texture={'file': os.path.join("assets", 'energy1.png'),
                                        #         # 'bumpmap': bumpmaps.stucco,
                                        #         'place': 'right',
                                        #         'flipx': False,
                                        #         'flipy': False,
                                        #         'turn': -1,
                                        #         },
                                        )
        #Sim.letters[f"node {number}"] = vp.text(text=f"N{number}", color=vp.color.black,
        #                                        pos=vp.vector(end_point_1.x, 3, end_point_1.z),
        #                                        billboard=True, emissive=True, pickable=False, align="center")
        Sim.letters[f"node {number}"] = vp.label(text=f"N{number}", color=vp.color.white,
                                                pos=vp.vector(end_point_1.x, 3, end_point_1.z),
                                                 opacity=0.1, box=False,
                                                #billboard=True, emissive=True,
                                                 pickable=False, align="center")

        Sim.nodes[number].what = "node"
        Sim.nodes[number].number = number
        Sim.labels[f"node {number}"] = vp.label(pos=end_point_2, text=f"n {number}", height=10,
                                                color=vp.color.white,
                                                visible=False)
        # add (wind) generators in outer circle (if number is matching)
        if number in Data.generator_numbers:
            # CREATE GENERATOR
            end_point_3 = vp.vector(0, 0, 0) + pointer.norm() * Sim.radius["geo2"]  # origin of cylinder for generator
            end_point_4 = vp.vector(0, 0, 0) + pointer.norm() * (
                    Sim.radius["geo2"] + 0.5)  # origin of label for generator # TODO: 0.5 should be parameter
            Sim.generators[number] = vp.cylinder(pos=vp.vector(end_point_3.x, 0, end_point_3.z),
                                                 color=Sim.colors["generators"],
                                                 radius=Sim.base["generators_r"],
                                                 axis=vp.vector(0, 3, 0),
                                                 pickable=True,
                                                 # texture={'file': os.path.join("assets", 'energy2.png'),
                                                 #         # 'bumpmap': bumpmaps.stucco,
                                                 #         'place': 'right',
                                                 #         'flipx': False,
                                                 #         'flipy': False,
                                                 #         'turn': -1,
                                                 #         },
                                                 )
            Sim.generators[number].what = "generator"
            Sim.generators[number].number = number
            Sim.letters[f"generator {number}"] = vp.label(text=f"G{number}", color=vp.color.white,
                                                         pos=vp.vector(end_point_3.x, 4, end_point_3.z),
                                                         opactiy=0.1, border=False,
                                                         #billboard=True, emissive=True,
                                                         pickable=False, align="center")

            Sim.labels[f"generator {number}"] = vp.label(pos=vp.vector(end_point_4.x, 0, end_point_4.z),
                                                         text=f"g {number}",
                                                         height=10,
                                                         color=vp.color.white,
                                                         visible=False,
                                                         )
            # pointer0 always points like x-axis
            # ------- pointers for angle ------
            start = vp.vector(end_point_3.x, end_point_3.y - 0, end_point_3.z)
            end1 = start + vp.vector(0,0,-Sim.radius["pointer0"])
            end2 = start + vp.vector(0,0,-Sim.radius["pointer1"])
            Sim.pointer0[number] = vp.arrow(pos=start,
                                            axis=end1 - start,
                                            color=vp.color.red,
                                            shaftwidth=1.0,
                                            # headwidth= 3,
                                            pickable=False,
                                            )
            Sim.pointer1[number] = vp.arrow(pos=start,
                                            axis=end2 - start,
                                            color=vp.color.orange,
                                            round=True,
                                            shaftwidth=0.5,
                                            pickable=False,
                                            # headwidth = 0.5
                                            )
            # ---- disc ----
            Sim.discs[number] = vp.extrusion(path=[start, vp.vector(start.x, start.y + 0.1, start.z)],
                                             shape=vp.shapes.circle(radius=Sim.base["generators_r"] + 5,
                                                                    angle1=vp.radians(170),
                                                                    angle2=vp.radians(-170)),
                                             pickable=False)
            # make automatic connection from generator to node
            Sim.generator_lines[number] = vp.curve(vp.vector(end_point_1.x, 0.1, end_point_1.z),
                                                   vp.vector(end_point_3.x, 0.1, end_point_3.z),
                                                   radius=0.1,
                                                   color=vp.color.orange,
                                                   pickable=False)

        # prepare clock-pointer for next number
        pointer = vp.rotate(pointer,
                            angle=vp.radians(360 / len(Data.node_numbers)),
                            axis=vp.vector(0, 1, 0),
                            )

    # ----- create CABLES ----
    for i, to_number_list in Data.cables_dict.items():
        for j in to_number_list:
            from_node = Sim.nodes[i]
            to_node = Sim.nodes[j]
            if (j, i) in Sim.cables.keys():
                continue  # create only one direction
            Sim.cables[(i, j)] = vp.curve(radius=0.1, color=vp.color.orange, pos=[from_node.pos, to_node.pos],
                                          pickable=False)
            Sim.cables[(i, j)].number = (i, j)  # tuple of both node numbers
            Sim.cables[(i, j)].what = "cable"
            # divide each  cable (0,1) into several subcables by creating  subnodes (first and last subnodes are the cable nodes)
            start = from_node.pos
            end = to_node.pos
            diff = end - start
            # create sub-discs
            # p = vp.vector(start.x, start.y, start.z)
            pointlist = []  # for sub-cables
            pointlist.append(start)
            for k in range(1, Sim.number_of_sub_cables):  # 6 subnodes
                p = start + k * vp.norm(diff) * vp.mag(diff) / (Sim.number_of_sub_cables)  # divide by
                subdisc = vp.cylinder(pos=p, radius=Sim.base["nodes_r"] / 3, color=vp.color.magenta,
                                      axis=vp.vector(0, 3, 0),
                                      pickable=True)
                subdisc.number = (i, j, k)
                subdisc.what = "subnode"
                Sim.sub_nodes[(i, j, k)] = subdisc
                pointlist.append(subdisc.pos)
                # label in the middle subnode
                if k == int(Sim.number_of_sub_cables / 2):
                    Sim.labels[f"cable {i}-{j}"] = vp.label(pos=subdisc.pos,
                                                            text=f"c {i}-{j}",
                                                            height=10,
                                                            color=vp.color.white,
                                                            visible=False,
                                                            )
            pointlist.append(end)
            # -- create sub-cables between sub-discs
            Sim.sub_cables[(i, j)] = vp.curve(color=vp.color.magenta, radius=0.15, pos=pointlist, pickable=False)


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
    for number in Sim.nodes:
        s = Data.df[col_name_node(number)]
        mi = s.min()
        ma = s.max()
        # print("min max for node ",number,":", mi, ma)
        if Data.nodes_min is None:
            Data.nodes_min = mi
        elif mi < Data.nodes_min:
            Data.nodes_min = mi
        if Data.nodes_max is None:
            Data.nodes_max = ma
        elif ma > Data.nodes_max:
            Data.nodes_max = ma
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
    for number in Sim.generators:
        s = Data.df[col_name_angle(number)]
        mi = s.min()
        ma = s.max()
        if Data.generators_angle_min is None:
            Data.generators_angle_min = mi
        elif mi < Data.generators_angle_min:
            Data.generators_angle_min = mi
        if Data.generators_angle_max is None:
            Data.generators_angle_max = ma
        elif ma > Data.generators_angle_max:
            Data.generators_angle_max = ma
    Sim.gui[
        "min_max_generators_angle"].text = f"<code>{Data.generators_angle_min:.2f} / {Data.generators_angle_max:.2f}</code>"
    # ----- generators: 60 ,  80 ,  100, 120
    Sim.colors["crit_low_generators"] = 0
    Sim.colors["too_low_generators"] = 60
    Sim.colors["low_generators"] = 60
    Sim.colors["good_low_generators"] = 60
    Sim.gui["color_good_high_generators"] = 60
    Sim.colors["good_high_generators"] = 60
    Sim.gui["color_high_generators"] = 80
    Sim.colors["high_generators"] = 80
    Sim.gui["color_too_high_generators"] = 100
    Sim.colors["too_high_generators"] = 100
    Sim.gui["color_crit_high_generators"] = 120
    Sim.colors["crit_high_generators"] = 120
    for number in Sim.generators:
        # use loading value
        s = Data.df[f"loading_gen_{number}"]
        mi = s.min()
        ma = s.max()
        if Data.generators_min is None:
            Data.generators_min = mi
        elif mi < Data.generators_min:
            Data.generators_min = mi
        if Data.generators_max is None:
            Data.generators_max = ma
        elif ma > Data.generators_max:
            Data.generators_max = ma
    Sim.gui["min_max_generators"].text = f"<code>{Data.generators_min:.2f} / {Data.generators_max:.2f}</code>"
    # -------- cables: 60, 80, 100, 120 ------------
    Sim.colors["crit_low_cables"] = 0
    Sim.colors["too_low_cables"] = 60
    Sim.colors["low_cables"] = 60
    Sim.colors["good_low_cables"] = 60
    Sim.gui["color_good_high_cables"] = 60
    Sim.colors["good_high_cables"] = 60
    Sim.gui["color_high_cables"] = 80
    Sim.colors["high_cables"] = 80
    Sim.gui["color_too_high_cables"] = 100
    Sim.colors["too_high_cables"] = 100
    Sim.gui["color_crit_high_cables"] = 120
    Sim.colors["crit_high_cables"] = 120

    for (number, targetlist) in Data.cables_dict.items():
        for target in targetlist:
            s = Data.df[f"loading_cable_{number}_{target}"]
            mi = s.min()
            ma = s.max()
            if Data.cables_min is None:
                Data.cables_min = mi
            elif mi < Data.cables_min:
                Data.cables_min = mi
            if Data.cables_max is None:
                Data.cables_max = ma
            elif ma > Data.cables_max:
                Data.cables_max = ma
        Sim.gui["min_max_cables"].text = f"<code>{Data.cables_min:.2f} / {Data.cables_max:.2f}</code>"




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
    #if not Sim.animation_running:
    #    return
    # -------- nodes --------
    for number, cyl in Sim.nodes.items():
        try:
            volt = Data.df[col_name_node(number)][Sim.i]
        except KeyError:
            print(f"KeyError: could not found Volt in line {Sim.i} column {Data.df[col_name_node(number)]}")
            continue
        cyl.axis = vp.vector(0, volt * Sim.factor["nodes_h"] + Sim.base["nodes_h"], 0)
        cyl.radius = volt * Sim.factor["nodes_r"] + Sim.base["nodes_r"]
        # conditional color
        cyl.color = update_color(volt, "nodes")
        Sim.labels[f"node {number}"].text = f"n {number}: {volt} V"
        Sim.letters[f"node {number}"].pos.y = cyl.axis.y + 1
        # --- sloped cables ? ----
        if Sim.sloped_cables:
            #for (i,j), curve in Sim.sub_cables.items():
            for (i,j) in Sim.cables:
                yi = Sim.nodes[i].axis.y
                yj = Sim.nodes[j].axis.y
                n = Sim.number_of_sub_cables +1
                delta = (yj - yi) / n
                ###print(i,j, delta)
                #for k in range(curve.npoints-1):
                # TODO: flexible number of sub-cables?
                for k in range(n-1):
                    y1 = yi + k * delta
                    y2 = yi + (k+1) * delta
                    if (i,j,k) in Sim.arrows_ij:
                        Sim.arrows_ij[(i,j,k)].pos.y = y1
                        Sim.arrows_ij[(i,j,k)].axis.y = y2 - y1
                    else:
                        print("key ",i,j,k, "not found in Sim.arrows_ij")
                    if (i,j,k) in Sim.arrows_ji:
                        Sim.arrows_ji[(i, j, k)].pos.y = y1
                        Sim.arrows_ji[(i, j, k)].axis.y = y2 - y1
                    elif (j,i,k) in Sim.arrows_ji:
                        Sim.arrows_ji[(j, i, k)].pos.y = y1
                        Sim.arrows_ji[(j, i, k)].axis.y = y2 - y1
                    else:
                        print(f"key {i}-{j}-{k} / {j}-{k}-{i}:  both not found in Sim.arrows_ji")
                #    oldpos = curve.point(k)["pos"]
                #    curve.modify(k, pos=vp.vector(oldpos.x, yi+delta*k ,oldpos.z))
        else:
            # all curves are at y zero ?
            pass

    # --------- generators ----------------
    for number, cyl in Sim.generators.items():
        try:
            power = Data.df[col_name_power(number)][Sim.i]
            g_angle = Data.df[col_name_angle(number)][Sim.i]
        except KeyError:
            print(
                f"KeyError: could not find power / angle value in line {Sim.i} for columns {col_name_power(number)} / {col_name_angle(number)}")
            continue
        cyl.axis = vp.vector(0, power * Sim.factor["generators_h"] + Sim.base["generators_h"], 0)
        cyl.radius = power * Sim.factor["generators_r"] + Sim.base["generators_r"]
        # ------- pointers for angle --------
        # Sim.pointer0[number].y = cyl.pos.y + cyl.axis.y + 1
        # Sim.pointer1[number].y = cyl.pos.y + cyl.axis.y + 1
        # TODO: compare with angle from previous frame, only move when necessary
        # reset pointer1
        p0 = Sim.pointer0[number]
        p1_axis_vector = vp.vector(0,0,-Sim.radius["pointer1"])
        p1_axis_vector = vp.rotate(p1_axis_vector, angle=vp.radians(-g_angle), axis=vp.vector(0, 1, 0))
        Sim.pointer1[number].axis = vp.vector(p1_axis_vector.x, p1_axis_vector.y, p1_axis_vector.z)
        Sim.pointer1[number].pos.y = cyl.axis.y
        #Sim.discs[number].color = update_color(g_angle, "generators_angle")
        Sim.pointer1[number].color = update_color(g_angle, "generators_angle")
        Sim.labels[f"generator {number}"].text = f"g {number}: {power} MW, {g_angle}°"
        Sim.letters[f"generator {number}"].pos.y = cyl.axis.y + 1
        # print(Sim.i, number, power)
        # color for generator, calculate % mva value
        """
        loading = % of MVA -> its for color coding the cables (* 100)
        # MVA calculation:
        % loading = sqrt (P^2 + Q^2) / MVArating
        """
        #p = power
        #q = 0
        #mva_node_number = Data.nodes_to_generators[number]
        #loading = ((p**2 + q**2)**0.5)/Data.mva_generators[mva_node_number] * 100
        loading = Data.df[f"loading_gen_{number}"][Sim.i]

        #print(f"loading % of Mva for generator {number}: p = {power}, q=0, mva_number= {mva_node_number} mva= {Data.mva_generators[mva_node_number]} loading is: {loading}")
        # assume that loading must be multiplied by 100 again...
        cyl.color = update_color(loading, "generators")

    # ------ cables -----
    #
    for number, targetlist in Data.cables_dict.items():
        for target in targetlist:
            # get power value from dataframe
            try:
                power1 = Data.df[col_name_cable(number, target)][Sim.i]
                power2 = Data.df[col_name_cable(target, number)][Sim.i]
            except KeyError:
                print(
                    f"KeyError: could not fine power1, power2 value(s) in line {Sim.i} for columns {col_name_cable(number, target)}, {col_name_cable(target, number)}")
                continue
            loss = abs(power1 + power2)
            # TODO: mva calculation


            if (number, target) in Data.mva_cables:
                mva_rating = Data.mva_cables[(number, target)]
            elif (target,number) in Data.mva_cables:
                mva_rating = Data.mva_cables[(target, number)]
            else:
                print("could not find mva_rating (cables) for", number, target)
                continue



            numtar = all((power1 > 0, power2 < 0))  # True if flow from number to target
            power = power1 if numtar else power2
            # print(number, target, "power is:", power1, power2, loss, numtar)
            #p = power
            #q = 0
            #loading = (p ** 2 + q ** 2) ** 0.5 / mva_rating * 100
            loading = Data.df[f"loading_cable_{number}_{target}"][Sim.i]
            # print(f"loading calc. for cable {number} {target}: p={power} q=0 mva_rating={mva_rating} loading =  {loading}")
            # mva: {(1, 2): 600, (1, 39): 1000, (2, 3): 500, (2, 25): 500, (2, 30): 900, (3, 4): 500, (3, 18): 500, (4, 5): 600, (4, 14): 500, (5, 6): 1200, (5, 8): 900, (6, 7): 900, (6, 11): 480, (6, 31): 1800, (7, 8): 900, (8, 9): 900, (9, 39): 900, (10, 11): 600, (10, 13): 600, (10, 32): 900, (12, 11): 500, (12, 13): 500, (13, 14): 600, (14, 15): 600, (15, 16): 600, (16, 17): 600, (16, 19): 600, (16, 21): 600, (16, 24): 600, (17, 18): 600, (17, 27): 600, (19, 20): 900, (19, 33): 900, (20, 34): 900, (21, 22): 900, (22, 23): 600, (22, 35): 900, (23, 24): 600, (23, 36): 900, (25, 26): 600, (25, 37): 900, (26, 27): 600, (26, 28): 600, (26, 29): 600, (28, 29): 600, (29, 38): 1200}

            if f"cable {number}-{target}" in Sim.labels:
                Sim.labels[f"cable {number}-{target}"].text = f"c {number}-->{target}: {power} ({loss}) W {numtar} \nloading: {loading}"
                # ---- new- --
                for k in range(Sim.number_of_sub_cables):
                    # TODO: flexible number of sub_cables?
                    # TODO: cable_factor

                    if Sim.gui["box_cables"].checked:
                        # make visible/invisible depending on power value
                        # get mva value and color value

                        if numtar:
                            Sim.arrows_ij[(number, target, k)].visible = True
                            Sim.arrows_ji[(number, target, k)].visible = False
                            Sim.arrows_ij[(number, target, k)].shaftwidth = power * Sim.factor["cables_r"] + Sim.base[
                                "cables_r"]
                            Sim.arrows_ij[(number, target, k)].headwidth = power * Sim.factor["cables_r"] + Sim.base[
                                "cables_r"] + 1
                            # dynamic color?
                            Sim.arrows_ij[(number, target, k)].color = update_color(loading, "cables")
                        else:
                            Sim.arrows_ij[(number, target, k)].visible = False
                            Sim.arrows_ji[(number, target, k)].visible = True
                            Sim.arrows_ji[(number, target, k)].shaftwidth = power * Sim.factor["cables_r"] + Sim.base[
                                "cables_r"]
                            Sim.arrows_ji[(number, target, k)].headwidth = power * Sim.factor["cables_r"] + Sim.base[
                                "cables_r"] + 1
                            Sim.arrows_ji[(number, target, k)].color = update_color(loading , "cables")
                    else:
                        # make all invisible
                        for a in Sim.arrows_ij.values():
                            a.visible = False
                        for a in Sim.arrows_ji.values():
                            a.visible = False


def main():
    # Sim.scene.bind("click", mouseclick )
    Sim.scene.bind("mousedown", mousebutton_down)
    Sim.scene.bind("mousemove", mouse_move)
    Sim.scene.bind("mouseup", mousebutton_up)

    camera_to_topdown()
    simtime = 0
    time_since_framechange = 0
    # frame_number = 0  # Sim.i
    while True:
        vp.rate(Sim.fps)
        simtime += Sim.dt
        time_since_framechange += Sim.dt
        # print("simtime", simtime)

        # text = f"mouse: {Sim.scene.mouse.pos} discs: "
        # Sim.status.text = text
        # Sim.status2.text = f"selected obj: {Sim.selected_object}, drag: {Sim.dragging},"
        # play animation
        if not Sim.animation_running:
            continue

        if time_since_framechange > Sim.frame_duration:
            time_since_framechange = 0
            Sim.i += 1
            if Sim.i >= len(Data.df):
                Sim.i = 0
            # update widgets
            Sim.gui["label_frame"].text = f"{Sim.i}"
            Sim.gui["frameslider"].value = Sim.i
            # get the data from df (for y values)
            update_stuff()


if __name__ == "__main__":
    create_data()
    read_mva_values()
    read_nodes_to_generators()
    calculate_loading()
    create_stuff()
    load_layout()
    create_widgets()
    get_Data_min_max()
    main()
