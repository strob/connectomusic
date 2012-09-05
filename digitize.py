import numm
import cv2
import numpy as np
import pickle

PATH = 'a.png'
# PATH = 'b.png'

net = numm.image2np(PATH)

MOUSEX = 0
MOUSEY = 0
PX = 0
PY = 0
OFFX = 0
OFFY = 0
CIRCLES = [] 
EDGES = []

def find_circles(img, cutoff=125, blur=10, min_area=2, max_area=50):
    blur = cv2.blur(img, (blur, blur))
    blur = blur.mean(axis=2)

    threshold = (blur < cutoff).astype(np.uint8)

    contours, hierarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    circles = [cv2.minEnclosingCircle(X) for X in contours]
    circles = filter(lambda (xy,r): r*2*np.pi >= min_area and r*2*np.pi <= max_area, circles)

    return circles

def find_edges(img, circles, maxdepth=50):
    edges = set()

    circlearray = np.array([(x,y,r) for ((x,y),r) in circles])

    def _in_circle(x,y):
        # XXX: could precompute by drawing circles to array
        test = (np.hypot(circlearray[:,0]-x, circlearray[:,1]-y) - circlearray[:,2] < 0)
        if sum(test) > 0:
            (x,y) = circlearray[test.argmax(),:2].astype(int)
            return (x,y)

    for (x,y),r, in circles:
        (x,y) = (int(x),int(y))

        tested_indices = set([(x,y)])

        def _iterate(x1,y1,depth=0):
            # recursive function to dynamically explore for edges
            for (dx,dy) in [[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]:
                (x2,y2) = (x1+dx,y1+dy)
                if not (x2,y2) in tested_indices:
                    tested_indices.add((x2,y2))

                    incircle = _in_circle(x2,y2)

                    if incircle is not None and incircle != (x,y):
                        print 'edge', (incircle, (x,y))
                        edges.add((incircle, (x,y)))
                        edges.add(((x,y), incircle))
                        break
                    elif y2<img.shape[0] and x2<img.shape[1] and img[y2,x2,0] < 125 and depth < maxdepth:
                        # don't exceed recursion depth
                        # grrr python !!
                        _iterate(x2,y2,depth+1)

        _iterate(x,y)

    return edges

def video_out(a):

    circles = CIRCLES #find_circles(net, cutoff=CUTOFF)

    c_out = np.zeros(net.shape, dtype=np.uint8)

    for xy,r in circles:
        x = int(xy[0])
        y = int(xy[1])
        r = int(r)

        cv2.circle(c_out, (x,y), r, (0, 255, 0), -1)

    edges = EDGES

    for xy1, xy2 in edges:
        cv2.line(c_out, xy1, xy2, (255,0,0))


    a[:] = net[OFFY:OFFY+240,OFFX:OFFX+320]
    a += c_out[OFFY:OFFY+240,OFFX:OFFX+320]

def mouse_in(type, px, py, button):
    global MOUSEX, MOUSEY, PX, PY
    MOUSEX = px
    MOUSEY = py

    if type == 'mouse-button-press':
        PX = MOUSEX
        PY = MOUSEY
    elif type == 'mouse-button-release':
        x1 = PX*320
        y1 = PY*240

        x2 = MOUSEX*320
        y2 = MOUSEY*240

        r = np.hypot(x1-x2,y1-y2)

        CIRCLES.append(((x1+OFFX,y1+OFFY),r))
        

def keyboard_in(type, key):
    global CIRCLES, EDGES, OFFX, OFFY

    if type == 'key-press':
        if key == 'e':
            pickle.dump(CIRCLES, open(PATH + '.circles.pkl', 'w'))

            EDGES = find_edges(net, CIRCLES)
            pickle.dump(EDGES, open(PATH + '.edges.pkl', 'w'))

        elif key == 'l':
            CIRCLES = pickle.load(open(PATH + '.circles.pkl'))
            EDGES = pickle.load(open(PATH + '.edges.pkl'))

        elif key == 'c':
            cutoff = int(MOUSEX*255)
            CIRCLES = find_circles(net, cutoff=cutoff)

        elif key == 'o':
            OFFX = int(MOUSEX * (net.shape[1]-320))
            OFFY = int(MOUSEY * (net.shape[0]-240))
