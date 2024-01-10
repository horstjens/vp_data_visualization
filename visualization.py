import os.path
import pandas as pd
import random
import vpython as vp

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
       
# TODOS
+let user drag nodes
+sub-divide cables into a (fixed?) number of sub-cables between sub-nodes and let user drag those sub-nodes
+color scale every "value" on a scale between green (normal) to red (upper limit) or blue (lower-limit)
+use different extruded shapes (Star etc.) instead of cylinders 

"""

class Data:
    """Data contains variables taken from the excel/csv file"""
    # create a pandas dataframe from csv
    df = pd.read_csv("raw_data.csv")
    # take some interesting columns (called 'series' in pandas)

    time_col_name = "Time(s)"
    generator_numbers = [i for i in range(30, 40)]  # numbers from 30 to 39

    # col_name for generator 30 angle: "ANGL 30[30 1.0000]1"
    # col_name for generator 30 power: "POWR 30[30 1.0000]1"
    ## angle 39 is the reference angle (0)

    node_numbers = [i for i in range(1, 40)]  # numbers from 1 to 39
    cable_col_names = [raw_name for raw_name in df if raw_name.startswith("POWR ") and (" TO " in raw_name)]
    cables_dict = {}  # {from_number: [to_number, to_number, to_number], ...}


class Sim:
    selected_object = None
    animation_running = False
    dragging = False
    scene = vp.canvas(title='bruce mouse dragging simulator demo',
                      # caption="coordinates: ",
                      width=1200, height=800,
                      center=vp.vector(0, 0, 0),
                      background=vp.color.gray(0.8),
                      )
    grid_max = 200
    grid_step = 10
    number_of_sub_cables = 6 # sub-nodes = sub_cables -1
    fps = 60
    dt = 1 / fps
    i = 1 # line in data sheet

    status = vp.label(text="nothing", pos=vp.vector(10, 10, 0), color=vp.color.green, pixel_pos=True, align="left")
    status2 = vp.label(text="nada", pos=vp.vector(10, 50, 0), color=vp.color.green, pixel_pos=True, align="left")
    #colors = (vp.color.red, vp.color.green, vp.color.blue, vp.color.yellow)
    colors = {"nodes": vp.color.blue,
              "generators": vp.color.yellow,
              "cables": vp.color.gray(0.5),
              "flyers1": vp.color.magenta,
              "flyers2": vp.color.purple,
              "disc": vp.color.gray(0.75),
              "grid": vp.color.black,
              "ground": vp.color.green,
              "pointer0": vp.color.orange,
              "pointer1": vp.color.red,
              "generator_lines": vp.color.gray(0.25),
              }
    factor = {"generators": 1.0,
              "nodes": 1.0,
              "cables": 0.01,
              "cables_x": 0.01,
              "cables_y": 0.01,
              "losses": 10.0,
              }
    visible = {"generators": True,
               "nodes": True,
               "cables": True,
               "flyers": False,
               }
    radius = {"generators": 5,
              "nodes": 4,
              "pointer0": 8 +0, # for wind angle
              "pointer1": 8 +0, # for wind angle
              "geo1": grid_max /2 - 25,
              "geo2": grid_max /2 - 1,
               }
    textures = {"generators": "energy2.png",
                "nodes": "energy1.png",
                #"map": "map001.png",
                }

    animation_duration = 20  # seconds
    frame_duration = animation_duration / len(Data.df)


    # cursor = vp.cylinder(radius = 1, color=vp.color.white, pos = vp.vector(0,0,0), axis=vp.vector(0,0.2,0),
    # opacity=0.5, pickable=False)
    # --- vpython objects -----
    nodes = {}
    cables = {} # direct connections, only visible when dragging nodes by mouse
    generators = {}
    pointer0 = {}  # to display angle at each generator
    pointer1 = {}  # to display angle at each generator
    discs = {}
    generator_lines= {}
    sub_nodes = {}
    sub_cables = {}
    labels = {}

    # line_parts =

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
    ##cables1 = set()
    #Data.cables_dict = {}
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
        ##if (c_to, c_from) not in cables1:
        ##    cables1.add((c_from, c_to))

    # print(cables1)  # a set of 48 connections ( 96 for both directions, including the losses )
    print("duplicate colnames:",duplicate_colnames)

    print("Data.generator_numbers", Data.generator_numbers)
    print("Data.node_numbers", Data.node_numbers)
    print("Data.cables.dict:", Data.cables_dict)

    # --------------------- location of nodes and generators -------------
    # idea: arrange all nodes in a big circle
    # arrange the generators in an even bigger circle with the sam origin


# ------------ helper function for GUI ------------
def mousebutton_down():
    Sim.selected_object = Sim.scene.mouse.pick
    if Sim.selected_object is None:
        Sim.dragging = False
    else:
        Sim.dragging = True


def mousebutton_up():
    Sim.dragging = False
    Sim.selected_object = None


def mouse_move():
    if Sim.dragging:
        o = Sim.selected_object
        o.pos = vp.vector(Sim.scene.mouse.pos.x, 0, Sim.scene.mouse.pos.z)

        if o.what == "node":
            Sim.labels[f"node {o.number}"].pos = o.pos
            # re-arrange all cables that are connected to this node
            i = o.number
            for (a,b), cable in Sim.cables.items():
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
                    Sim.sub_nodes[(i2,j2,k)].pos = p
                    pointlist.append(p)
                    # TODO: sub-optimal code, iterates more often then necessary over all subdiscs
                pointlist.append(end)
                for number, point in enumerate(pointlist):
                    Sim.sub_cables[(i2,j2)].modify(number, pos=point)
            # exist connected generator?
            if o.number in Sim.generator_lines.keys():
                Sim.generator_lines[o.number].modify(0, pos=o.pos)
        elif o.what == "generator":
            Sim.labels[f"generator {o.number}"].pos = o.pos
            # mouve both pointers and disc
            Sim.pointer0[o.number].pos = o.pos
            Sim.pointer1[o.number].pos = o.pos
            Sim.discs[o.number].pos = o.pos
            # update generator_line
            Sim.generator_lines[o.number].modify(1, pos=o.pos)


        elif o.what == "subnode":
            # change only the attached sub-cables
            i,j,k = o.number
            Sim.sub_cables[i,j].modify(k, pos=o.pos)


        #elif o.what == "subdisc":
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
    # ground floor
    Sim.scene.visible = False
    vp.box(#pos=vp.vector(Sim.grid_max / 2, -0.05, Sim.grid_max / 2),
           pos=vp.vector(0, -0.1, 0),
           size=vp.vector(Sim.grid_max, 0.15, Sim.grid_max),
           #color=vp.color.cyan,
           #opacity=0.5,
            texture={'file': os.path.join("assets",'map001.png'),
                 # 'bumpmap':bumpmaps.stucco,
                 # 'place':'left',
                 # 'flipx':True,
                 # 'flipy':True,
                  'turn':3,
                 },
           pickable=False)

    Sim.scene.waitfor("textures")
    Sim.scene.visible = True
    # make grid
    for x in range(-Sim.grid_max//2, Sim.grid_max//2, Sim.grid_step):
        vp.curve(pos=[vp.vector(x, 0, -Sim.grid_max//2), vp.vector(x, 0, Sim.grid_max//2)], color=vp.color.black, radius=0.01, pickable=False)
    for z in range(-Sim.grid_max//2, Sim.grid_max//2, Sim.grid_step):
        vp.curve(pos=[vp.vector(-Sim.grid_max//2, 0, z), vp.vector(Sim.grid_max//2, 0, z)], color=vp.color.black, radius=0.01, pickable=False)
    # create 4 nodes (disc)
    # for i in range(4):
    #     p = vp.vector(random.uniform(0, Sim.grid_max), 0, random.uniform(0, Sim.grid_max))
    #     if i == -1:  # impossible value, do NOT make a star
    #         # make a star TODO: extrusion makes the texture ugly if texture is a loaded image
    #         starshape = vp.shapes.star(n=5, radius=0.75, iradius=0.5)
    #         pa = [vp.vector(0,0,0), vp.vector(0,0.25,0)]
    #         d = vp.extrusion(pos=p+vp.vector(0,0.25,0), path=pa, shape=starshape,
    #                          #color=Sim.colors[i],
    #                          texture=vp.textures.stucco,
    #                          #texture={"file": os.path.join("assets", "energy1.png"),
    #                          #         "place": "left" ,
    #                          #         "flipy": False,
    #                          #         "flipx": False,
    #                          #         },
    #                          )
    #
    #     else:
    #         # make a cylinder
    #         d = vp.cylinder(pos=p,
    #                 axis=vp.vector(0, 0.25, 0),
    #                 radius=0.75,
    #                 color=Sim.colors["nodes"],
    #                 texture={"file":os.path.join("assets","energy1.png"),
    #                          "place":"right",
    #                          "flipy":True,
    #                          "flipx":True,
    #                          },
    #                 pickable=True)
    #     d.number = i  # simple integer for node number
    #     d.what = "node"
    #     #letter = vp.text(pos = p + vp.vector(0,0.25,0),
    #     #                 text=f"{i}",
    #     #                 color=vp.color.magenta,
    #     #                 up=vp.vector(0,0,-0.1))
    #     #disc = vp.compound((d, letter))
    #
    #     Sim.nodes[i] = d

    # ====
    # create an inner circle with all nodes (busbars, blue cylinder)
    pointer = vp.vector(Sim.radius["geo1"], 0, 0)
    for i, number in enumerate(Data.node_numbers):
        # CREATE NODE
        end_point_1 = vp.vector(0, 0, 0) + pointer  # origin of cylinder for node
        end_point_2 = vp.vector(0, 0, 0) + pointer.norm() * (Sim.radius["geo1"] + 5)  # origin of label for node # TODO: 5 should be parameter
        Sim.nodes[number] = vp.cylinder(pos=vp.vector(end_point_1.x, 0, end_point_1.z),
                                        color=Sim.colors["nodes"],
                                        radius=Sim.radius["nodes"],
                                        axis=vp.vector(0, 2, 0),
                                        pickable = True,
                                        )
        Sim.nodes[number].what = "node"
        Sim.nodes[number].number = number
        Sim.labels[f"node {number}"] = vp.label(pos=end_point_2, text=f"n {number}", height=10,
                                                color=vp.color.white,
                                                visible=True)
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
                                                 pickable = True,
                                                 )
            Sim.generators[number].what = "generator"
            Sim.generators[number].number = number
            Sim.labels[f"generator {number}"] = vp.label(pos=vp.vector(end_point_4.x, 0, end_point_4.z),
                                                         text=f"g {number}",
                                                         height=10,
                                                         color=vp.color.white,
                                                         visible=True,
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
                         shape=vp.shapes.circle(radius=Sim.radius["generators"] + 5, angle1=vp.radians(90), # TODO: +5 should be parameter
                                                angle2=vp.radians(-90)),
                         pickable=False)
            # make automatic connection from generator to node
            Sim.generator_lines[number] = vp.curve(vp.vector(end_point_1.x, 0.1, end_point_1.z),
                                                   vp.vector(end_point_3.x, 0.1, end_point_3.z),
                     radius=0.1,
                     color=vp.color.orange,
                     pickable = False)

        # prepare clock-pointer for next number
        pointer = vp.rotate(pointer,
                            angle=vp.radians(360 / len(Data.node_numbers)),
                            axis=vp.vector(0, 1, 0),
                            )
    # ====================================== end of original code from scrip009 ==================
    # create 2 cables for each node, last one connects to the first one
    keys = list(Sim.nodes.keys())
    #for i, node in Sim.nodes.items():
    #    j = i + 1
    #    if j == len(keys):
    #        j = 0
    for i, to_number_list in Data.cables_dict.items():
        for j in to_number_list:
            from_node = Sim.nodes[i]
            to_node = Sim.nodes[j]
            if (j,i) in Sim.cables.keys():
                continue # create only one direction
            Sim.cables[(i,j)] = vp.curve(radius=0.1, color=vp.color.orange, pos=[from_node.pos, to_node.pos], pickable=False)
            Sim.cables[(i,j)].number = (i,j) # tuple of both node numbers
            Sim.cables[(i,j)].what = "cable"
            # divide each  cable (0,1) into 4 subcables by creating 5 subnodes (first and last subnodes are the cable nodes)
            start = from_node.pos
            end = to_node.pos
            diff = end-start
            #Sim.sub_discs[(i, j)] = []
            # create sub-discs
            #p = vp.vector(start.x, start.y, start.z)
            pointlist = [] # for sub-cables
            pointlist.append(start)
            for k in range(1,Sim.number_of_sub_cables): #  6 subnodes
                p = start + k * vp.norm(diff) * vp.mag(diff) / (Sim.number_of_sub_cables)  # divide by
                subdisc = vp.cylinder(pos=p, radius=Sim.radius["nodes"]/3, color=vp.color.magenta, axis=vp.vector(0,3,0),
                                                        pickable=True)
                subdisc.number = (i,j,k)
                subdisc.what = "subnode"
                Sim.sub_nodes[(i,j,k)] = subdisc
                pointlist.append(subdisc.pos)
            pointlist.append(end)
            # -- create sub-cables between sub-discs
            Sim.sub_cables[(i,j)] = vp.curve(color=vp.color.magenta, radius=0.15, pos=pointlist, pickable=False )



def main():
    # Sim.scene.bind("click", mouseclick )
    Sim.scene.bind("mousedown", mousebutton_down)
    Sim.scene.bind("mousemove", mouse_move)
    Sim.scene.bind("mouseup", mousebutton_up)
    create_stuff()
    ##ballon = vp.sphere(pos=vp.vector(Sim.size/2, 14, Sim.size/2), color=vp.color.red, pickable=False, radius=0.25)

    # Sim.scene.center = vp.vector(Sim.size/2, 0, Sim.size/2)
    # TODO fix camera (REihenfolge von pos, forward, range. verzerrung bei mousedrag -> bessere pick funktion machen?
    Sim.scene.camera.pos = vp.vector(0, 2, 0)
    Sim.scene.forward = vp.vector(0.01, -1, 0)  # FIXME: if forward vector is set to vp.vector(0,-1,0)
                                                # then all becomes black
    Sim.scene.range = Sim.grid_max / 2

    Sim.scene.autoscale = True
    Sim.scene.autoscale = False

    # Sim.scene.userzoom = False
    Sim.scene.userspin = False
    # Sim.scene.userpan = False
    #print(f"objects: {Sim.scene.objects}\n lights: {Sim.scene.lights}")
    simtime = 0
    time_since_framechange = 0
    # frame_number = 0  # Sim.i
    while True:
        vp.rate(Sim.fps)
        simtime += Sim.dt
        time_since_framechange += Sim.dt

        text = f"mouse: {Sim.scene.mouse.pos} discs: "
        Sim.status.text = text
        Sim.status2.text = f"selected obj: {Sim.selected_object}, drag: {Sim.dragging},"
        # play animation
        if not Sim.animation_running:
            continue



if __name__ == "__main__":
    create_data()
    main()
