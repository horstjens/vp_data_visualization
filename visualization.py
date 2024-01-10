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
class Data:
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
    Data.cables_dict = {}
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
    print(Data.cables_dict)
    print("duplicate colnames:")
    print(duplicate_colnames)
    # --------------------- location of nodes and generators -------------
    # idea: arrange all nodes in a big circle
    # arrange the generators in an even bigger circle with the sam origin



# helper functions for vpython widgets

def button_start_func(b):
    print("start was pressed", b.text)

def button_end_func(b):
    print("end was pressed", b.text)

def button_play_func(b):
    print("play button was pressed", b.text)
    if "play" in b.text.lower():
        Sim.animation_running = True
        Sim.button_play.text = "Pause ||"
    else:
        Sim.animation_running = False
        Sim.button_play.text = "Play >"


def slider1_func(b):
    """jump to a specific frame in the dataset """
    print("slider is set to ", b.value)
    # Sim.connAB.pos.y = power_ab[b.value]
    Sim.label3.text = str(b.value)
    Sim.i = b.value
    update_stuff()


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

def check5_func(b):
    """toggles grid lines"""
    for line in Sim.gridlines:
        line.visible = b.checked

def input1_func(b):
    print("the y factor for generators is now:", b.number)
    Sim.factor_generators = b.number
    update_stuff()

def input2_func(b):
    print("the y factor for nodes is now:", b.number)
    Sim.factor_nodes= b.number
    update_stuff()

def input3_func(b):
    print("the y factor for cables is now:", b.number)
    Sim.factor_cables = b.number
    update_stuff()

class Sim:
    """all important vpython constants are in this class, to make referencing from outside more easy"""
    GRID_MAX = 250
    GRID_STEP = 25
    NODE_RADIUS = 4  # how big a node is
    GENERATOR_RADIUS = 8
    POINTER0_RADIUS = GENERATOR_RADIUS + 10
    POINTER1_RADIUS = GENERATOR_RADIUS + 15
    geo_radius1 = 200
    geo_radius2 = 225
    animation_duration = 20 # seconds
    frame_duration = animation_duration / len(Data.df)
    animation_running = False
    scene = vp.canvas(title='Bruce training data',
                      caption="show: ",
                      width=1200, height=800,
                      center=vp.vector(0, 0, 0),
                      background=vp.color.black,
                      )

    fps = 60
    dt = 1 / fps
    i = 0  # frame number, row in dataframe
    mini_arrow_length = 9
    mini_arrow_base1 = 3
    mini_arrow_base2 = 3
    mini_arrow_distance = 2
    mini_arrow_speed = 13
    scene.append_to_title("\n")
    gridlines = []
    labels = {}
    nodes = {}
    generators = {}
    pointer0 = {}  # to display angle at each generator
    pointer1 = {}  # to display angle at each generator
    cables = {} # base arrow from origin to target, will be invisible  # TODO delete?
    mini_arrows = {} # list of moving arrows
    factor_generators = 1.0
    factor_nodes = 1.0
    factor_cables = 0.01

