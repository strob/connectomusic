import base64
import json

SETS = ['s0', 's1', 's2']

for key in SETS:
    mapping = json.load(open("%s.json" % (key)))
    out = {}
    for num, aiffs in mapping.items():
        out[num] = [base64.b64encode(open("%s.mp3" % (aiff)).read()) for aiff in aiffs]

    json.dump(out, open("%s-audio.json" % (key), "w"))
