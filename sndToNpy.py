import numm
import numpy as np
import sys

for f in sys.argv[1:]:
    snd = numm.sound2np(f)
    np.save(f+'.npy', snd[:,0])
