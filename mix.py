import numm
import numpy as np

def mix(l, r):
    "Mix two stereo tracks"
    out = np.zeros((max(len(l), len(r)), 2), int)
    out[:len(l),0] = l[:,0]
    out[:len(l),1] = l[:,1]/2
    out[:len(r),0] += r[:,0]/2
    out[:len(r),1] += r[:,1]
    return (out / (out.max() / float(2**15-1))).astype(np.int16)

if __name__=='__main__':
    import sys
    res = mix(numm.sound2np(sys.argv[1]),
              numm.sound2np(sys.argv[2]))
    numm.np2sound(res, 'mixed.wav')
