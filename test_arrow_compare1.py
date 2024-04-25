import vpython as vp
import os.path

VERSION = "4b"

class Sim:
    start_turning_distance1 = 2
    start_turning_distance2 = 1 ## 2?
    running = False
    mapsize = 10
    scene = vp.canvas(title='',
                      caption=f"arrowdemo version {VERSION} ",
                      width=1200, height=800,
                      # center=vp.vector(middle[0], 0, middle[1]),
                      background=vp.color.gray(0.3),
                      # align="left",  # caption is to the right?
                      )

    fps = 60
    dt = 1 / fps
    # nodes = {}
    letters = {"AB":{},
               "CD":{},
               "EF":{},
               "GH":{},
               }
    cables = {"AB":{},
              "CD":{},
              "EF": {},
              "GH": {},
              }
    arrow_text = "\U0001F5F2" # flash
    arrow_speed = 0.45
    arrow_turn_speed = 90 # ° per second?
    arrow_length = 0.25
    arrow_flow = True   # fly from A to B. False: B to A
    arrow_spacing = 2.5 # 2 arrowlengths from tip to tip
    shadowballradius = 0.125
    blackarrows = {"AB": [],
                   "CD": [],
                   "EF": [],
                   "GH": [],
                   }
    max_arrows = 0
    points = {"AB":[],
              "CD":[],
              "EF": [],
              "GH": [],
              }
    distances = {"AB":[],
                 "CD":[],
                 "EF": [],
                 "GH": [],
                 }




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
        #print("black arrow created")
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
            self.axis = vp.norm(Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0])
        else:
            index = -1  # fly from B to A
            self.next_point = -2
            self.previous_point = -1
            self.axis = vp.norm(Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1])
        self.axis = vp.norm(self.axis) * Sim.arrow_length
        self.new_axis = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.fly_direction = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.pos = Sim.points[self.nodestring][index] - self.axis

    def flip_direction(self):
        #if not self.turning:
        #    middle = self.pos + self.axis / 2
        #    self.axis = -self.axis
        #    self.pos = middle - self.axis / 2
        #else:
        #middle = self.pos + self.fly_direction / 2
        #self.axis = -self.axis
        #self.pos = middle - self.fly_direction / 2
        #self.fly_direction = -self.fly_direction
        #self.flow = Sim.arrow_flow
        # remove arrows with a None..
        #if (self.next_point is None) or (self.previous_point is None):
        #    self.color = vp.color.orange
        #    self.speed = 0
        # ------- new code --------
        ##if (self.next_point is None) or (self.previous_point is None):
        ##    self.color = vp.color.orange
        ##   self.speed = 0

        self.flow = Sim.arrow_flow
        #self.fly_direction *= -1
        #self.axis *= -1
        if self.flow: # from A to B
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.next_point]-Sim.points[self.nodestring][self.previous_point]) * Sim.arrow_length
            elif self.previous_point is not None:
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point]-Sim.points[self.nodestring][self.previous_point-1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.yellow

        else: # from B to A
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point]-Sim.points[self.nodestring][self.next_point]) * Sim.arrow_length
            elif self.next_point is not None:
                self.new_axis = vp.norm(
                    Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][self.next_point+1]) * Sim.arrow_length
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
            self.distance_from_previous_point = vp.mag(self.pos - Sim.points[self.nodestring][self.previous_point])
        if self.next_point is not None:
            self.distance_from_next_point = vp.mag(self.pos - Sim.points[self.nodestring][self.next_point])
        #except IndexError:
        #    print("IndexError", self.previous_point, self.next_point)
        #    if self.next_point == len(Sim.points):
        #        self.next_point -= 1
        #if self.axis != self.fly_direction:
        #    self.turing = True
        #else:
        #    self.turing = False
        diff_angle = vp.diff_angle(self.fly_direction, self.axis)
        #print("diff angle, abs", diff_angle, abs(diff_angle))
        if abs(vp.diff_angle(self.axis, self.new_axis )) > 0.05:
            self.turning = True
        else:
            self.axis = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)
            self.turning = False
        if self.turning:
            diff_angle_old = abs(vp.diff_angle(self.axis, self.new_axis))
            #print("diff_angle:", vp.degrees(diff_angle), self.previous_point, self.next_point)
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
            #if self.next_point < len(Sim.points):
            if self.next_point is not None and self.previous_point is not None:
                # not at end
                #if (self.distance_from_previous_point + vp.mag(self.fly_direction) / 2) > (
                #        Sim.distances[self.next_point] - Sim.distances[self.previous_point]):
                prev_to_tip = self.distance_from_previous_point + vp.mag(self.fly_direction) * Sim.start_turning_distance1 ##2
                prev_to_tail = self.distance_from_previous_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][self.previous_point]
                if prev_to_tail < full_length < prev_to_tip:
                    #try: # if self.next_point + 1 == len(Sim.points) -> IndexError
                    #    self.new_axis = vp.norm(
                    #        Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    #except IndexError:
                    #    pass # do not change new_axis
                    if (self.next_point+1) < len(Sim.points[self.nodestring]): # no IndexError
                        self.new_axis = vp.norm(Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][self.next_point]) * Sim.arrow_length
                    else:
                        pass # do not change new_axis
                elif prev_to_tail > full_length:
                    self.pos = Sim.points[self.nodestring][self.next_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y,self.new_axis.z)

                    # reached new point, end turning
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(Sim.points[self.nodestring][self.next_point+1]-Sim.points[self.nodestring][self.next_point]) * Sim.arrow_length
                    #except IndexError:
                    else:
                        # apparently arrow reached end of AB direction and is waiting to be recycled
                        self.new_axis = vp.norm(Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0]) * Sim.arrow_length

                    self.previous_point += 1
                    self.next_point += 1

                    if self.next_point >= len(Sim.points[self.nodestring]):
                        self.next_point = None

                    #overshot = self.distance_from_previous_point + vp.mag(self.fly_direction) - (
                    #    Sim.distances[self.next_point] - Sim.distances[self.previous_point])
                    #self.pos = Sim.points[self.next_point]

            else: # at end
                if self.distance_from_previous_point > vp.mag(self.axis) / 2:
                #if self.distance_from_next_point < vp.mag
                    # self.visible = False
                    self.color = vp.color.red
                    # go to waiting
                    self.speed = 0
        elif not self.flow:
            # flying from next point to previous point
            #if self.previous_point >= 0:
            if self.previous_point is not None and self.next_point is not None:
                # not at end
                #print(self.next_point, self.previous_point)
                #if (self.distance_from_next_point + vp.mag(self.axis) / 2) > (
                #        Sim.distances[self.next_point] - Sim.distances[self.previous_point]):
                next_to_tip = self.distance_from_next_point + vp.mag(self.fly_direction) * Sim.start_turning_distance1 ##2
                next_to_tail = self.distance_from_next_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][self.previous_point]
                if next_to_tail < full_length < next_to_tip:
                    if (self.previous_point - 1) >= 0: # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point -1] - Sim.points[self.nodestring][self.previous_point]) * Sim.arrow_length
                    else:
                        pass # do not change new_axis
                elif next_to_tail > full_length:
                    self.pos = Sim.points[self.nodestring][self.previous_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][self.previous_point]) * Sim.arrow_length
                    else:
                        # apparently reached first waypoint, in BA direction, prepare for recycling
                        self.new_axis = vp.norm(Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1]) * Sim.arrow_length
                    self.previous_point -= 1
                    self.next_point -= 1

                    if self.previous_point <0 :
                        self.previous_point = None



            else: # at end
                if self.distance_from_next_point > vp.mag(self.axis) /2 :
                    # self.visible = False
                    self.color = vp.color.red
                    # go to waiting
                    self.speed = 0

        # if self.next_point > 0:
        # if (self.distance_from_previous_point + vp.mag(self.axis)/2) > (Sim)


