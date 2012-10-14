# render from a params.json file

import player
import graph

import sys
import json
import cv2
import os
import shutil
import subprocess

FPS = 30
R = 44100
WINDOW = R/FPS
MAX_DUR = 5*60                  # seconds

params = json.load(open(sys.argv[1]))
outdir = sys.argv[2]
os.makedirs(outdir)

g = graph.connected_directed_graph(version=params["sounds"])
p = player.Player(g, speed=params["speed"], target_nnodes=params["target"], flipped=params["flipped"])

shutil.copy(sys.argv[1], os.path.join(outdir, 'orig.params.json'))

os.chdir(outdir)

p.toggle_recording()

# trigger
for pt in params['mouse']:
    node = g.nearest(pt[0], pt[1])
    p.trigger(node)
for num in params['nummap']:
    for node in g.grpnodes.get(num,[]):
        p.trigger(node)
    

cur_t = 0
rec_video = None
while cur_t < MAX_DUR:
    p.next(buffer_size=WINDOW)
 
    im = p.draw()

    # RESIZE
    im = cv2.resize(im, (800, 800))

    if rec_video is None:
        rec_video = cv2.VideoWriter()
        rec_video.open('out.avi', cv2.cv.CV_FOURCC(*'DIVX'), 30, (im.shape[1], im.shape[0]), True)

    rec_video.write(im)

    cur_t += WINDOW / float(R)

    if len(p._state_edges) + len(p._state_nodes) == 0:
        print 'early finish', cur_t
        break

p.toggle_recording()

# join a/v & delete v
cmd = ['ffmpeg', '-i', 'out.avi', '-i', 'out.wav', '-acodec', 'copy', '-vcodec', 'copy', 'merge.avi']
p = subprocess.Popen(cmd)
p.wait()

os.unlink('out.avi')
