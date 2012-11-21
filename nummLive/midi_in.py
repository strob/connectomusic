print a
if a[1] == 20:
    p._target = mLogScale(a[2], 75)
elif a[1] == 21:
    p._speed = mLogScale(a[2], 200)

if a[0] == 153: # down
    if a[1] == 61:
        inhibit()
    elif a[1] == 69:
        saturate()

    elif a[1] == 65:
        p.bidirectionaltoggle()
    elif a[1] == 63:
        p.burntoggle()
    elif a[1] == 60:
        p.flip()

    elif a[1] == 58:
        toggleZoom()

    elif a[1] == 48:
        p.trigger_selection()

    elif a[1] == 49:
        p.set_sound_version(0)
    elif a[1] == 51:
        p.set_sound_version(1)
    elif a[1] == 68:
        p.set_sound_version(2)

    elif a[1] == 57:
        p.select_by_coords(CENTER)
    elif a[1] == 55:
        p.select_by_coords(CORNERS)