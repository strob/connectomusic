import vinyl
import offline
import numm

import cv2

scale=2

for side in 'ABCD':
    print side

    params = getattr(vinyl, side)
    player = offline.init(params)

    # Set to high-resolution
    base = player._get_base_frame(scale=scale)

    # create a one-bit screen from the base
    base[base==0] = 255
    base[base<255]= 0

    numm.np2image(base, '%s-base.png' % (side))

    # describe the initial conditions as a same-sized set of circles

    initial = base.copy()
    initial[:] = 255

    def s(pt):
        return (pt[0]*scale, pt[1]*scale)

    for nodestate in player._state_nodes:
        cv2.circle(initial, s(nodestate.node.pt), int(5*scale), (0, 0, 0), -1)

    numm.np2image(initial, '%s-initial.png' % (side))

    # and accumulate a set of the first N edges out from the initial condition
    N = 150
    edges = set()

    while len(edges) < N:
        player.next()
        for edgestate in player._state_edges:
            edges.add(edgestate.edge)

    inprog = base.copy()
    inprog[:] = 255

    for edge in edges:
        cv2.line(inprog, s(edge.a.pt), s(edge.b.pt), (0, 0, 0), scale)

    numm.np2image(inprog, '%s-edges.png' % (side))

    # And finally render a merged image as a preview
    comp = base.copy()
    comp[:,:,1] = initial[:,:,1]
    comp[:,:,2] = inprog[:,:,2]

    numm.np2image(comp, '%s-comp.png' % (side))