def create_widgets():
    # ---- widgets above window in title area -------
    Sim.button_start = vp.button(bind=button_start_func, text="|<", pos=Sim.scene.title_anchor)
    Sim.button_play = vp.button(bind=button_play_func, text="play >", pos=Sim.scene.title_anchor)
    Sim.button_end = vp.button(bind=button_end_func, text=">|", pos=Sim.scene.title_anchor)

    Sim.label1 = vp.wtext(pos=Sim.scene.title_anchor, text="---hallo---")
    Sim.scene.append_to_title("\n")
    Sim.label2 = vp.wtext(pos=Sim.scene.title_anchor, text="timeframe:  ")
    Sim.slider1 = vp.slider(pos=Sim.scene.title_anchor, bind=slider1_func, min=0, max=len(Data.df),
                        length=700, step=1)
    Sim.label3 = vp.wtext(pos=Sim.scene.title_anchor, text=" 0")
    Sim.label4 = vp.wtext(pos=Sim.scene.title_anchor, text=f" of {len(Data.df)} ")
    Sim.scene.append_to_title("\n")
    # ---- widgets below window in caption area
    Sim.box1 = vp.checkbox(pos=Sim.scene.caption_anchor, text="node labels ", checked=False, bind=check1_func)
    Sim.box2 = vp.checkbox(pos=Sim.scene.caption_anchor, text="generator labels ", checked=False, bind=check2_func)
    Sim.box3 = vp.checkbox(pos=Sim.scene.caption_anchor, text="cable labels ", checked=False, bind=check3_func)
    #Sim.box4 = vp.checkbox(pos=Sim.scene.caption_anchor, text="base cables ", checked=False, bind=check4_func)
    Sim.box5 = vp.checkbox(pos=Sim.scene.caption_anchor, text="grid ", checked=True, bind=check5_func)
    Sim.scene.append_to_caption("\n")
    vp.wtext(pos=Sim.scene.caption_anchor, text="y factor (confirm with ENTER) for: generators:")
    Sim.input1 = vp.winput(pos=Sim.scene.caption_anchor, bind=input1_func,
                           #prompt="generators:", # prompt does not work with python yet
                           type="numeric", text="1.0")
    vp.wtext(pos=Sim.scene.caption_anchor, text=" nodes:")
    Sim.input2 = vp.winput(pos=Sim.scene.caption_anchor, bind=input2_func,
                           #prompt="nodes:",       # prompt does not work with python yet
                           type="numeric", text="1.0")
    vp.wtext(pos=Sim.scene.caption_anchor, text=" cables:")
    Sim.input2 = vp.winput(pos=Sim.scene.caption_anchor, bind=input3_func,
                           # prompt="nodes:",       # prompt does not work with python yet
                           type="numeric", text="0.01")