class Shadowarrow2(vp.arrow):
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
            self.axis = vp.norm(Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0])
        else:
            index = -1  # fly from B to A
            self.next_point = -2
            self.previous_point = -1
            self.axis = vp.norm(Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1])
        self.axis = vp.norm(self.axis) * Sim.arrow_length
        self.new_axis = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.fly_direction = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        ##self.pos = Sim.points[self.nodestring][index] - self.axis
        self.middle = Sim.points[self.nodestring][index] - self.axis/2
        self.pos = self.middle - self.axis/2

    def flip_direction(self):
        # if not self.turning:
        #    middle = self.pos + self.axis / 2
        #    self.axis = -self.axis
        #    self.pos = middle - self.axis / 2
        # else:
        # middle = self.pos + self.fly_direction / 2
        # self.axis = -self.axis
        # self.pos = middle - self.fly_direction / 2
        # self.fly_direction = -self.fly_direction
        # self.flow = Sim.arrow_flow
        # remove arrows with a None..
        # if (self.next_point is None) or (self.previous_point is None):
        #    self.color = vp.color.orange
        #    self.speed = 0
        # ------- new code --------
        ##if (self.next_point is None) or (self.previous_point is None):
        ##    self.color = vp.color.orange
        ##   self.speed = 0

        self.flow = Sim.arrow_flow
        # self.fly_direction *= -1
        # self.axis *= -1
        if self.flow:  # from A to B
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][
                    self.previous_point]) * Sim.arrow_length
            elif self.previous_point is not None:
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point] - Sim.points[self.nodestring][
                    self.previous_point - 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.yellow

        else:  # from B to A
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point] - Sim.points[self.nodestring][
                    self.next_point]) * Sim.arrow_length
            elif self.next_point is not None:
                self.new_axis = vp.norm(
                    Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][
                        self.next_point + 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.blue
        # --- both ---
        self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)
        self.axis = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

    def update(self):
        #self.pos -= self.axis / 2
        if self.flow != Sim.arrow_flow:
            self.flip_direction()
        self.middle += self.speed * Sim.dt * vp.norm(self.fly_direction)
        # magnitude of a vector is always positive
        if self.previous_point is not None:
            self.distance_from_previous_point = vp.mag(self.middle - Sim.points[self.nodestring][self.previous_point])
        if self.next_point is not None:
            self.distance_from_next_point = vp.mag(self.middle - Sim.points[self.nodestring][self.next_point])
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
            oldpos = self.middle
            self.rotate(origin=self.middle,
                        angle=vp.radians(Sim.arrow_turn_speed) * Sim.dt * self.turn_direction,
                        axis=vp.vector(0, 1, 0))
            self.middle = oldpos
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
                prev_to_tip = self.distance_from_previous_point + vp.mag(self.fly_direction) * Sim.start_turning_distance2 ## 2?
                prev_to_tail = self.distance_from_previous_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][
                    self.previous_point]
                if prev_to_tail < full_length < prev_to_tip:
                    # try: # if self.next_point + 1 == len(Sim.points) -> IndexError
                    #    self.new_axis = vp.norm(
                    #        Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    #    pass # do not change new_axis
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][
                                self.next_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif prev_to_tail > full_length:
                    self.middle = Sim.points[self.nodestring][self.next_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][
                                self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    else:
                        # apparently arrow reached end of AB direction and is waiting to be recycled
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0]) * Sim.arrow_length

                    self.previous_point += 1
                    self.next_point += 1

                    if self.next_point >= len(Sim.points[self.nodestring]):
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
                next_to_tip = self.distance_from_next_point + vp.mag(self.fly_direction) * Sim.start_turning_distance2 ## 2?
                next_to_tail = self.distance_from_next_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][
                    self.previous_point]
                if next_to_tail < full_length < next_to_tip:
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][
                                self.previous_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif next_to_tail > full_length:
                    self.middle = Sim.points[self.nodestring][self.previous_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][
                                self.previous_point]) * Sim.arrow_length
                    else:
                        # apparently reached first waypoint, in BA direction, prepare for recycling
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1]) * Sim.arrow_length
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
        self.pos = self.middle - self.axis /2
        #self.pos += self.axis / 2
        # if self.next_point > 0:
        # if (self.distance_from_previous_point + vp.mag(self.axis)/2) > (Sim)


