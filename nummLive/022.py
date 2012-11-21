zoom = None
def toggleZoom():
    global zoom
    if zoom is None and len(p._selection) > 0:
        zoom = p._selection[0]
    else:
        zoom = None
button("toggle zoom", toggleZoom)