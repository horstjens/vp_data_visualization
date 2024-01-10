import pandas as pd
import vpython as vp

"""
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

"""

# create a pandas dataframe from csv
df = pd.read_csv("raw_data.csv")
# take some interesting columns (called 'series' in pandas)

time_col_name = "Time(s)"
generator_numbers = [i for i in range(30, 40)]  # numbers from 30 to 39


# col_name for generator 30 angle: "ANGL 30[30 1.0000]1"
# col_name for generator 30 power: "POWR 30[30 1.0000]1"
## angle 39 is the reference angle (0)

def col_name_angle(generator_number):
    return f"ANGL {generator_number}[{generator_number} 1.0000]1"


def col_name_power(generator_number):
    return f"POWR {generator_number}[{generator_number} 1.0000]1"


node_numbers = [i for i in range(1, 40)]  # numbers from 1 to 39


# col_name for node 1: "VOLT 1 [1 1.0000]"

def col_name_node(node_number):
    return f"VOLT {node_number} [{node_number} 1.0000]"


cable_col_names = [raw_name for raw_name in df if raw_name.startswith("POWR ") and (" TO " in raw_name)]
print(cable_col_names)


# col_name for cable from 3 to 18: "POWR 3 TO 18 CKT '1 '"

def col_name_cable(from_number, to_number):
    return f"POWR {from_number} TO {to_number} CKT '1 '"


# cable connections (only one direction is necessary for now)
# SOME COL NAMES SEEM TO EXIST TWICE OR MORE OFTEN IN THE SPREADSHEET
# NODE 261 does not exist but connection to it exist
# NODE 281 does not exist but connection to it exist
##cables1 = set()
cables_dict = {}
duplicate_colnames = []
for colname in cable_col_names:
    words = colname.split(" ")
    c_from = int(words[1])
    c_to = int(words[3])
    if c_from not in node_numbers:
        continue
    if c_to not in node_numbers:
        continue
    print(colname, c_from, c_to)
    if c_from in cables_dict:
        if c_to in cables_dict[c_from]:
            print("strange error: duplicate column:", colname)
            duplicate_colnames.append(colname)
        else:
            cables_dict[c_from].append(c_to)
    else:
        cables_dict[c_from] = [c_to]
    ##if (c_to, c_from) not in cables1:
    ##    cables1.add((c_from, c_to))

# print(cables1)  # a set of 48 connections ( 96 for both directions, including the losses )
print(cables_dict)
print("duplicate colnames:")
print(duplicate_colnames)
# --------------------- location of nodes and generators -------------
# idea: arrange all nodes in a big circle
# arrange the generators in an even bigger circle with the sam origin



# helper functions for vpython widgets

def button_start_func(b):
    print("start was pressed", b.text)


def slider1_func(b):
    print("slider is set to ", b.value)
    # Sim.connAB.pos.y = power_ab[b.value]
    Sim.label3.text = str(b.value)


def check1_func(b):
    """toggles labels for nodes"""
    for name, value in Sim.labels.items():
        if name.startswith("node"):
            Sim.labels[name].visible = b.checked


def check2_func(b):
    """toggles labels for generators"""
    for name, value in Sim.labels.items():
        if name.startswith("generator"):
            Sim.labels[name].visible = b.checked


def check3_func(b):
    """toggles labels for cables"""
    for name, value in Sim.labels.items():
        if name.startswith("cable"):
            Sim.labels[name].visible = b.checked


def check4_func(b):
    """toggles visibility for base cables"""
    for name in Sim.cables:
        Sim.cables[name].visible = b.checked


class Sim:
    """all important vpython constants are in this class, to make referencing from outside more easy"""
    GRID_MAX = 250
    GRID_STEP = 25
    NODE_RADIUS = 4  # how big a node is
    GENERATOR_RADIUS = 8
    geo_radius1 = 200
    geo_radius2 = 225
    scene = vp.canvas(title='Bruce training data',
                      caption="caption area",
                      width=800, height=600,
                      center=vp.vector(0, 0, 0),
                      background=vp.color.black,
                      )

    fps = 60
    dt = 1 / fps
    mini_arrow_length = 5
    scene.append_to_title("\n")
    labels = {}
    nodes = {}
    generators = {}
    cables = {} # base arrow from origin to target, will be invisible
    mini_arrows = {}
    # ---- widgets above window in title area -------
    button_start = vp.button(bind=button_start_func, text="Start", pos=scene.title_anchor)
    label1 = vp.wtext(pos=scene.title_anchor, text="---hallo---")
    scene.append_to_title("\n")
    label2 = vp.wtext(pos=scene.title_anchor, text="timeframe:  ")
    slider1 = vp.slider(pos=scene.title_anchor, bind=slider1_func, min=0, max=len(df),
                        length=700, step=1)
    label3 = vp.wtext(pos=scene.title_anchor, text=" 0")
    label4 = vp.wtext(pos=scene.title_anchor, text=f" of {len(df)} ")
    scene.append_to_title("\n")
    # ---- widgets below window in caption area
    box1 = vp.checkbox(pos=scene.caption_anchor, text="show node labels", checked=True, bind=check1_func)
    box2 = vp.checkbox(pos=scene.caption_anchor, text="show generator labels", checked=True, bind=check2_func)
    box3 = vp.checkbox(pos=scene.caption_anchor, text="show cable labels", checked=True, bind=check3_func)
    box4 = vp.checkbox(pos=scene.caption_anchor, text="show base cables", checked=True, bind=check4_func)


