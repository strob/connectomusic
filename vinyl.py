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

NOT_SECOND_ORDER = 'final_material_tt_bearbeit_[N\(]*'
SECOND_AND_NEU = 'final_material_tt_bearbeit_[2N]*'

# 2nd order sounds
# bi-directional edges
# don't repeat sounds

# start in center

A = {"target": 3, #5
     "speed": 20,
     "mouse": [CENTER],
     "burn": True,
     "bidirectional": True,
     "sounds": SOUNDS[2]}

# start in at corners
# half speed of A

B = {"target": 4,
     "speed": 10,
     "mouse": CORNERS,
     "burn": True,
     "bidirectional": True,
     "sounds": SECOND_AND_NEU} #SOUNDS[2]}

# non-2nd-order sounds
# directed edges
# allow repeating sounds
# start with every node activated

# move from higher-degree nodes to lower
C = {"target": 9999,
     "speed": 7,
     "sounds": NOT_SECOND_ORDER,
     "seizure": True,
     "flipped": False}

# move from lower-degree nodes to higher
# enable loop-nodes

D = {"target": 9999,
     "speed": 7,
     "sounds": NOT_SECOND_ORDER,
     "seizure": True,
     "flipped": True}

if __name__=='__main__':
    render(A, "vinyl/A")
    render(B, "vinyl/B_And_Neu")
    # C["files"] = [X+'.npy' for X in leftovers()]
    # render(C, "vinyl/C")
    # # D["files"] = [X+'.npy' for X in leftovers()]
    # render(D, "vinyl/D")
