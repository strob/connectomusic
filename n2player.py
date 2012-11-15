#!/usr/bin/env python2

from PyQt4 import QtGui
import sys
from numm import qui

import offline

params = {"target": 10,
          "speed": 20,
          "sounds": "final_material_tt_bearbeit_NEU_gekurzt"}
p = offline.init(params)
base = p._get_base_frame(scale=1)

app = QtGui.QApplication(sys.argv)
app.setApplicationName('NUMMMMMM')

NW = qui.NummWindow(width=base.shape[1],
                    height=base.shape[0],
                    midiname="padKONTROL MIDI 2",
                    ctx={"p":p})
NW.show()

if __name__=='__main__':
    sys.exit(app.exec_())
