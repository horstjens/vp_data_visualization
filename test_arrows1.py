import vpython as vp


class Sim:
    running = False
    mapsize = 10
    scene = vp.canvas(title=f'arrow demo',
                      # caption="coordinates: ",
                      width=1200, height=800,
                      # center=vp.vector(middle[0], 0, middle[1]),
                      background=vp.color.gray(0.3),
                      # align="left",  # caption is to the right?
                      )

    fps = 60
    dt = 1 / fps
    # nodes = {}
    letters = {}
    cables = {}
    arrowspeed = 1.15
    arrow_length = 0.5
    blackarrows = {"AB": []}
    max_arrows = 0
    points = []
    distances = []


class Shadowarrow(vp.arrow):

    def __init__(self, nodestring="AB", flow=True, **kwargs):
        super().__init__(**kwargs)
        #print("black arrow created")
        if nodestring not in Sim.blackarrows:
            Sim.blackarrows[nodestring] = []
        Sim.blackarrows[nodestring].append(self)
        self.nodestring = nodestring
        self.flow = flow
        self.speed = Sim.arrowspeed
        self.color = vp.color.black
        self.shaftwidth = 0.03

        # get pos from nodestring and flow
        if flow:
            index = 0  # fly from A to B
            self.next_node = 1
            self.previous_node = 0
            self.axis = vp.norm(Sim.points[1] - Sim.points[0])
        else:
            index = -1  # fly from B to A
            self.next_node = -2
            self.previous_node = -1
            self.axis = vp.norm(Sim.points[-2] - Sim.points[-1])
        self.axis = vp.norm(self.axis) * Sim.arrow_length
        self.pos = Sim.points[index] - self.axis

    def update(self):
        self.pos += self.speed * Sim.dt * vp.norm(self.axis)
        self.distance_from_previous_point = vp.mag(self.pos - Sim.points[self.previous_node])
        if self.flow:
            if self.next_node < len(Sim.points):
                if (self.distance_from_previous_point + vp.mag(self.axis) / 2) > (
                        Sim.distances[self.next_node] - Sim.distances[self.previous_node]):
                    self.pos = Sim.points[self.next_node]
                    if self.next_node < (len(Sim.points) - 1):
                        self.axis = vp.norm(
                            Sim.points[self.next_node + 1] - Sim.points[self.next_node]) * Sim.arrow_length
                    else:
                        pass  # dont change axis
                    self.pos -= self.axis / 2
                    self.previous_node += 1
                    self.next_node += 1
            else:
                if self.distance_from_previous_point > vp.mag(self.axis) / 2:
                    # self.visible = False
                    self.color = vp.color.red
                    # go to waiting
                    self.speed = 0
        # else: # flow = False
        # if self.next_node > 0:
        # if (self.distance_from_previous_point + vp.mag(self.axis)/2) > (Sim)


def create_stuff():
    # axis arrows with letters
    vp.arrow(axis=vp.vector(1, 0, 0), color=vp.color.red, pickable=False)
    vp.arrow(axis=vp.vector(0, 1, 0), color=vp.color.green, pickable=False)
    vp.arrow(axis=vp.vector(0, 0, 1), color=vp.color.blue, pickable=False)
    # ground floor (with map)
    vp.box(pos=vp.vector(Sim.mapsize / 2, -0.05, Sim.mapsize / 2),
           # pos=Sim.center + vp.vector(0, -0.01, 0),
           size=vp.vector(Sim.mapsize, 0.015, Sim.mapsize),
           )
    # ------- nodes -------------
    # create cable AB
    Sim.cables["AB"] = []
    for n in range(10):
        x = Sim.mapsize / 10 * n + 0.5
        z = vp.random() * ((Sim.mapsize - 1) / 2) + 0.5
        Sim.cables["AB"].append(vp.box(pos=vp.vector(x, 0.0, z),
                                       size=vp.vector(0.2, 0.2, 0.2),
                                       color=vp.color.cyan,
                                       opacity=0.5))
        Sim.letters[n] = vp.label(pos=vp.vector(x, 0.25, z),
                                  text="A" if n == 0 else "B" if n == 9 else f"{n}",
                                  color=vp.color.black,
                                  box=False,
                                  opacity=0)
    Sim.points = [box.pos for box in Sim.cables["AB"]]  # list of vectors
    Sim.distances = []
    for n, point in enumerate(Sim.points):
        if n == 0:
            distance = 0
        else:
            distance += vp.mag(point - Sim.points[n - 1])
        Sim.distances.append(distance)
    Sim.max_arrows = Sim.distances[-1] / Sim.arrow_length / 2
    # create 2 black arrows
    # Shadowarrow("AB", True)
    # Shadowarrow("AB", False)


def get_min_distance(nodestring="AB"):
    # get minmial distance from point A to closest Arrow
    min_distance = Sim.distances[-1]  # maximal possible distance
    for a in Sim.blackarrows[nodestring]:
        if a.flow:
            distance = a.distance_from_previous_point + Sim.distances[a.previous_node]
            if distance < min_distance:
                min_distance = distance
    return min_distance


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
            # spawn arrows
            #print("arrows:", len(Sim.blackarrows), Sim.max_arrows)
            if len(Sim.blackarrows["AB"]) < Sim.max_arrows:
                if len(Sim.blackarrows["AB"]) == 0:
                    Shadowarrow()
                else:
                    mindist = get_min_distance("AB")
                    if mindist > Sim.arrow_length * 2:

                        waiting_arrows = [a for a in Sim.blackarrows["AB"] if a.speed == 0]
                        if len(waiting_arrows) == 0:
                            Shadowarrow()
                        else:
                            # recycle one of the red waiting arrows
                            a = waiting_arrows[0]
                            a.pos = Sim.points[0]
                            a.axis = vp.norm(Sim.points[1] - Sim.points[0]) * Sim.arrow_length
                            a.pos -= a.axis 
                            a.visible = True
                            a.color = vp.color.black
                            a.speed = Sim.arrowspeed
                            a.previous_node = 0
                            a.next_node = 1

            # move arrows
            print("moving arrows")
            for nodestring, arrowlist in Sim.blackarrows.items():
                for blackarrow in arrowlist:
                    blackarrow.update()


if __name__ == "__main__":
    create_stuff()
    main()
