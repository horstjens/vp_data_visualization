import os.path
import pandas as pd
import random
import vpython as vp
#TODO Bruce: cylinders fix y axis, dynamic radius. Flyers inside cable (change cable radius, make it transparent, flyers z-axis?)
# fixme: besserer mini richtungswechsel (update)
# TODO: better widget layout

"""moving a disc in a 2d plane using the mouse,
and moving the sub-lines as well
curves have special modify method for each point, see https://www.glowscript.org/docs/VPythonDocs/curve.html

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
Angle	deg	        -180	-170	-160	-150	  150	 160	  170	  180
Voltage	pu	        0.9	   0.925	0.95	0.975	1.025	1.05	1.075	    1.1
Power	% of MVA 	                                   60	  80	  100	  120
Losses	%	                                            2	   3	    4	    5

# wind, node: cylinder grows in y axis
# cables: cylinder radius grows (xz axis)
# cables: connect top y value of their connected cylinders. arrows between each subnode. 
# losses: ? arrows up/down?


       
# TODOS
+color scale every "value" on a scale between green (normal) to red (upper limit) or blue (lower-limit)
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


class Sim:
    mode = "arrange"
    glider_number = 1
    selected_object = None
    animation_running = False
    dragging = False
    scene = vp.canvas(title='v 015 ',
                      # caption="coordinates: ",
                      width=1200, height=800,
                      center=vp.vector(0, 0, 0),
                      background=vp.color.gray(0.8),
                      align = "left", # caption is to the right?
                      )
    grid_max = 200
    grid_step = 10
    number_of_sub_cables = 6  # sub-nodes = sub_cables -1
    fps = 60
    dt = 1 / fps
    i = 1  # line in data sheet
    gui = {}  # widgets for gui
    #status = vp.label(text="nothing", pos=vp.vector(10, 10, 0), color=vp.color.green, pixel_pos=True, align="left")
    #status2 = vp.label(text="nada", pos=vp.vector(10, 50, 0), color=vp.color.green, pixel_pos=True, align="left")
    # colors = (vp.color.red, vp.color.green, vp.color.blue, vp.color.yellow)
    colors = {"nodes": vp.color.blue,
              "generators": vp.color.yellow,
              "cables": vp.color.gray(0.5),
              "mini_arrow": vp.color.purple,
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
    factor = {"generators": 1.0,
              "nodes": 1.0,
              "cables": 0.01,
              "arrows": 0.01,
              "arrows_x": 0.01,
              "arrows_z": 0.01,
              "losses": 1.0,
              }
    visible = {"generators": True,
               "nodes": True,
               "cables": True,
               "flyers": False,
               }
    radius = {"generators": 5,
              "nodes": 4,
              "pointer0": 8 + 0,  # for wind angle
              "pointer1": 8 + 0,  # for wind angle
              "geo1": grid_max / 2 - 25,
              "geo2": grid_max / 2 - 1,
              }
    textures = {#"generators": os.path.join("energy2.png"),
                #"nodes": os.path.join("energy1.png"),
                "map": os.path.join("map001.png"),
                }
    animation_duration = 20  # seconds
    frame_duration = animation_duration / len(Data.df)
    mini_arrow_length = 2
    mini_arrow_base1 = 1
    mini_arrow_base2 = 1
    mini_arrow_distance = 20
    mini_arrow_speed = 8

    # cursor = vp.cylinder(radius = 1, color=vp.color.white, pos = vp.vector(0,0,0), axis=vp.vector(0,0.2,0),
    # opacity=0.5, pickable=False)
    # --- vpython objects -----
    grid = []
    nodes = {}
    cables = {}  # direct connections, only visible when in arrange mode
    generators = {}
    pointer0 = {}  # to display angle at each generator
    pointer1 = {}  # to display angle at each generator
    discs = {}
    generator_lines = {}
    sub_nodes = {}  # path for cable, only visible when in arrange mode
    sub_cables = {}  # path for cable, only visible when in arrange mode
    labels = {}   # 2d text label
    letters = {}  # 3d billboard letters for nodes and generators
    mini_arrows = {}  # flying along the path, only visible when in simulation mode
    mini_shadows = {}  # shadow for each glider
    mini_losses = {}  # stalagtites below each glider
    # arrows indication flow in cables
    arrows_ij = {}
    arrows_ji = {}
     


class Glider(vp.pyramid):
    number = 1

    def __init__(self, i, j, old_pnr, new_pnr, pos):
        randomcolor = Sim.colors["mini_arrow"]
        colordelta = 0.08
        randomcolor.x += random.uniform(-colordelta, colordelta)
        randomcolor.y += random.uniform(-colordelta, colordelta)
        randomcolor.z += random.uniform(-colordelta, colordelta)
        randomcolor.x = max(0, randomcolor.x)
        randomcolor.y = max(0, randomcolor.y)
        randomcolor.z = max(0, randomcolor.z)
        randomcolor.x = min(1, randomcolor.x)
        randomcolor.y = min(1, randomcolor.y)
        randomcolor.z = min(1, randomcolor.z)
        super().__init__(pos=pos,
                         color=randomcolor,
                         size=vp.vector(Sim.mini_arrow_length, Sim.mini_arrow_base1, Sim.mini_arrow_base2),
                         # axis = vp.norm(new_point-old_point) * Sim.mini_arrow_length,
                         pickable=False,
                         # emissive = True
                         )

        self.i = i
        self.j = j
        curve = Sim.sub_cables[(i, j)]
        self.path = [p["pos"] for p in curve.slice(0, curve.npoints)]
        self.old_pnr = old_pnr
        self.new_pnr = new_pnr
        self.numtar = True
        self.number = Glider.number
        Glider.number += 1
        self.get_bearing()
        Sim.mini_arrows[(i, j)][self.number] = self

    def get_bearing(self):
        if all((self.numtar, self.old_pnr > self.new_pnr)):
            self.old_pnr, self.new_pnr = self.new_pnr, self.old_pnr  # swap
        if all((not self.numtar, self.old_pnr < self.new_pnr)):
            self.old_pnr, self.new_pnr = self.new_pnr, self.old_pnr  # swap
        if all((self.numtar, self.new_pnr >= len(self.path))):
            self.pos = vp.vector(self.path[0].x, self.pos.y, self.path[0].z)
            self.old_pnr = 0
            self.new_pnr = 1
        if all((not self.numtar, self.new_pnr < 0)):
            self.pos = vp.vector(self.path[-1].x, self.pos.y, self.path[-1].z)
            self.old_pnr = len(self.path) - 1
            self.new_pnr = len(self.path) - 2
        newpoint = vp.vector(self.path[self.new_pnr].x, self.pos.y, self.path[self.new_pnr].z)
        self.axis = vp.norm(newpoint - self.pos) * Sim.mini_arrow_length

    def move(self, dt):
        new_pos = self.pos + vp.norm(self.axis) * Sim.mini_arrow_speed * dt
        # test at y 0
        if vp.mag(vp.vector(new_pos.x, 0, new_pos.z) - self.path[self.new_pnr]) < Sim.mini_arrow_length:
            delta = 1 if self.numtar else -1
            self.new_pnr += delta
            self.old_pnr += delta
            self.get_bearing()
        self.pos += vp.norm(self.axis) * Sim.mini_arrow_speed * dt


# ---------- helper functions for Data -----------


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


def func_end(b):
    print("end was pressed", b.text)


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
    for i, curve in Sim.sub_cables.items():
        curve.visible = b.checked


def func_toggle_nodes(b):
    """toggle visibility for nodes (busbars)"""
    for i, cyl in Sim.nodes.items():
        cyl.visible = b.checked


def func_toggle_generators(b):
    """toggle visibility for wind generators """
    for i in Sim.generators:
        Sim.generators[i].visible = b.checked
        #Sim.discs[i].visible = b.checked
        #Sim.pointer0[i].visible = b.checked
        #Sim.pointer1[i].visible = b.checked
        Sim.generator_lines[i].visible = b.checked

def func_toggle_generators_angle(b):
    """toggle visibility for wind generators disc and pointers"""
    for i in Sim.generators:
        #Sim.generators[i].visible = b.checked
        Sim.discs[i].visible = b.checked
        Sim.pointer0[i].visible = b.checked
        Sim.pointer1[i].visible = b.checked
        #Sim.generator_lines[i].visible = b.checked



def func_toggle_gliders(b):
    for (i, j) in Sim.cables:
        if (i,j) in Sim.mini_arrows:
            for n, glider in Sim.mini_arrows[(i, j)].items():
                glider.visible = b.checked


def func_toggle_shadows(b):
    for (i, j) in Sim.cables:
        if (i, j) in Sim.mini_shadows:
            for n, shadow in Sim.mini_shadows[(i, j)].items():
                shadow.visible = b.checked


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

def func_toggle_legend(b):
    """toggle visibility of legend"""
    for l in Sim.gui["legend"]:
        l.visible = b.checked

def func_factor_generators(b):
    # print("the y factor for generators is now:", b.number)
    Sim.factor["generators"] = b.number
    update_stuff()


def func_factor_nodes(b):
    # print("the y factor for nodes is now:", b.number)
    Sim.factor["nodes"] = b.number
    update_stuff()


def func_factor_cables(b):
    # print("the y factor for cables is now:", b.number)
    Sim.factor["arrows"] = b.number
    update_stuff()


def func_factor_cables_x(b):
    # print("the x factor for cables base is now:", b.number)
    Sim.factor["arrows_x"] = b.number
    update_stuff()


def func_factor_cables_z(b):
    # print("the z factor for cables base is now:", b.number)
    Sim.factor["arrows_z"] = b.number
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



def func_simulation(b):
    save_layout()
    Sim.gui["mode"].text = "mode is now: simulation"
    #Sim.gui["save_layout"].disabled = True
    Sim.mode = "simulation"
    #Sim.gui["arrange"].disabled = False
    Sim.gui["simulation"].disabled = True
    Sim.gui["restart"].disabled = False
    Sim.gui["play"].disabled = False
    Sim.gui["frameslider"].disabled = False
    # update gui so that cables can be toggled
    Sim.gui["box_cables"].disabled = False
    # update gui so that gliders are visible and not anymore disabled
    Sim.gui["box_gliders"].disabled = False
    Sim.gui["box_losses"].disabled = False
    Sim.gui["box_shadows"].disabled = False
    Sim.gui["box_gliders"].checked = True
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
    #for arrowlist in Sim.mini_arrows.values():
    #    for o in arrowlist:
    #        o.visible = False
    Sim.mini_arrows = {}
    # ---- delete all shadows ---
    #for shadowlist in Sim.mini_shadows.values():
    #    for o in shadowlist:
    #        o.visible = False
    Sim.mini_shadows = {}
    # ---- delete all mini-losses ----
    #for losslist in Sim.mini_losses.values():
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
            color = vp.color.gray(0.75) if k % 2 == 0 else vp.color.gray(0.25) # TODO: better color cycling
            if k == (len(pointlist)-1):
                continue # already at last point in pointlist
            point2 = pointlist[k+1]
            diff = point2 - point1

            Sim.arrows_ij[(i, j, k)] = vp.arrow(pos=point1, axis=diff, round=True, shaftwidth=1, headwidth=2, color=color, visible=True, pickable=False )
            Sim.arrows_ji[(i,j,k)] = vp.arrow(pos=point2, axis=-diff, round=True, shaftwidth=1, headwidth=2, color=color, visible=False, pickable=False )

    # ----- old: ---
    # ------------ create NEW mini_Arrows, one at each subnode------------
    # create little (moving) gliders for cable, loss, shadow
    for (i, j), curve in Sim.sub_cables.items():
        plist = [p["pos"] for p in curve.slice(0, curve.npoints)]
        #Sim.mini_arrows[(i, j)] = {}
        #Sim.mini_shadows[(i, j)] = {}
        #Sim.mini_losses[(i, j)] = {}
        for number, point in enumerate(plist):
            new_number = number + 1
            if number == len(plist) - 1:
                p2 = plist[-1] + (plist[-1] - plist[-2])
            else:
                p2 = plist[new_number]
            big_diff = vp.mag(p2 - point)
            space_between = Sim.mini_arrow_length + Sim.mini_arrow_distance
            n = 0
            while n * space_between < big_diff:
                startpoint = point + vp.norm(p2 - point) * n * space_between
                #g = Glider(i, j, number, new_number,
                #           startpoint)  # is putting himself into Sim.mini_arrows[(i,j)][g.number]
                #shadow = vp.cylinder(pos=vp.vector(startpoint.x, 0, startpoint.z),
                #                     opacity=0.5,
                #                     color=vp.color.black,
                #                     radius=Sim.mini_arrow_base1,
                #                     axis=vp.vector(0, 0.02, 0),
                #                     pickable=False)
                #Sim.mini_shadows[(i, j)][g.number] = shadow
                #losspin = vp.arrow(pos=startpoint,
                #                   pickable=False,
                #                   axis=vp.vector(0, -0.1, 0),
                #                   color=Sim.colors["losses"],
                #                   size=vp.vector(1, 0.1, 0.1))
                #Sim.mini_losses[(i, j)][g.number] = losspin
                n += 1


def save_layout():  # not a button anymore, therefore no parameter b. function get executed by func_simulation()
    """save pos for each: generator, node, subnode. Save pointlist for each sub_cable"""
    with open("layout_data.txt","w") as myfile:
        myfile.write("#generators\n")
        for i, gen in Sim.generators.items():
            myfile.write(f"{i} {gen.pos.x} {gen.pos.y} {gen.pos.z}\n")
        myfile.write("#nodes\n")
        for i, cyl in Sim.nodes.items():
            myfile.write(f"{i} {cyl.pos.x} {cyl.pos.y} {cyl.pos.z}\n")
        myfile.write("#curves\n")
        for (i,j), curve in Sim.sub_cables.items():
            for k in range(curve.npoints):
                point = curve.point(k)["pos"]
                myfile.write(f"{i} {j} {k} {point.x} {point.y} {point.z}\n")
    print("file layout_data.txt is written")

def load_layout():
    #print("generators:", Sim.generators)
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
        match mode:
            case None:
                continue

            case "curves":
                i, j, k, x, y, z = [float(word) for word in line.split(" ")]
                i, j, k = int(i), int(j), int(k)
                pointpos = vp.vector(x,y,z)
                Sim.sub_cables[(i,j)].modify(k, pointpos)
                if (i,j,k) in Sim.sub_nodes:
                    Sim.sub_nodes[(i,j,k)].pos = pointpos
                if k == int(Sim.number_of_sub_cables / 2):
                    Sim.labels[f"cable {i}-{j}"].pos = pointpos

            case "nodes":
                number, x, y, z = [float(word) for word in line.split(" ")]
                number = int(number)
                npos = vp.vector(x,y,z)
                Sim.nodes[number].pos = npos
                Sim.letters[f"node {number}"].pos = npos + Sim.nodes[number].axis + vp.vector(0,1,0)
                Sim.labels[f"node {number}"].pos = npos
                if number in Sim.generator_lines:
                    Sim.generator_lines[number].modify(0, npos)
                for (i,j), curve in Sim.cables.items():
                    if i == number:
                        curve.modify(0, npos)
                    if j == number:
                        curve.modify(1, npos)

            case "generators":
                number, x, y, z = [float(word) for word in line.split(" ")]
                number = int(number)
                gpos = vp.vector(x,y,z)
                Sim.generators[number].pos = gpos
                Sim.labels[f"generator {number}"].pos = gpos
                Sim.letters[f"generator {number}"].pos = gpos + Sim.generators[number].axis + vp.vector(0, 1, 0)
                Sim.discs[number].pos = gpos
                Sim.pointer0[number].pos = gpos
                Sim.pointer1[number].pos = gpos
                Sim.generator_lines[number].modify(1, pos=gpos) # 1 is the generator, 0 is the node
                #Sim.generator_lines[number].modify(0, pos=Sim.nodes[number].pos)

            case _:
                print("unhandled value for mode in layout file:", mode)
    print("loading of layout data was sucessfull")


def func_color_too_low_nodes(b):
    print(b.number)

def func_color_low_nodes(b):
    print(b.number)

def func_color_nodes(b):
    print(b.number)

def func_color_high_nodes(b):
    print(b.number)

def func_color_too_high_nodes(b):
    print(b.number)

def func_color_too_low_generators(b):
    print(b.number)

def func_color_low_generators(b):
    print(b.number)

def func_color_generators(b):
    print(b.number)

def func_color_high_generators(b):
    print(b.number)

def func_color_too_high_generators(b):
    print(b.number)

def func_color_too_low_generators_angle(b):
    print(b.number)

def func_color_low_generators_angle(b):
    print(b.number)

def func_color_generators_angle(b):
    print(b.number)

def func_color_high_generators_angle(b):
    print(b.number)

def func_color_too_high_generators_angle(b):
    print(b.number)

def func_color_too_low_cables(b):
    print(b.number)

def func_color_low_cables(b):
    print(b.number)

def func_color_cables(b):
    print(b.number)

def func_color_high_cables(b):
    print(b.number)

def func_color_too_high_cables(b):
    print(b.number)

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
    #Sim.scene.append_to_title("mode:")
    #Sim.gui["arrange"] = vp.button(bind=func_arrange, text="arrange", pos=Sim.scene.title_anchor, disabled=True)
    #Sim.gui["save_layout"] = vp.button(bind=func_save_layout, text="save layout", pos=Sim.scene.title_anchor,
    #                                   disabled=False)
    Sim.gui["mode"] = vp.wtext(pos=Sim.scene.title_anchor, text="mode is now: arrange nodes by dragging with mouse")
    Sim.gui["simulation"] = vp.button(bind=func_simulation, text="start simulation", pos=Sim.scene.title_anchor,
                                      disabled=False)
    Sim.gui["restart"] = vp.button(bind=func_restart, text="|<", pos=Sim.scene.title_anchor, disabled=True)
    Sim.gui["play"] = vp.button(bind=func_play, text="play >", pos=Sim.scene.title_anchor, disabled=True)
    # Sim.button_end = vp.button(bind=func_end, text=">|", pos=Sim.scene.title_anchor)

    # Sim.label1 = vp.wtext(pos=Sim.scene.title_anchor, text="---hallo---")
    #Sim.scene.append_to_title("\n")
    Sim.gui[" timeframe"] = vp.wtext(pos=Sim.scene.title_anchor, text="timeframe:  ")
    Sim.gui["frameslider"] = vp.slider(pos=Sim.scene.title_anchor, bind=func_time_slider, min=0, max=len(Data.df),
                                       length=700, step=1, disabled=True)
    Sim.gui["label_frame"] = vp.wtext(pos=Sim.scene.title_anchor, text=" 0")
    Sim.gui["label_last_frame"] = vp.wtext(pos=Sim.scene.title_anchor, text=f" of {len(Data.df)} ")
    Sim.scene.append_to_title("\n")
    # ---- widgets below window in caption area --------------
    Sim.scene.append_to_caption("<code>entinity:    |visible| label | y-factor |"
                                "<span style='background-color:#0000FF'> too low  </span>|"  # blue
                                "<span style='background-color:#00FFFF'> low     </span>|"       # cyan
                                "<span style='background-color:#00FF00'> good     </span>|"      # green
                                "<span style='background-color:#FFFF00'> high    </span>|"      # yellow
                                "<span style='background-color:#FF0000'> too high</span>|"  # red
                                " min / max |</code>\n")
    Sim.scene.append_to_caption("<code>nodes:       |  </code>")
    Sim.gui["box_node"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True, bind=func_toggle_nodes)
    Sim.gui["box_node_labels"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=False, bind=func_toggle_nodes_labels)

    Sim.gui["factor_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_factor_nodes,width=50,
                                        # prompt="nodes:",       # prompt does not work with python yet
                                        type="numeric", text="1.0")
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_low_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_nodes,width=50,
                                        type="numeric", text=f"{Data.nodes_min}") # TODO : get value for nodes
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_low_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_nodes,width=50,
                                               type="numeric", text="-5.0")  # TODO : get  value for nodes
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_nodes,width=50,
                                           type="numeric", text="0.0")  # TODO : get value for nodes
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_high_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_nodes,width=50,
                                       type="numeric", text="5.0")  # TODO : get value for nodes
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_high_nodes"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_nodes,width=50,
                                       type="numeric", text=f"{Data.nodes_max}")  # TODO : get value for nodes
    Sim.scene.append_to_caption("<code>| </code>")
    Sim.gui["min_max_nodes"] = vp.wtext(pos = Sim.scene.caption_anchor, text = "? / ?")
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>generators:  |  </code>")
    Sim.gui["box_generator"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True,
                                  bind=func_toggle_generators)
    Sim.gui["box_generator_labels"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=False,
                                  bind=func_toggle_generator_labels)
    Sim.gui["factor_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_factor_generators,width=50,
                                             # prompt="generators:", # prompt does not work with python yet
                                             type="numeric", text="1.0")
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_low_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_generators,width=50,
                                        type="numeric", text="-10.0") # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_low_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_generators,width=50,
                                               type="numeric", text="-5.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_generators,width=50,
                                           type="numeric", text="0.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_high_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_generators,width=50,
                                       type="numeric", text="5.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_high_generators"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_generators,width=50,
                                       type="numeric", text="10.0")  # TODO : get value
    Sim.scene.append_to_caption("<code>| </code>")
    Sim.gui["min_max_generators"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>    - angle: |  </code>")
    Sim.gui["box_generators_angle"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=True,
                                           bind=func_toggle_generators_angle)
    Sim.scene.append_to_caption("<code>                 | </code>")
    Sim.gui["color_too_low_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_generators_angle,width=50,
                                                    type="numeric", text="-10.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_low_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_generators_angle,width=50,
                                                type="numeric", text="-5.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_generators_angle,width=50,
                                            type="numeric", text="0.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_high_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_generators_angle,width=50,
                                                 type="numeric", text="5.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_high_generators_angle"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_generators_angle,width=50,
                                                     type="numeric", text="10.0")  # TODO : get value
    Sim.scene.append_to_caption("<code>| </code>")
    Sim.gui["min_max_generators_angle"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")

    Sim.scene.append_to_caption("<code>cables:      |  </code>")
    Sim.gui["box_cables"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True, disabled=True,
                                  bind=func_toggle_cables)
    Sim.gui["box_cables_labels"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> | </code>", checked=True, bind=func_toggle_cable_labels)
    Sim.gui["factor_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_factor_cables,width=50,
                                         # prompt="nodes:",       # prompt does not work with python yet
                                         type="numeric", text="0.01")
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_low_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_cables,width=50,
                                                    type="numeric", text="-10.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_low_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_cables,width=50,
                                                type="numeric", text="-5.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_cables,width=50,
                                            type="numeric", text="0.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_high_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_cables,width=50,
                                                 type="numeric", text="5.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_high_cables"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_cables,width=50,
                                                     type="numeric", text="10.0")  # TODO : get value
    Sim.scene.append_to_caption("<code>| </code>")
    Sim.gui["min_max_cables"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>losses:      |  </code>")
    Sim.gui["box_losses"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False,
                                        disabled=True, bind=func_toggle_losses)
    Sim.scene.append_to_caption("<code>     | </code>")  # because no labels for losses (it's in the cable lable)
    Sim.gui["factor_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_factor_losses, width=50,
                                         type="numeric", text="1.0")
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_low_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_low_losses,width=50,
                                                    type="numeric", text="-10.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_low_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_low_losses, width=50,
                                                type="numeric", text="-5.0")  # TODO : get default value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_losses, width=50,
                                            type="numeric", text="0.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_high_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_high_losses, width=50,
                                                 type="numeric", text="5.0")  # TODO : get value
    Sim.scene.append_to_caption("<code> | </code>")
    Sim.gui["color_too_high_losses"] = vp.winput(pos=Sim.scene.caption_anchor, bind=func_color_too_high_losses, width=50,
                                                     type="numeric", text="10.0")  # TODO : get value
    Sim.scene.append_to_caption("<code>| </code>")
    Sim.gui["min_max_losses"] = vp.wtext(pos=Sim.scene.caption_anchor, text="? / ?")
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>  gliders:   |  </code>")
    Sim.gui["box_gliders"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False, disabled=True,
                                  bind=func_toggle_gliders)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>  shadows:   |  </code>")
    Sim.gui["box_shadows"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False, disabled=True,
                                  bind=func_toggle_shadows)
    Sim.scene.append_to_caption("\n")

    Sim.scene.append_to_caption("<code>grid:        |  </code>")
    Sim.gui["box_grid"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True, bind=func_toggle_grid)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>letters:     |  </code>")
    Sim.gui["box_letters"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=True, bind=func_toggle_letters)
    Sim.scene.append_to_caption("\n")
    Sim.scene.append_to_caption("<code>legend:      |  </code>")
    Sim.gui["box_legend"] = vp.checkbox(pos=Sim.scene.caption_anchor, text="<code> |  </code>", checked=False, bind=func_toggle_legend)
    Sim.scene.append_to_caption("\n")
    # legend:
    Sim.gui["legend"] = [
        vp.label(text="nodes (busbars)", pixel_pos=True, pos=vp.vector(10, 790, 0), color=vp.color.blue, align="left",
                 box=False, visible=False),
        vp.label(text="generators", pixel_pos=True, pos=vp.vector(10, 770, 0), color=vp.color.yellow, align="left",
                 box=False, visible=False),
        vp.label(text="cables (connections)", pixel_pos=True, pos=vp.vector(10, 750, 0), color=vp.color.magenta,
                 align="left", box=False, visible=False),
        vp.label(text="losses (connections)", pixel_pos=True, pos=vp.vector(10, 730, 0), color=vp.color.red, align="left",
                 box=False, visible=False)
        ]
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
    match o.what:
        case "node":
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
        case "generator":
            Sim.labels[f"generator {o.number}"].pos = o.pos
            Sim.letters[f"generator {o.number}"].pos.x = o.pos.x
            Sim.letters[f"generator {o.number}"].pos.z = o.pos.z
            # mouve both pointers and disc
            Sim.pointer0[o.number].pos = o.pos
            Sim.pointer1[o.number].pos = o.pos
            Sim.discs[o.number].pos = o.pos
            # update generator_line
            Sim.generator_lines[o.number].modify(1, pos=o.pos)
        case "subnode":
            # change only the attached sub-cables
            i, j, k = o.number
            Sim.sub_cables[i, j].modify(k, pos=o.pos)
            if k == int(Sim.number_of_sub_cables / 2):
                Sim.labels[f"cable {i}-{j}"].pos = o.pos
        case _:
            pass # something else got dragged
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
                                        radius=Sim.radius["nodes"],
                                        axis=vp.vector(0, 2, 0),
                                        pickable=True,
                                        #texture={'file': os.path.join("assets", 'energy1.png'),
                                        #         # 'bumpmap': bumpmaps.stucco,
                                        #         'place': 'right',
                                        #         'flipx': False,
                                        #         'flipy': False,
                                        #         'turn': -1,
                                        #         },
                                        )
        Sim.letters[f"node {number}"] = vp.text(text=f"N{number}", color=vp.color.black,
                                            pos=vp.vector(end_point_1.x, 3, end_point_1.z),
                                            billboard=True, emissive=True, pickable=False, align="center")

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
                                                 radius=Sim.radius["generators"],
                                                 axis=vp.vector(0, 3, 0),
                                                 pickable=True,
                                                 #texture={'file': os.path.join("assets", 'energy2.png'),
                                                 #         # 'bumpmap': bumpmaps.stucco,
                                                 #         'place': 'right',
                                                 #         'flipx': False,
                                                 #         'flipy': False,
                                                 #         'turn': -1,
                                                 #         },
                                                 )
            Sim.generators[number].what = "generator"
            Sim.generators[number].number = number
            Sim.letters[f"generator {number}"] = vp.text(text=f"G{number}", color=vp.color.black,
                                                pos=vp.vector(end_point_3.x, 4, end_point_3.z),
                                                billboard=True, emissive=True, pickable=False, align="center")

            Sim.labels[f"generator {number}"] = vp.label(pos=vp.vector(end_point_4.x, 0, end_point_4.z),
                                                         text=f"g {number}",
                                                         height=10,
                                                         color=vp.color.white,
                                                         visible=False,
                                                         )
            # pointer0 always points like x-axis
            # ------- pointers for angle ------
            start = vp.vector(end_point_3.x, end_point_3.y - 0, end_point_3.z)
            end1 = start + vp.vector(Sim.radius["pointer0"], 0, 0)
            end2 = start + vp.vector(Sim.radius["pointer1"], 0, 0)
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
                                             shape=vp.shapes.circle(radius=Sim.radius["generators"] + 5,
                                                                    angle1=vp.radians(90),
                                                                    # TODO: +5 should be parameter
                                                                    angle2=vp.radians(-90)),
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
                subdisc = vp.cylinder(pos=p, radius=Sim.radius["nodes"] / 3, color=vp.color.magenta,
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
                                                            visible=True,
                                                            )
            pointlist.append(end)
            # -- create sub-cables between sub-discs
            Sim.sub_cables[(i, j)] = vp.curve(color=vp.color.magenta, radius=0.15, pos=pointlist, pickable=False)




def get_Data_min_max():
    # ---- nodes -----
    for number in Sim.nodes:
        s = Data.df[col_name_node(number)]
        mi = s.min()
        ma = s.max()
        #print("min max for node ",number,":", mi, ma)
        if Data.nodes_min is None:
            Data.nodes_min = mi
        elif mi < Data.nodes_min:
            Data.nodes_min = mi
        if Data.nodes_max is None:
            Data.nodes_max = ma
        elif ma > Data.nodes_max:
            Data.nodes_max = ma
    Sim.gui["color_too_low_nodes"].text = f"{Data.nodes_min-1:.2f}"
    Sim.gui["color_too_high_nodes"].text = f"{Data.nodes_max+1:.2f}"
    Sim.gui["color_low_nodes"].text = f"{Data.nodes_min:.2f}"
    Sim.gui["color_high_nodes"].text = f"{Data.nodes_max:.2f}"
    Sim.gui["color_nodes"].text = f"{Data.nodes_min + (Data.nodes_max - Data.nodes_min)/2:.2f}"
    Sim.gui["min_max_nodes"].text = f"<code>{Data.nodes_min:.2f} / {Data.nodes_max:.2f}</code>"
    # generators power
    for number in Sim.generators:
        s = Data.df[col_name_power(number)]
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
    Sim.gui["color_too_low_generators"].text = f"{Data.generators_min-1:.2f}"
    Sim.gui["color_too_high_generators"].text = f"{Data.generators_max+1:.2f}"
    Sim.gui["color_low_generators"].text = f"{Data.generators_min:.2f}"
    Sim.gui["color_high_generators"].text = f"{Data.generators_max:.2f}"
    Sim.gui["color_generators"].text = f"{Data.generators_min + (Data.generators_max - Data.generators_min)/2:.2f}"
    Sim.gui["min_max_generators"].text = f"<code>{Data.generators_min:.2f} / {Data.generators_max:.2f}</code>"
    # generators angle
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
    Sim.gui["color_too_low_generators_angle"].text = f"{Data.generators_angle_min - 1:.2f}"
    Sim.gui["color_too_high_generators_angle"].text = f"{Data.generators_angle_max + 1:.2f}"
    Sim.gui["color_low_generators_angle"].text = f"{Data.generators_angle_min:.2f}"
    Sim.gui["color_high_generators_angle"].text = f"{Data.generators_angle_max:.2f}"
    Sim.gui["color_generators_angle"].text = f"{Data.generators_angle_min + (Data.generators_angle_max - Data.generators_angle_min) / 2:.2f}"
    Sim.gui["min_max_generators_angle"].text = f"<code>{Data.generators_angle_min:.2f} / {Data.generators_angle_max:.2f}</code>"

def update_stuff():
    # -------- nodes --------
    for number, cyl in Sim.nodes.items():
        volt = Data.df[col_name_node(number)][Sim.i]
        cyl.axis = vp.vector(0, volt * Sim.factor["nodes"], 0)
        Sim.labels[f"node {number}"].text = f"n {number}: {volt} V"
        Sim.letters[f"node {number}"].pos.y = cyl.axis.y + 1


    # --------- generators ----------------
    for number, cyl in Sim.generators.items():
        power = Data.df[col_name_power(number)][Sim.i]
        g_angle = Data.df[col_name_angle(number)][Sim.i]
        cyl.axis = vp.vector(0, power * Sim.factor["generators"], 0)
        # ------- pointers for angle --------
        # Sim.pointer0[number].y = cyl.pos.y + cyl.axis.y + 1
        # Sim.pointer1[number].y = cyl.pos.y + cyl.axis.y + 1
        # TODO: compare with angle from previous frame, only move when necessary
        # reset pointer1
        p0 = Sim.pointer0[number]
        p1_axis_vector = vp.vector(Sim.radius["pointer1"], 0, 0)
        p1_axis_vector = vp.rotate(p1_axis_vector, angle=vp.radians(g_angle), axis=vp.vector(0, 1, 0))
        Sim.pointer1[number].axis = vp.vector(p1_axis_vector.x, p1_axis_vector.y, p1_axis_vector.z)
        Sim.labels[f"generator {number}"].text = f"g {number}: {power} MW, {g_angle}°"
        Sim.letters[f"generator {number}"].pos.y = cyl.axis.y + 1
        # print(Sim.i, number, power)

    # ------ cables -----
    #
    for number, targetlist in Data.cables_dict.items():
        for target in targetlist:
            # get power value from dataframe
            power1 = Data.df[col_name_cable(number, target)][Sim.i]
            power2 = Data.df[col_name_cable(target, number)][Sim.i]
            loss = abs(power1 + power2)
            numtar = all((power1 > 0, power2 < 0))  # True if flow from number to target
            power = power1 if numtar else power2
            # print(number, target, "power is:", power1, power2, loss, numtar)
            if f"cable {number}-{target}" in Sim.labels:
                Sim.labels[f"cable {number}-{target}"].text = f"c {number}-->{target}: {power} ({loss}) W {numtar}"
                # ---- new- --
                for k in range(Sim.number_of_sub_cables):
                    # TODO: flexible number of sub_cables?
                    # TODO: cable_factor
                    if numtar:
                        Sim.arrows_ij[(number, target, k)].visible = True
                        Sim.arrows_ji[(number, target, k)].visible = False
                        Sim.arrows_ij[(number, target, k)].shaftwidth = power  * Sim.factor["cables"]
                        Sim.arrows_ij[(number, target, k)].headwidth = power  * Sim.factor["cables"] +1
                    else:
                        Sim.arrows_ij[(number, target, k)].visible = False
                        Sim.arrows_ji[(number, target, k)].visible = True
                        Sim.arrows_ji[(number, target, k)].shaftwidth = power  * Sim.factor["cables"]
                        Sim.arrows_ji[(number, target, k)].headwidth = power  * Sim.factor["cables"] + 1

                # --- old ---
                # let sub_cables stay on the ground
                # Sim.sub_cables[(number,target)].origin.y = power * Sim.factor["cables"]
                # ----- mini-arrows ------
                # print(Sim.mini_arrows[(number, target)])
                # gliderdict = Sim.mini_arrows[(number, target)]:
                # print("arrow:", n, number, target, arrow)
                #for n, glider in Sim.mini_arrows[(number, target)].items():
                #    glider.pos.y = power * Sim.factor["arrows"]
                #    glider.numtar = numtar
                #    Sim.mini_losses[(number, target)][glider.number].pos.y = glider.pos.y
                #    Sim.mini_losses[(number, target)][glider.number].axis = vp.vector(0, -loss * Sim.factor["losses"],
                #                                                                      0)


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

        #text = f"mouse: {Sim.scene.mouse.pos} discs: "
        #Sim.status.text = text
        #Sim.status2.text = f"selected obj: {Sim.selected_object}, drag: {Sim.dragging},"
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
        # --- gliders ----
        for (i, j), gliderdict in Sim.mini_arrows.items():
            for n, glider in gliderdict.items():
                glider.move(Sim.dt)
                shadow = Sim.mini_shadows[(i, j)][n]
                shadow.pos.x = glider.pos.x
                shadow.pos.z = glider.pos.z
                loss = Sim.mini_losses[(i, j)][n]
                loss.pos.x = glider.pos.x
                loss.pos.z = glider.pos.z
                # loss.pos.y = glider.pos.y


if __name__ == "__main__":
    create_data()
    create_stuff()
    load_layout()
    create_widgets()
    get_Data_min_max()
    main()