def create_stuff():
    # make 3 arrows from origin
    Sim.xarrow = vp.arrow(axis=vp.vector(10, 0, 0), color=vp.color.red)
    Sim.yarrow = vp.arrow(axis=vp.vector(0, 10, 0), color=vp.color.green)
    Sim.zarrow = vp.arrow(axis=vp.vector(0, 0, 10), color=vp.color.blue)
    # make a grid
    for i in range(-Sim.GRID_MAX, Sim.GRID_MAX + 1, Sim.GRID_STEP):
        Sim.gridlines.append(vp.curve(vp.vector(i, 0, -Sim.GRID_MAX), vp.vector(i, 0, Sim.GRID_MAX), radius=0.1, color=vp.color.cyan))
        Sim.gridlines.append(vp.curve(vp.vector(-Sim.GRID_MAX, 0, i), vp.vector(Sim.GRID_MAX, 0, i), radius=0.1, color=vp.color.cyan))

    # create an inner circle with all nodes (blue cylinder)
    pointer = vp.vector(Sim.geo_radius1, 0, 0)
    for i, number in enumerate(Data.node_numbers):
        end_point_1 = vp.vector(0, 0, 0) + pointer  # origin of cylinder for node
        end_point_2 = vp.vector(0, 0, 0) + pointer.norm() * (Sim.geo_radius1 + 5)  # origin of label for node
        Sim.nodes[number] = vp.cylinder(pos=vp.vector(end_point_1.x, 0, end_point_1.z),
                                        color=vp.color.blue,
                                        radius=Sim.NODE_RADIUS,
                                        axis=vp.vector(0, 24, 0),
                                        )

        Sim.labels[f"node {number}"] = vp.label(pos=end_point_2, text=f"n {number}", height=10, color=vp.color.white,
                                                visible=False)
        # add generators in outer circle (if number is matching)
        if number in Data.generator_numbers:
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
                                                         visible=False
                                                         )
            # pointer0 always points like x-axis
            # ------- pointers for angle ------
            start = vp.vector(end_point_3.x, end_point_3.y - 2, end_point_3.z)
            end1 = start + vp.vector(Sim.POINTER0_RADIUS, 0,0)
            end2 = start + vp.vector(Sim.POINTER1_RADIUS, 0, 0)
            Sim.pointer0[number] = vp.arrow(pos=start,
                                            axis=end1-start,
                                            color=vp.color.red,
                                            shaftwidth = 1.0,
                                            #headwidth= 3
                                            )
            Sim.pointer1[number] = vp.arrow(pos=start,
                                            axis=end2-start,
                                            color=vp.color.orange,
                                            round=True,
                                            shaftwidth=0.5,
                                            #headwidth = 0.5
                                            )
            # ---- disc ----
            vp.extrusion(path=[start, vp.vector(start.x, start.y+0.1, start.z)],
                         shape=vp.shapes.circle(radius=Sim.GENERATOR_RADIUS+5,angle1=vp.radians(90), angle2=vp.radians(-90)))
            # make automatic connection from generator to node
            vp.curve(vp.vector(end_point_1.x, 2, end_point_1.z),
                     vp.vector(end_point_3.x, 2, end_point_3.z),
                     radius=2,
                     color=vp.color.orange)

        # prepare clock-pointer for next number
        pointer = vp.rotate(pointer,
                            angle=vp.radians(360 / len(Data.node_numbers)),
                            axis=vp.vector(0, 1, 0),
                            )

    # print("yes")

    # create ALL cables
    for o_number, t_numbers in Data.cables_dict.items():
        # get the value
        ov = vp.vector(Sim.nodes[o_number].pos.x,Sim.nodes[o_number].pos.y,Sim.nodes[o_number].pos.z)
        for t in t_numbers:
            tv = vp.vector(Sim.nodes[t].pos.x, Sim.nodes[t].pos.y, Sim.nodes[t].pos.z)
            # base cable (invisible at start)
            #Sim.cables[(o_number, t)] = vp.arrow(pos=ov, axis=tv-ov, color=vp.color.green, shaftwidth=1, visible=False)
            # base cable lable
            Sim.labels[f"cable {o_number} {t}"] = vp.label(pos=ov + vp.norm(tv-ov) * vp.mag(tv-ov)/2,
                                                           text=f"c {o_number} {t}",
                                                           height=10,
                                                           color=vp.color.white,
                                                           visible=False)
            # little (moving) arrows
            Sim.mini_arrows[(o_number, t)] = []  # empty list
            start = vp.vector(ov.x, ov.y, ov.z)
            end = start + vp.norm(tv-ov) * Sim.mini_arrow_length
            #Sim.mini_arrows[(o_number,t)].append(vp.arrow(pos=vp.vector(start.x, start.y, start.z),
            #                                              axis=end-start,
            #                                              color = vp.color.magenta))
            #Sim.mini_arrows[(o_number, t)].append(vp.pyramid(pos=vp.vector(start.x, start.y, start.z),
            #                                                 axis = end-start,
            #                                                 color= vp.color.magenta,
            #                                                 length=Sim.mini_arrow_base1,
            #                                                 width=Sim.mini_arrow_base2,
            #                                                 ))
            mini_counter = 1
            end += vp.norm(tv - ov) *   Sim.mini_arrow_distance
            while (vp.mag(end-ov) + Sim.mini_arrow_length) < vp.mag(tv-ov):
                start = vp.vector(end.x, end.y, end.z)
                end += vp.norm(tv-ov) * Sim.mini_arrow_length
                mini_counter += 1
                #Sim.mini_arrows[(o_number, t)].append(vp.arrow(pos=vp.vector(start.x, start.y, start.z),
                #                                               axis=end - start,
                #                                               color=vp.color.purple if mini_counter % 2 == 0 else vp.color.magenta,
                #                                               shaft_width = 5,
                #                                               ))
                Sim.mini_arrows[(o_number, t)].append(vp.pyramid(pos=vp.vector(start.x, start.y, start.z),
                                                                 axis=end - start,
                                                                 color=vp.color.purple if mini_counter % 2 == 0 else vp.color.magenta,
                                                                 length=Sim.mini_arrow_base1,
                                                                 width=Sim.mini_arrow_base2,
                                                                 ))
                end += vp.norm(tv - ov) *  Sim.mini_arrow_distance
    # done with creating stuff - make ONE update for correcting y values

    update_stuff()


