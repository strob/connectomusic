libpath = '/home/rmo/src/connectomusic'
import sys
sys.path.append(libpath)
import os
os.chdir(libpath)

import graph
import player

g = graph.connected_directed_graph()
p = player.Player(g)

#--

# set resolution

p = player.Player(g, scale=800/1500.0, thick=2)

#--


p.thick=1
p._baseframe = None

#--

# selections

CENTER = [[602, 833]]
CORNERS = [[48, 1234], [1194, 1239], [1196, 47], [41, 73]]

def buttonFunction(k, v):
    def onclick():
        p.select_by_coords(v)
    return onclick

def trigger():
    p.trigger_selection()


def inhibit():
    p._state_nodes = []
    p._state_edges = []
    for n in p.graph.get_all_nodes():
        n.release_sound()

def saturate():
    p._selection = list(g.get_all_nodes())[:p._target]

zoom = None
def toggleZoom():
    global zoom
    if zoom is None and len(p._selection) > 0:
        zoom = p._selection[0]
    else:
        zoom = None

import numpy as np
def mLogScale(m, max):
    return int(np.e**((m/128.0)*np.log(max)) - 1)


def video_out(a):
    try:
        if zoom is None:
            a[:] = p.draw()
        else:
            a[:] = p.zoom(zoom)
    except Exception,err:
        print err
        print "Whatever."
    

def audio_out(a):
    try:
        a[:] = p.next(len(a))
    except Exception,err:
        print err
        print "Whatever."

def mouse_in(type, px, py, button):
    # mouse_in(type, px, py, button):
    pos = [int(px*p.origw), int(py*p.origh)]
    nearest = g.nearest(*pos)
    if type=='mouse-move':
        p._selection = [nearest]
    elif type=='mouse-button-press':
        p.trigger(nearest)
        p._selection = []

current_number = 0
def tune():
    global current_number
    p.select_by_nedges(current_number + 1, p._target)
    current_number = (current_number + 1) % 19
    print 'selected', current_number

def midi_in(*a):
    print a
    if a[1] == 20:
        #p._target = mLogScale(a[2], 75)
        p._target = mLogScale(a[2], 250)
    elif a[1] == 21:
        p._speed = mLogScale(a[2], 200)

    if a[0] == 153: # down
        if a[1] == 61:
            inhibit()
        elif a[1] == 69:
            saturate()

        elif a[1] == 65:
            p.bidirectionaltoggle()
        elif a[1] == 63:
            p.burntoggle()
        elif a[1] == 60:
            p.flip()

        elif a[1] == 58:
            toggleZoom()

        elif a[1] == 48:
            p.trigger_selection()

        elif a[1] == 49:
            p.set_sound_version(0)
        elif a[1] == 51:
            p.set_sound_version(1)
        elif a[1] == 68:
            p.set_sound_version(2)

        elif a[1] == 54:
            tune()

        elif a[1] == 57:
            p.select_by_coords(CENTER)
        elif a[1] == 55:
            p.select_by_coords(CORNERS)    

# -- listen for MIDI--

import pygame.midi as midi
import time

device = "padKONTROL MIDI 2"

midi.init()
nmidi = midi.get_count()
for mid in range(nmidi):
    info = midi.get_device_info(mid)
    if device in info[1] and info[2]:
        print mid, info
        break

inp = midi.Input(mid)
def events():
    while True:
        if inp.poll():
            for data,ts in inp.read(1):
                yield data
        else:
            time.sleep(1/100.0)

def midi_loop():
    for ev in events():
        midi_in(*ev)
import threading
t = threading.Thread(target=midi_loop)
t.start()

# launch numm sketch
import numm
h,w = p.draw().shape[:2]
nummOut = numm.Run(width=w,height=h,midiname="padKONTROL MIDI 2",fps=5, **globals())
nummOut.run()
