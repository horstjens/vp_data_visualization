import vpython as vp
import random

class Game:
    scene = vp.canvas(title='firework',
                      # caption="coordinates: ",
                      width=1200, height=800,
                      center=vp.vector(0, 0, 0),
                      background=vp.color.gray(0.8),
                      )
    fps = 100
    dt = 1/fps
    grid_max = 50
    grid_step = 5
    arrowlist = []

def create_stuff():
    # arrows
    vp.arrow(axis=vp.vector(1,0,0), color=vp.color.red)
    vp.arrow(axis=vp.vector(0,1,0), color=vp.color.green)
    vp.arrow(axis=vp.vector(0,0,1), color=vp.color.blue)
    vp.text(pos=vp.vector(1.5,0,0), text="x", color=vp.color.red)
    vp.text(pos=vp.vector(0, 1.5, 0), text="y", color=vp.color.green)
    vp.text(pos=vp.vector(0,0,1.5), text="z", color=vp.color.blue)
    # ground
    vp.box(pos = vp.vector(0,-0.1,0),
           color=vp.color.gray(0.5),
           size=vp.vector(Game.grid_max, 0.2, Game.grid_max),
           pickable=False,
           )
    # grid
    for x in range(-Game.grid_max//2, Game.grid_max//2, Game.grid_step):
        vp.curve(pos=[vp.vector(x,0,-Game.grid_max/2), vp.vector(x, 0, Game.grid_max/2)],
                 color=vp.color.black, radius=0.01)
    for z in range(-Game.grid_max // 2, Game.grid_max // 2, Game.grid_step):
        vp.curve(pos=[vp.vector(-Game.grid_max / 2,0,z), vp.vector(Game.grid_max / 2,0,z)],
                 color=vp.color.black, radius=0.01)

    # some random black balls

    #for _ in range(7):
    #    vp.sphere(pos=vp.vector(random.uniform(-Game.grid_max/2, Game.grid_max/2),
    #                            random.uniform(0,1.5),
    #                            random.uniform(-Game.grid_max/2, Game.grid_max/2)),
    #              radius = random.uniform(0.1, 0.5),
    #              color=vp.color.black)
    vp.box(pos = vp.vector(1,3,-1), size=vp.vector(2,6,0.1),color=vp.color.black)
    vp.box(pos=vp.vector(3.9, 3, 0), size=vp.vector(2, 6, 0.1), color=vp.color.gray(0.6))
    # Node A
    Game.node_a = vp.cylinder(pos = vp.vector(-5,0,-2), axis=vp.vector(0,3,0),radius=0.5,color=vp.color.red)
    # Node B
    Game.node_b = vp.cylinder(pos = vp.vector(7,0,1.5), axis=vp.vector(0,3,0),radius=0.5,color=vp.color.red)
    # cable AB
    Game.cable_ab = vp.cylinder(pos=Game.node_a.pos + vp.vector(0,2,0), axis=Game.node_b.pos - Game.node_a.pos, radius=0.25, opacity=0.25, ) #color=vp.color.white)

class FlyingArrow(vp.arrow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = 2.5
        # create light
        self.color=vp.color.blue
        self.emissive = True
        self.light = vp.local_light(pos=self.pos, color=vp.color.white*0.3)

    def update(self, dt):
        new_pos = self.pos + vp.norm(self.axis) * self.speed * dt
        if vp.mag(Game.node_a.pos - new_pos ) > vp.mag(Game.node_a.pos - Game.node_b.pos):
            self.pos = vp.vector(Game.node_a.pos.x, self.pos.y, Game.node_a.pos.z)
        else:
            self.pos = new_pos
        self.light.pos = self.pos



def main():
    create_stuff()
    Game.arrowlist.append(
        FlyingArrow(pos=Game.node_a.pos + vp.vector(0,2,0),
                    axis=vp.norm(Game.node_b.pos - Game.node_a.pos) * 0.5,
                    ))
    Game.arrowlist.append(
        FlyingArrow(pos=Game.node_a.pos + vp.vector(0,2,0) + (Game.node_b.pos - Game.node_a.pos) /2,
                    axis=vp.norm(Game.node_b.pos - Game.node_a.pos) * 0.5,
                    ))
    while True:
        vp.rate(Game.fps)
        for arrow in Game.arrowlist:
            arrow.update(Game.dt)

if __name__ == "__main__":
    main()