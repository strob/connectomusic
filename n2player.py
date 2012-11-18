#!/usr/bin/env python2

from PyQt4 import QtGui
import sys
from numm import qui

import offline

params = {"target": 10,
          "speed": 20,
          "sounds": "final_material_tt_bearbeit_2nd_order_NEUER_(450)"}
p = offline.init(params)
scale = 0.5
base = p._get_base_frame(scale=scale)

app = QtGui.QApplication(sys.argv)
app.setApplicationName('NUMMMMMM')

NW = qui.NummWindow(width=base.shape[1],
                    height=base.shape[0],
                    midiname="padKONTROL MIDI 2",
                    ctx={"p":p, "scale":scale})
NW.setup.setPlainText('import pygame')
NW.loop.setPlainText('''
v[:] = p.draw()
a[:] = p.next(len(a))
for ev in e:
    print ev
    if ev.type == pygame.MOUSEBUTTONDOWN:
        pt = [x/scale for x in ev.pos]
        node = p.graph.nearest(*pt)
        print node
        p.trigger(node)
''')
NW.show()

if __name__=='__main__':
    sys.exit(app.exec_())
