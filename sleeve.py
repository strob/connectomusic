import vinyl
import offline
import numm
import Image

import cv2

scale=2
thick=4

def save(np, path):
    lines = np[:,:,0]
    lines[lines>0] = 255
    alpha = lines.copy()
    lines[:] = 0

    im = Image.fromarray(lines, mode='L')
    im.putalpha(Image.fromarray(alpha, mode='L'))
    im.save(path)

for side in 'ABCD':
    print side

    params = getattr(vinyl, side)
    player = offline.init(params)

    # Set to high-resolution
    base = player._get_base_frame(scale=scale,thick=thick)

    # numm.np2image(base, '%s-base.png' % (side))
    save(base, '%s-base.png' % (side))

    # describe the initial conditions as a same-sized set of circles

    initial = base.copy()
    initial[:] = 0

    def s(pt):
        return (pt[0]*scale, pt[1]*scale)

    for nodestate in player._state_nodes:
        cv2.circle(initial, s(nodestate.node.pt), int(5*scale), (255, 255, 255), -1)

    # numm.np2image(initial, '%s-initial.png' % (side))
    save(initial, '%s-initial.png' % (side))

    # and accumulate a set of the first N edges out from the initial condition
    N = 150
    edges = set()

    while len(edges) < N:
        player.next()
        for edgestate in player._state_edges:
            edges.add(edgestate.edge)

    inprog = base.copy()
    inprog[:] = 0

    for edge in edges:
        cv2.line(inprog, s(edge.a.pt), s(edge.b.pt), (255, 255, 255), int(round(scale*thick*1.5)))

    # numm.np2image(inprog, '%s-edges.png' % (side))
    save(inprog, '%s-edges.png' % (side))

    # And finally render a merged image as a preview
    comp = base.copy()
    comp[:,:,1] = initial[:,:,1]
    comp[:,:,2] = inprog[:,:,2]

    numm.np2image(comp, '%s-comp.png' % (side))