class Shadowball(vp.sphere):
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
        self.radius = Sim.shadowballradius

        # get pos from nodestring and flow
        if self.flow:
            index = 0  # fly from A to B
            self.next_point = 1
            self.previous_point = 0
            self.axis = vp.norm(Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0])
        else:
            index = -1  # fly from B to A
            self.next_point = -2
            self.previous_point = -1
            self.axis = vp.norm(Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1])
        self.axis = vp.norm(self.axis) * Sim.arrow_length
        self.new_axis = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.fly_direction = vp.vector(self.axis.x, self.axis.y, self.axis.z)
        self.pos = Sim.points[self.nodestring][index] - self.axis

    def flip_direction(self):
        # if not self.turning:
        #    middle = self.pos + self.axis / 2
        #    self.axis = -self.axis
        #    self.pos = middle - self.axis / 2
        # else:
        # middle = self.pos + self.fly_direction / 2
        # self.axis = -self.axis
        # self.pos = middle - self.fly_direction / 2
        # self.fly_direction = -self.fly_direction
        # self.flow = Sim.arrow_flow
        # remove arrows with a None..
        # if (self.next_point is None) or (self.previous_point is None):
        #    self.color = vp.color.orange
        #    self.speed = 0
        # ------- new code --------
        ##if (self.next_point is None) or (self.previous_point is None):
        ##    self.color = vp.color.orange
        ##   self.speed = 0

        self.flow = Sim.arrow_flow
        # self.fly_direction *= -1
        # self.axis *= -1
        if self.flow:  # from A to B
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][
                    self.previous_point]) * Sim.arrow_length
            elif self.previous_point is not None:
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point] - Sim.points[self.nodestring][
                    self.previous_point - 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.yellow

        else:  # from B to A
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point] - Sim.points[self.nodestring][
                    self.next_point]) * Sim.arrow_length
            elif self.next_point is not None:
                self.new_axis = vp.norm(
                    Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][
                        self.next_point + 1]) * Sim.arrow_length
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
            self.distance_from_previous_point = vp.mag(self.pos - Sim.points[self.nodestring][self.previous_point])
        if self.next_point is not None:
            self.distance_from_next_point = vp.mag(self.pos - Sim.points[self.nodestring][self.next_point])
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
                prev_to_tip = self.distance_from_previous_point + vp.mag(
                    self.fly_direction) * Sim.start_turning_distance1  ##2
                prev_to_tail = self.distance_from_previous_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][
                    self.previous_point]
                if prev_to_tail < full_length < prev_to_tip:
                    # try: # if self.next_point + 1 == len(Sim.points) -> IndexError
                    #    self.new_axis = vp.norm(
                    #        Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    #    pass # do not change new_axis
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][
                                self.next_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif prev_to_tail > full_length:
                    self.pos = Sim.points[self.nodestring][self.next_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][
                                self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    else:
                        # apparently arrow reached end of AB direction and is waiting to be recycled
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0]) * Sim.arrow_length

                    self.previous_point += 1
                    self.next_point += 1

                    if self.next_point >= len(Sim.points[self.nodestring]):
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
                next_to_tip = self.distance_from_next_point + vp.mag(
                    self.fly_direction) * Sim.start_turning_distance1  ##2
                next_to_tail = self.distance_from_next_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][
                    self.previous_point]
                if next_to_tail < full_length < next_to_tip:
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][
                                self.previous_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif next_to_tail > full_length:
                    self.pos = Sim.points[self.nodestring][self.previous_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][
                                self.previous_point]) * Sim.arrow_length
                    else:
                        # apparently reached first waypoint, in BA direction, prepare for recycling
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1]) * Sim.arrow_length
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

        # if self.next_point > 0:
        # if (self.distance_from_previous_point + vp.mag(self.axis)/2) > (Sim)


