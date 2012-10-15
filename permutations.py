from offline import render

SOUNDS = ['final_material_tt_bearbeit_(140)',
          'final_material_tt_bearbeit_NEU_gekurzt_(171)',
          'final_material_tt_bearbeit_2nd_order_NEUER_(450)',
          '*']
CENTER = [602, 833]
CORNERS = [[48, 1234], [1194, 1239], [1196, 47], [41, 73]]

baseparams = {
    "nummap": [],
    "speed": 50,
    "target": 25,
    "actions": [],
    "flipped": False,
    "mouse": []
}

def _outdir(msg, params):
    params["nm"] = '_'.join([str(x) for x in params["nummap"]])
    params["ms"] = ""
    params["msg"] = msg
    params["extra"] = ""
    if params.get("burn", False):
        params["extra"] += "burn-"
    if params.get("bidirectional", False):
        params["extra"] += "bi-"
    for pt in params["mouse"]:
        params["ms"] += "%dx%d-" % (pt[0], pt[1])
    return "vid/%(msg)s-%(sounds)s-s%(speed)d-f%(flipped)d-t%(target)d-nm%(nm)s-ms%(ms)s%(extra)s" % (params)

for idx, sound in enumerate(reversed(SOUNDS)):

    # Corners simultaneous
    params = baseparams.copy()

    params["sounds"] = sound

    params["mouse"] = CORNERS
    for speed in [50, 20]:
        params["speed"] = speed

        render(params, _outdir("simulcorners", params))

    # sequential
    params["speed"] = 150
    for corner in CORNERS:
        params["mouse"] = [corner]

        render(params, _outdir("seqcorners", params))

    # center
    params["mouse"] = [CENTER]
    params["target"] = 2
    params["speed"] = 20

    render(params, _outdir("slowlowcenter", params))

    params["target"] = 1.5
    params["speed"] = 8
    render(params, _outdir("slowerlowercenter", params))

    params["target"] = 50
    params["speed"] = 6
    render(params, _outdir("slowhightargetcenter", params))

    params["target"] = 0.5
    params["speed"] = 4
    render(params, _outdir("slowestinhibitcenter", params))

    params["bidirectional"] = True
    params["burn"] = True
    params["speed"] = 8
    render(params, _outdir("slowburningcenter", params))

    params["speed"] = 20
    render(params, _outdir("burningcenter", params))

    params["mouse"] = CORNERS
    params["speed"] = 30
    params["target"] = 10
    render(params, _outdir("burningcorners", params))

    params["bidirectional"] = False
    params["burn"] = False

    params["target"] = 50
    params["speed"] = 200
    render(params, _outdir("fastcenter", params))

    # EVERYTHING
    params["mouse"] = []
    params["nummap"] = range(20)

    for speed in [20,200]:
        params["speed"] = speed
        for flipped in [True, False]:
            params["flipped"] = flipped
            render(params, _outdir("everything", params))


    # mid-letter
    params["nummap"] = [7]
    params["speed"] = 100
    for flipped in [True, False]:
        params["flipped"] = flipped
        render(params, _outdir("midletter", params))

    # # highest point
    # params["nummap"] = [18,19]
    # params["flipped"] = False
    # render(params, _outdir("highest", params))

    # lowest point
    params["nummap"] = [1,2]
    params["flipped"] = True
    render(params, _outdir("lowest", params))
    
    params["speed"] = 10
    render(params, _outdir("lowestslow", params))
