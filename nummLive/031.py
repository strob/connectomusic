def selectNumber(idx):
    p.select_by_nedges(idx, p._target)
add_spin("select #", selectNumber, 1, 20)