class Shadowtext(vp.label):
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
        self.text = Sim.arrow_text
        self.box = False
        self.line = False
        self.opacity = 0
        #self.radius = Sim.shadowballradius

        # get pos from nodestring and flow
        if self.flow:
            index = 0  # fly from A to B
            self.next_point = 1
            self.previous_point = 0
            self.axis2 = vp.norm(Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0])
        else:
            index = -1  # fly from B to A
            self.next_point = -2
            self.previous_point = -1
            self.axis2 = vp.norm(Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1])
        self.axis2 = vp.norm(self.axis2) * Sim.arrow_length
        self.new_axis = vp.vector(self.axis2.x, self.axis2.y, self.axis2.z)
        self.fly_direction = vp.vector(self.axis2.x, self.axis2.y, self.axis2.z)
        self.pos = Sim.points[self.nodestring][index] - self.axis2

    def flip_direction(self):
        # if not self.turning:
        #    middle = self.pos + self.axis / 2
        #    self.axis = -self.axis
        #    self.pos = middle - self.axis / 2
        # else:
        # middle = self.pos + self.fly_direction / 2
        # self.axis = -self.axis
        # self.pos = middle - self.fly_direction / 2
        # self.fly_direction = -self.fly_direction
        # self.flow = Sim.arrow_flow
        # remove arrows with a None..
        # if (self.next_point is None) or (self.previous_point is None):
        #    self.color = vp.color.orange
        #    self.speed = 0
        # ------- new code --------
        ##if (self.next_point is None) or (self.previous_point is None):
        ##    self.color = vp.color.orange
        ##   self.speed = 0

        self.flow = Sim.arrow_flow
        # self.fly_direction *= -1
        # self.axis *= -1
        if self.flow:  # from A to B
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][
                    self.previous_point]) * Sim.arrow_length
            elif self.previous_point is not None:
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point] - Sim.points[self.nodestring][
                    self.previous_point - 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.yellow

        else:  # from B to A
            if (self.next_point is not None) and (self.previous_point is not None):
                self.new_axis = vp.norm(Sim.points[self.nodestring][self.previous_point] - Sim.points[self.nodestring][
                    self.next_point]) * Sim.arrow_length
            elif self.next_point is not None:
                self.new_axis = vp.norm(
                    Sim.points[self.nodestring][self.next_point] - Sim.points[self.nodestring][
                        self.next_point + 1]) * Sim.arrow_length
            else:
                self.speed = 0
                self.color = vp.color.blue
        # --- both ---
        self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)
        self.axis2 = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

    def update(self):
        if self.flow != Sim.arrow_flow:
            self.flip_direction()
        self.pos += self.speed * Sim.dt * vp.norm(self.fly_direction)
        # magnitude of a vector is always positive
        if self.previous_point is not None:
            self.distance_from_previous_point = vp.mag(self.pos - Sim.points[self.nodestring][self.previous_point])
        if self.next_point is not None:
            self.distance_from_next_point = vp.mag(self.pos - Sim.points[self.nodestring][self.next_point])
        # except IndexError:
        #    print("IndexError", self.previous_point, self.next_point)
        #    if self.next_point == len(Sim.points):
        #        self.next_point -= 1
        # if self.axis != self.fly_direction:
        #    self.turing = True
        # else:
        #    self.turing = False
        diff_angle = vp.diff_angle(self.fly_direction, self.axis2)
        # print("diff angle, abs", diff_angle, abs(diff_angle))
        if abs(vp.diff_angle(self.axis, self.new_axis)) > 0.05:
            self.turning = True
        else:
            self.axis2 = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)
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
                prev_to_tip = self.distance_from_previous_point + vp.mag(
                    self.fly_direction) * Sim.start_turning_distance1  ##2
                prev_to_tail = self.distance_from_previous_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][
                    self.previous_point]
                if prev_to_tail < full_length < prev_to_tip:
                    # try: # if self.next_point + 1 == len(Sim.points) -> IndexError
                    #    self.new_axis = vp.norm(
                    #        Sim.points[self.next_point + 1] - Sim.points[self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    #    pass # do not change new_axis
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][
                                self.next_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif prev_to_tail > full_length:
                    self.pos = Sim.points[self.nodestring][self.next_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.next_point + 1) < len(Sim.points[self.nodestring]):  # no IndexError
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.next_point + 1] - Sim.points[self.nodestring][
                                self.next_point]) * Sim.arrow_length
                    # except IndexError:
                    else:
                        # apparently arrow reached end of AB direction and is waiting to be recycled
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][1] - Sim.points[self.nodestring][0]) * Sim.arrow_length

                    self.previous_point += 1
                    self.next_point += 1

                    if self.next_point >= len(Sim.points[self.nodestring]):
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
                next_to_tip = self.distance_from_next_point + vp.mag(
                    self.fly_direction) * Sim.start_turning_distance1  ##2
                next_to_tail = self.distance_from_next_point
                full_length = Sim.distances[self.nodestring][self.next_point] - Sim.distances[self.nodestring][
                    self.previous_point]
                if next_to_tail < full_length < next_to_tip:
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][
                                self.previous_point]) * Sim.arrow_length
                    else:
                        pass  # do not change new_axis
                elif next_to_tail > full_length:
                    self.pos = Sim.points[self.nodestring][self.previous_point]
                    self.fly_direction = vp.vector(self.new_axis.x, self.new_axis.y, self.new_axis.z)

                    # reached new point, end turning
                    if (self.previous_point - 1) >= 0:  # not at first point
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][self.previous_point - 1] - Sim.points[self.nodestring][
                                self.previous_point]) * Sim.arrow_length
                    else:
                        # apparently reached first waypoint, in BA direction, prepare for recycling
                        self.new_axis = vp.norm(
                            Sim.points[self.nodestring][-2] - Sim.points[self.nodestring][-1]) * Sim.arrow_length
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

        # if self.next_point > 0:
        # if (self.distance_from_previous_point + vp.mag(self.axis)/2) > (Sim)


