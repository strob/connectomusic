# connectomusic: core init

libpath = '/home/rmo/src/connectomusic'
import sys
sys.path.append(libpath)
import os
os.chdir(libpath)

import graph
import player

g = graph.connected_directed_graph()
p = player.Player(g)