def update_stuff():
    # --------- generators ----------------
    for number, cyl in Sim.generators.items():
        power = Data.df[col_name_power(number)][Sim.i]
        g_angle = Data.df[col_name_angle(number)][Sim.i]
        cyl.axis = vp.vector(0, power * Sim.factor_generators, 0)
        # ------- pointers for angle --------
        #Sim.pointer0[number].y = cyl.pos.y + cyl.axis.y + 1
        #Sim.pointer1[number].y = cyl.pos.y + cyl.axis.y + 1
        # TODO: compare with angle from previous frame, only move when necessary
        # reset pointer1
        p0 = Sim.pointer0[number]
        p1_axis_vector = vp.vector(Sim.POINTER1_RADIUS, 0, 0)
        p1_axis_vector = vp.rotate(p1_axis_vector, angle=vp.radians(g_angle), axis=vp.vector(0,1,0))
        Sim.pointer1[number].axis = vp.vector(p1_axis_vector.x, p1_axis_vector.y, p1_axis_vector.z)
        Sim.labels[f"generator {number}"].text = f"g {number}: {power} MW, {g_angle}°"
        #print(Sim.i, number, power)
    # -------- nodes --------
    for number, cyl in Sim.nodes.items():
        volt = Data.df[col_name_node(number)][Sim.i]
        cyl.axis = vp.vector(0, volt * Sim.factor_nodes, 0)
        Sim.labels[f"node {number}"].text = f"n {number}: {volt} V"
    # ------ cables -----

    # make negative cables invisible
    for number, targetlist in Data.cables_dict.items():
        for target in targetlist:
            # get power value from dataframe
            power = Data.df[col_name_cable(number, target)][Sim.i]
            #print("power is:", power)
            Sim.labels[f"cable {number} {target}"].text = f"c {number}-->{target}: {power} W"
            if power < 0:
                # make invisible
                v = False
            else:
                v = True
            ##for (o, t), arrow_list in Sim.mini_arrows.items():
            ##   for a in arrow_list:
            for glider in Sim.mini_arrows[(number, target)]:
                #print("arrowlist:",arrowlist)
                #print("miniarrows:", Sim.mini_arrows[(number, target)])
                glider.visible = v
                glider.pos.y = power * Sim.factor_cables


def mainloop():
    simtime = 0
    time_since_framechange = 0
    #frame_number = 0  # Sim.i
    while True:
        vp.rate(Sim.fps)
        simtime += Sim.dt
        time_since_framechange += Sim.dt
        # play animation
        if Sim.animation_running:
            if time_since_framechange > Sim.frame_duration:
                time_since_framechange = 0
                Sim.i += 1
                if Sim.i >= len(Data.df):
                    Sim.i = 0
                # update widgets
                Sim.label3.text = f"{Sim.i}"
                Sim.slider1.value = Sim.i
                # get the data from df (for y values)
                update_stuff()

        # move the little gliders
        if Sim.animation_running:
            for (o, t), arrow_list in Sim.mini_arrows.items():
                for a in arrow_list:
                    start_pos = Sim.nodes[o].pos
                    end_pos = Sim.nodes[t].pos
                    move = vp.norm(end_pos-start_pos) * Sim.mini_arrow_speed * Sim.dt
                    a.pos += move
                    # check distance by ignoring y
                    exz = vp.vector(end_pos.x, 0, end_pos.z)
                    axz = vp.vector(a.pos.x, 0, a.pos.z)
                    if vp.mag(exz - axz) < Sim.mini_arrow_length:
                        a.pos = vp.vector(start_pos.x, start_pos.y, start_pos.z)


if __name__ == "__main__":
    create_data()
    create_widgets()
    create_stuff()
    mainloop()