def widget_func_button_flow(b):
    Sim.arrow_flow = not Sim.arrow_flow
    #for a in Sim.blackarrows["AB"]:
    #    a.flip_direction()
    if Sim.arrow_flow:
        Sim.button_flow.text = "Flow is now: A to B"
    else:
        Sim.button_flow.text = "Flow is now: B to A"

def widget_func_input1(b):

    Sim.start_turning_distance1 = max(0.01, b.number)

def widget_func_input2(b):
    Sim.start_turning_distance2 = max(0.01, b.number)

def widget_func_turnspeed(b):
    Sim.arrow_turn_speed = b.number

def create_widgets():
    Sim.button_flow =  vp.button(pos=Sim.scene.title_anchor, text="Flow is now: A to B", bind=widget_func_button_flow)
    Sim.scene.append_to_title("AB starts turing at:")
    vp.winput(pos=Sim.scene.title_anchor, bind=widget_func_input1, type="numeric", text=Sim.start_turning_distance1 )
    Sim.scene.append_to_title("CD starts turning at:")
    vp.winput(pos=Sim.scene.title_anchor, bind=widget_func_input2, type="numeric", text=Sim.start_turning_distance2)
    Sim.scene.append_to_title("turn speed:")
    vp.winput(pos=Sim.scene.title_anchor, bind=widget_func_turnspeed, type="numeric", text=Sim.arrow_turn_speed)

