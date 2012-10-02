import cv2
import sys
import numpy as np

import graph
import pickle
from player import Player

USAGE = 'python ui.py (left|right) EDGES SOUND [SOUND [SOUND ...]]'

if len(sys.argv) < 3:
    print USAGE
    sys.exit(1)

new_edges = pickle.load(open("ALL_EDGES.pkl"))

if sys.argv[1] == 'left':
    # XXX: Prune to left_nodes
    pass
elif sys.argv[1] != 'right':
    print USAGE
    sys.exit(1)

id_to_node = {}
def _intpt(pt):
    return (int(pt[0]), int(pt[1]))

def _node(X):
    if X._id not in id_to_node:
        id_to_node[X._id] = graph.Node(_intpt(X.get_center()))
    return id_to_node[X._id]

edges = [graph.Edge(_node(X[0]), _node(X[1]),
                    cost=np.hypot(*(np.array(X[0].get_center())-X[1].get_center())))
         for X in new_edges]
g = graph.Graph(edges)

#g = graph.load_graph(sys.argv[1], directed=True)
graph.connect_to_samples(g, sys.argv[2:])

p = Player(g, speed=150, decay=0.98)

H,W,_depth = p.draw().shape
divisor = 1
mousex, mousey = 0,0

recording = False
rec_audio = []
rec_video = None

def mouse_in(type, px, py, button):
    global mousex, mousey
    mousex = px
    mousey = py
    if type=='mouse-button-press':
        nearest = g.nearest(px*W, py*H)
        p.trigger(nearest, 1.0)

def audio_out(a):
    global divisor
    out = p.next(len(a))
    divisor = max(out.max() / float(2**15-1), divisor)

    if recording:
        rec_audio.append(out)

    out /= divisor
    a[:] = out.astype(np.int16)

def video_out(a):
    global rec_video

    im = p.draw()

    if recording:
        if rec_video is None:
            rec_video = cv2.VideoWriter()
            rec_video.open('rec.avi', cv2.cv.CV_FOURCC(*'MJPG'), 30, (im.shape[1], im.shape[0]), True)

        rec_video.write(im)

    im = cv2.resize(im, (320,240))
    # im = im[:240,:320]
    a[:] = im

def keyboard_in(type, key):
    global recording, rec_audio, rec_video

    if type=='key-press':
        if key=='p':
            p._target += 1
        elif key=='n':
            p._target -= 1

        elif key=='d':
            p._decay = pow(mousex, 0.25)
            print 'decay', p._decay
        elif key=='s':
            p._speed = 200*mousex
            print 'speed', p._speed

        elif key=='r':
            if recording:
                recording = False

                out = np.concatenate(rec_audio)
                out /= out.max() / float(2**15-1)
                numm.np2sound(out.astype(np.int16),
                              'rec.wav')

            else:
                rec_audio = []
                rec_video = None
                recording = True

if __name__=='__main__':
    import numm
    numm.run(**globals())