# make 3 arrows from origin
xarrow = vp.arrow(axis=vp.vector(10, 0, 0), color=vp.color.red)
yarrow = vp.arrow(axis=vp.vector(0, 10, 0), color=vp.color.green)
zarrow = vp.arrow(axis=vp.vector(0, 0, 10), color=vp.color.blue)
# make a grid
for i in range(-Sim.GRID_MAX, Sim.GRID_MAX + 1, Sim.GRID_STEP):
    vp.curve(vp.vector(i, 0, -Sim.GRID_MAX), vp.vector(i, 0, Sim.GRID_MAX), radius=0.1, color=vp.color.cyan)
    vp.curve(vp.vector(-Sim.GRID_MAX, 0, i), vp.vector(Sim.GRID_MAX, 0, i), radius=0.1, color=vp.color.cyan)

# create an inner circle with all nodes (blue cylinder)
pointer = vp.vector(Sim.geo_radius1, 0, 0)
for i, number in enumerate(node_numbers):
    end_point_1 = vp.vector(0, 0, 0) + pointer  # origin of cylinder for node
    end_point_2 = vp.vector(0, 0, 0) + pointer.norm() * (Sim.geo_radius1 + 5)  # origin of label for node
    Sim.nodes[number] = vp.cylinder(pos=vp.vector(end_point_1.x, 0, end_point_1.z),
                                    color=vp.color.blue,
                                    radius=Sim.NODE_RADIUS,
                                    axis=vp.vector(0, 24, 0),
                                    )

    Sim.labels[f"node {number}"] = vp.label(pos=end_point_2, text=f"n {number}", height=10, color=vp.color.white)
    # add generators in outer circle (if number is matching)
    if number in generator_numbers:
        end_point_3 = vp.vector(0, 0, 0) + pointer.norm() * Sim.geo_radius2  # origin of cylinder for generator
        end_point_4 = vp.vector(0, 0, 0) + pointer.norm() * (Sim.geo_radius2 + 5)  # origin of label for generator
        Sim.generators[number] = vp.cylinder(pos=vp.vector(end_point_3.x, 0, end_point_3.z),
                                             color=vp.color.yellow,
                                             radius=Sim.GENERATOR_RADIUS,
                                             axis=vp.vector(0, 48, 0),
                                             )
        Sim.labels[f"generator {number}"] = vp.label(pos=vp.vector(end_point_4.x, 0, end_point_4.z),
                                                     text=f"g {number}",
                                                     height=10,
                                                     color=vp.color.white,
                                                     )
        # make automatic connection from generator to node
        vp.curve(vp.vector(end_point_1.x, 2, end_point_1.z),
                 vp.vector(end_point_3.x, 2, end_point_3.z),
                 radius=2,
                 color=vp.color.orange)

    # prepare clock-pointer for next number
    pointer = vp.rotate(pointer,
                        angle=vp.radians(360 / len(node_numbers)),
                        axis=vp.vector(0, 1, 0),
                        )

# print("yes")

# create ALL cables
for o_number, t_numbers in cables_dict.items():
    # get the value
    ov = vp.vector(Sim.nodes[o_number].pos.x,Sim.nodes[o_number].pos.y,Sim.nodes[o_number].pos.z)
    for t in t_numbers:
        tv = vp.vector(Sim.nodes[t].pos.x, Sim.nodes[t].pos.y, Sim.nodes[t].pos.z)
        # base cable
        Sim.cables[(o_number, t)] = vp.arrow(pos=ov, axis=tv-ov, color=vp.color.green, shaftwidth=1)
        # base cable lable
        Sim.labels[f"cable {o_number} {t}"] = vp.label(pos=ov + vp.norm(tv-ov) * vp.mag(tv-ov)/2,
                                                       text=f"c {o_number} {t}",
                                                       height=10,
                                                       color=vp.color.white)
        # little arrows
        Sim.mini_arrows[(o_number, t)] = []  # empty list
        start = vp.vector(ov.x, ov.y, ov.z)
        end = start + vp.norm(tv-ov) * Sim.mini_arrow_length
        Sim.mini_arrows[(o_number,t)].append(vp.arrow(pos=vp.vector(start.x, start.y, start.z),
                                                      axis=end-start,
                                                      color = vp.color.magenta))
        mini_counter = 1
        end += vp.norm(tv - ov) * Sim.mini_arrow_length * 1.5
        while (vp.mag(end-ov) + Sim.mini_arrow_length) < vp.mag(tv-ov):
            start = vp.vector(end.x, end.y, end.z)
            end += vp.norm(tv-ov) * Sim.mini_arrow_length
            mini_counter += 1
            Sim.mini_arrows[(o_number, t)].append(vp.arrow(pos=vp.vector(start.x, start.y, start.z),
                                                           axis=end - start,
                                                           color=vp.color.purple if mini_counter % 2 == 0 else vp.color.magenta)
                                                  )








while True:
    vp.rate(Sim.fps)