def create_stuff():
    #vp.label(text="\U0001F5F2")
    # axis arrows with letters
    vp.arrow(axis=vp.vector(1, 0, 0), color=vp.color.red, pickable=False)
    vp.arrow(axis=vp.vector(0, 1, 0), color=vp.color.green, pickable=False)
    vp.arrow(axis=vp.vector(0, 0, 1), color=vp.color.blue, pickable=False)
    # ground floor (with map)
    colors = (vp.color.gray(3), vp.color.gray(22))
    for stripe_number in range(4):
        vp.box(pos=vp.vector(Sim.mapsize / 2 , -0.05, Sim.mapsize / 4 + (Sim.mapsize / 2 * stripe_number)),
           # pos=Sim.center + vp.vector(0, -0.01, 0),
           size=vp.vector(Sim.mapsize, 0.015, Sim.mapsize/2),
           color=vp.color.orange if stripe_number % 2 == 0 else vp.color.purple,
           )
    # ------- nodes -------------
    track_colors = [vp.color.cyan, vp.color.orange, vp.color.red, vp.color.yellow]
    for track_number, nodestring in enumerate(("AB", "CD", "EF","GH")):
        # create cable AB
        Sim.cables[nodestring] = []
        for n in range(10):
            x = Sim.mapsize / 10 * n + 0.5
            z = vp.random() * ((Sim.mapsize - 1) / 2)  + 0.5 + track_number* Sim.mapsize/2
            Sim.cables[nodestring].append(vp.box(pos=vp.vector(x, 0.0, z),
                                           size=vp.vector(0.2, 0.2, 0.2),
                                           #color=vp.color.cyan,
                                           color=track_colors[track_number],
                                           opacity=0.5))
            Sim.letters[nodestring][n] = vp.label(pos=vp.vector(x, 0.25, z),
                                      text=nodestring[0] if n == 0 else nodestring[-1] if n == 9 else f"{n}",
                                      color=vp.color.black,
                                      box=False,
                                      opacity=0)
        Sim.points[nodestring] = [box.pos for box in Sim.cables[nodestring]]  # list of vectors
        Sim.distances[nodestring] = []
        for n, point in enumerate(Sim.points[nodestring]):
            if n == 0:
                distance = 0
            else:
                distance += vp.mag(point - Sim.points[nodestring][n - 1])
            Sim.distances[nodestring].append(distance)
        Sim.max_arrows = Sim.distances[nodestring][-1] / (Sim.arrow_length * Sim.arrow_spacing)
        print(Sim.distances[nodestring][-1], Sim.max_arrows)
        # create 2 black arrows
        # Shadowarrow("AB", True)
        # Shadowarrow("AB", False)
        #vp.label(pos=vp.vector(0,0,5),
        #       size=vp.vector(1,0.1,1),
        #         text="60%",
        #       texture=os.path.join("assets", "pie_percent_60.png"))



