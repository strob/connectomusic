from offline import render
import glob
from permutations import SOUNDS, CENTER, CORNERS, baseparams

def leftovers():
    all_sounds = set(glob.glob('snd/*/*.aiff'))
    samplefiles= glob.glob('vinyl/*/out.samples.txt')
    used_sounds = set()
    for samplefile in samplefiles:
        used_sounds.union([X.split('\t')[-1] for X in open(samplefile).read().strip().split('\n')])
    return all_sounds.difference(used_sounds)
        

A = {"target": 1.5,
     "speed": 30,
     "mouse": [CENTER],
     "burn": True,
     "bidirectional": True,
     "sounds": SOUNDS[2]}

B = {"target": 3,
     "speed": 5,
     "mouse": CORNERS,
     "burn": True,
     "bidirectional": True,
     "sounds": SOUNDS[2]}

C = {"target": 25,
     "speed": 5,
     "sounds": SOUNDS[3],
     "nummap": range(20),
     "flipped": False}

D = {"target": 25,
     "speed": 5,
     "sounds": SOUNDS[3],
     "nummap": range(20),
     "flipped": True}

if __name__=='__main__':
    render(A, "vinyl/A")
    render(B, "vinyl/B")
    C["files"] = [X+'.npy' for X in leftovers()]
    render(C, "vinyl/C")
    D["files"] = [X+'.npy' for X in leftovers()]
    render(D, "vinyl/D")
