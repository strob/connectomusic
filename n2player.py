#!/usr/bin/env python2

import sys

import numm
import offline

params = {"target": 10,
          "speed": 20,
          "sounds": "final_material_tt_bearbeit_2nd_order_NEUER_(450)"}
p = offline.init(params)
scale = 0.5
base = p._get_base_frame(scale=scale)

def video_out(v):
    v[:] = p.draw()
def audio_out(a):
    a[:] = p.next(len(a))
def mouse_in(type, px, py, button):
    if type == 'mouse-button-press':
        pt = (px*base.shape[1]/scale, py*base.shape[0]/scale)
        node = p.graph.nearest(*pt)
        print node
        p.trigger(node)

NW = numm.Run(
    video_out=video_out,
    audio_out=audio_out,
    mouse_in=mouse_in,
    width=base.shape[1],
    height=base.shape[0],
    midiname="padKONTROL MIDI 2").run()

if __name__=='__main__':
    sys.exit(app.exec_())
