# render from a params.json file

import player
import graph

import sys
import json
import cv2
import os
import shutil
import subprocess

import rerender

FPS = 30
R = 44100
WINDOW = R/FPS
MAX_DUR = 5*60                  # seconds

def render(params, outdir):
    curdir = os.getcwd()

    if os.path.exists(outdir):
        print 'skipping', outdir
        return

    os.makedirs(outdir)

    g = graph.connected_directed_graph(version=params["sounds"], bd=params.get("bidirectional", False), files=params.get("files", None))
    p = player.Player(g, speed=params["speed"], target_nnodes=params["target"], flipped=params.get("flipped", False), burnbridges=params.get("burn", False))

    # shutil.copy(sys.argv[1], os.path.join(outdir, 'orig.params.json'))

    # os.chdir(outdir)

    p.toggle_recording()

    # trigger
    for pt in params.get('mouse', []):
        node = g.nearest(pt[0], pt[1])
        p.trigger(node)
        print 'trigger', node.pt, pt, node.payload
    for num in params.get('nummap',[]):
        for node in g.grpnodes.get(num,[]):
            p.trigger(node)
    if params.get('seizure', False):
        for node in g.get_all_nodes():
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
            rec_video.open(os.path.join(outdir, 'out.avi'), cv2.cv.CV_FOURCC(*'DIVX'), 30, (im.shape[1], im.shape[0]), True)

        rec_video.write(im)

        cur_t += WINDOW / float(R)

        if len(p._state_edges) + len(p._state_nodes) == 0:
            print 'early finish', cur_t
            break

    os.chdir(outdir)
    p.toggle_recording()

    # Actually, replace audio. Whatever.
    print 're-render audio'
    rerender.render('out.samples.txt')

    # join a/v & delete v
    cmd = ['ffmpeg', '-i', 'out.avi', '-i', 'noclip.wav', '-acodec', 'copy', '-vcodec', 'copy', 'merge.avi']
    p = subprocess.Popen(cmd)
    p.wait()

    os.unlink('out.avi')

    os.chdir(curdir)

if __name__=='__main__':
    params = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]

    render(params, outdir)
