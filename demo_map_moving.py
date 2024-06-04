import vpython as vp
import random

vp.arrow(axis=vp.vec(1,0,0), color=vp.color.red)
vp.arrow(axis=vp.vec(0,1,0), color=vp.color.green)
vp.arrow(axis=vp.vec(0,0,1), color=vp.color.blue)

boxes = []
for x in range(40):
    line = []
    for z in range(20):
        line.append(vp.box(pos=vp.vec(x+0.5,0,z+0.5),
                           size=vp.vec(0.9,0.1,0.9),
                           color=vp.color.gray(0.5)))
    boxes.append(line)


while True:
    vp.rate(5)
    for x in range(40):
        for z in range(20):
            b = boxes[x][z]
            b.size.y += random.choice((-0.6,-0.5,-0.4, -0.3, -0.2, -0.1, 0.0, 0.0, 0.1, 0.2, 0.2,0.3))
            b.size.y = max(0.1, b.size.y)
            b.size.y = min(10.0, b.size.y)
            b.pos.y = b.size.y /2
            b.color = vp.vec(b.size.y / 10, 0, 1-b.size.y/10)