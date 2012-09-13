import cv2
import sys
import numpy as np

import graph
from player import Player

USAGE = 'python ui.py EDGES SOUND [SOUND [SOUND ...]]'

if len(sys.argv) < 3:
    print USAGE
    sys.exit(1)

g = graph.load_graph(sys.argv[1], directed=True)
graph.connect_to_samples(g, sys.argv[2:])

p = Player(g, speed=50)

H,W,_depth = p.draw().shape
divisor = 1

def mouse_in(type, px, py, button):
    if type=='mouse-button-press':
        nearest = g.nearest(px*W, py*H)
        p.trigger(nearest, 1.0)

def audio_out(a):
    global divisor
    out = p.next(len(a))
    divisor = max(out.max() / float(2**15-1), divisor)
    out /= divisor
    a[:] = out.astype(np.int16)

def video_out(a):
    im = p.draw()
    im = cv2.resize(im, (320,240))
    a[:] = im

def keyboard_in(type, key):
    print type, key
    if type=='key-press':
        if key=='p':
            p._target += 1
        elif key=='n':
            p._target -= 1

if __name__=='__main__':
    import numm
    numm.run(**globals())

# def key_press(k):
#     print 'key', k
# def mouse_event(ev, x, y, button, flags):
#     if ev == cv2.EVENT_LBUTTONDOWN:
#         print 'click', x, y
#         nearest = g.nearest(x, y)
#         p.trigger(nearest, 1.0)

# cv2.namedWindow("CONNECTOMUSIC")
# cv2.setMouseCallback("CONNECTOMUSIC", mouse_event)

# import pyaudio
# audio = pyaudio.PyAudio()
# stream = audio.open(format = pyaudio.paInt16,
#                 channels = 2,
#                 rate = 44100,
#                 output = True)

# while 1:
#     cv2.imshow("CONNECTOMUSIC", p.draw())

#     out = p.next(44100/10)
#     print out.shape, out.min(), out.max()
#     if out.max() > 0:
#         out /= out.max() / float(2**15-1)
#     else:
#         print 'zero'
#     print out.shape, out.min(), out.max()
    
#     stream.write(out.astype(np.int16).tostring())

#     ch = cv2.waitKey(30)
#     if ch == 27:                # quit
#         break
#     elif ch > -1 and ch < 256:
#         key_press(chr(ch))

# cv2.destroyAllWindows()
# stream.stop_stream()
# stream.close()
# audio.terminate()