def get_min_distance(nodestring="AB"):
    # get minmial distance from point A to closest Arrow
    min_distance = Sim.distances[nodestring][-1]  # maximal possible distance (from Point A to last Waypoint (B))
    for a in Sim.blackarrows[nodestring]:
        if a.flow:  # from A to B
            if a.previous_point is None:
                continue
            #print(a.previous_point)
            distance = a.distance_from_previous_point + Sim.distances[nodestring][a.previous_point]
            if distance < min_distance:
                min_distance = distance
        else:      # from B to A
            if a.next_point is None:
                continue
            distance = a.distance_from_next_point + Sim.distances[nodestring][-1] - Sim.distances[nodestring][a.next_point]
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
            for nodestring in ["AB","CD","EF","GH"]:
                if len(Sim.blackarrows[nodestring]) < Sim.max_arrows:
                    if len(Sim.blackarrows[nodestring]) == 0:
                        if nodestring == "AB":
                            Shadowarrow(nodestring=nodestring)
                        elif nodestring == "CD":
                            Shadowarrow2(nodestring=nodestring)
                        elif nodestring == "EF":
                            Shadowball(nodestring=nodestring)
                        elif nodestring == "GH":
                            Shadowtext(nodestring=nodestring)
                    else:
                        mindist = get_min_distance(nodestring) # shortest distance from an arrow to node A or B
                        if mindist > Sim.arrow_length * Sim.arrow_spacing:
                            waiting_arrows = [a for a in Sim.blackarrows[nodestring] if a.speed == 0]
                            if len(waiting_arrows) == 0:
                                if nodestring == "AB":
                                    Shadowarrow(nodestring=nodestring)
                                elif nodestring == "CD":
                                    Shadowarrow2(nodestring=nodestring)
                                elif nodestring == "EF":
                                    Shadowball(nodestring=nodestring)
                                elif nodestring == "GH":
                                    Shadowtext(nodestring=nodestring)
                            else:
                                # recycle one of the red waiting arrows
                                a = waiting_arrows[0]
                                if a.flow:
                                    a.pos = Sim.points[nodestring][0]
                                    a.axis = vp.norm(Sim.points[nodestring][1] - Sim.points[nodestring][0]) * Sim.arrow_length
                                    a.fly_direction = vp.norm(Sim.points[nodestring][1]-Sim.points[nodestring][0]) * Sim.arrow_length
                                    a.color = vp.color.blue
                                    a.previous_point = 0
                                    a.next_point = 1
                                else:
                                    a.pos = Sim.points[nodestring][-1]
                                    a.axis = vp.norm(Sim.points[nodestring][-2] - Sim.points[nodestring][-1]) * Sim.arrow_length
                                    a.fly_direction = vp.norm(Sim.points[nodestring][-2] - Sim.points[nodestring][-1]) * Sim.arrow_length
                                    a.previous_point = len(Sim.points[nodestring]) -2
                                    a.next_point = len(Sim.points[nodestring]) - 1
                                    a.color = vp.color.yellow
                                a.pos -= a.axis
                                a.visible = True
                                a.new_axis = vp.vector(a.axis.x, a.axis.y, a.axis.z)
                                #a.color = vp.color.purple
                                a.speed = Sim.arrow_speed


            # move arrows
            #print("moving arrows")
            for nodestring2, arrowlist in Sim.blackarrows.items():
                for blackarrow in arrowlist:
                    blackarrow.update()


if __name__ == "__main__":
    create_stuff()
    create_widgets()
    main()
