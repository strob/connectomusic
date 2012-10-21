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

A = {"target": 12, #5
     "speed": 25,
     "mouse": [CENTER],
     "burn": True,
     "bidirectional": True,
     "sounds": SOUNDS[2]}

B = {"target": 12, #5
     "speed": 25,
     "mouse": CORNERS,
     "burn": True,
     "bidirectional": True,
     "sounds": SOUNDS[2]}

C = {"target": 9999,
     "speed": 7,
     "sounds": NOT_SECOND_ORDER,
     "seizure": True,
     "flipped": False}

D = {"target": 9999,
     "speed": 7,
     "sounds": NOT_SECOND_ORDER,
     "seizure": True,
     "flipped": True}

if __name__=='__main__':
    render(A, "vinyl/A")
    render(B, "vinyl/B")
    # C["files"] = [X+'.npy' for X in leftovers()]
    render(C, "vinyl/C")
    # D["files"] = [X+'.npy' for X in leftovers()]
    render(D, "vinyl/D")
