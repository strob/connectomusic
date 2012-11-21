# mouse_in(type, px, py, button):
pos = [int(px*p.origw), int(py*p.origh)]
nearest = g.nearest(*pos)
if type=='mouse-move':
    p._selection = [nearest]
elif type=='mouse-button-press':
    p.trigger(nearest)
    p._selection = []