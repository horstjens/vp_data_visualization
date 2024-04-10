import vpython as vp




class Sim:
    running = False
    mapsize = 10
    scene = vp.canvas(title=f'arrow demo',
                      # caption="coordinates: ",
                      width=1200, height=800,
                      #center=vp.vector(middle[0], 0, middle[1]),
                      background=vp.color.gray(0.3),
                      #align="left",  # caption is to the right?
                      )

    fps = 60
    dt = 1 / fps
    #nodes = {}
    letters = {}
    cables = {}
    arrowspeed = 0.08
    blackarrows = {}



class Shadowarrow(vp.arrow):

    def __init__(self, nodestring, flow, **kwargs):
        super().__init__(**kwargs)
        if nodestring not in Sim.blackarrows:
            Sim.blackarrows[nodestring] = []
        Sim.blackarrows[nodestring].append(self)
        self.nodestring = nodestring
        self.flow = flow
        self.color = vp.color.black
        self.shaftwidth = 0.03
        cables = Sim.cables[self.nodestring] # list of boxes !
        self.distances_ab = []
        total_distance = 0
        for n, box in enumerate(cables):
            distance = box.pos - cables[0].pos
            self.distances_ab.append(distance)


        # get pos from nodestring and flow
        if flow:
            index = 0     # fly from A to B
            self.next_node = 1
            self.old_node = 0
            self.axis = vp.norm(cables[1].pos-cables[0].pos)
        else:
            index = -1    # fly from B to A
            self.next_node = -2
            self.old_node = -1
            self.axis = vp.norm(cables[-2].pos-cables[-1].pos)
        self.axis = vp.norm(self.axis) * 0.5
        self.pos = cables[index].pos - self.axis

    def update(self):
        self.pos += Sim.arrowspeed * Sim.dt * vp.norm(self.axis)
        if self.flow:
            pass










def create_stuff():
    # axis arrows with letters
    vp.arrow( axis=vp.vector(1, 0, 0), color=vp.color.red, pickable=False)
    vp.arrow( axis=vp.vector(0, 1, 0), color=vp.color.green, pickable=False)
    vp.arrow( axis=vp.vector(0, 0, 1), color=vp.color.blue, pickable=False)
    # ground floor (with map)
    vp.box(pos=vp.vector(Sim.mapsize/2 , -0.05, Sim.mapsize / 2),
        #pos=Sim.center + vp.vector(0, -0.01, 0),
        size=vp.vector(Sim.mapsize, 0.015, Sim.mapsize),
        )
    # ------- nodes -------------
    # create cable AB
    Sim.cables["AB"] = []
    for n in range(10):
        x = Sim.mapsize/10 * n + 0.5
        z = vp.random()  * (Sim.mapsize -1) + 0.5
        Sim.cables["AB"].append(vp.box(pos=vp.vector(x, 0.0, z),
                                       size=vp.vector(0.2, 0.2, 0.2),
                                       color=vp.color.cyan,
                                       opacity=0.5))
        Sim.letters[n] = vp.label(pos=vp.vector(x, 0.25, z),
                                  text="A" if n == 0 else "B" if n == 9 else f"{n}",
                                  color=vp.color.black,
                                  box=False,
                                  opacity=0)
    # create 2 black arrows
    Shadowarrow("AB", True)
    Shadowarrow("AB", False)


def main():
    simtime = 0
    time_since_framechange = 0
    # frame_number = 0  # Sim.i
    Sim.running = True
    while True:
        vp.rate(Sim.fps)
        simtime += Sim.dt
        time_since_framechange += Sim.dt
        # print("simtime", simtime)
        if Sim.running:
            for nodestring, arrowlist in Sim.blackarrows.items():
                for blackarrow in arrowlist:
                    blackarrow.update()



if __name__ == "__main__":
    create_stuff()
    main()