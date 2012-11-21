def loadCallbacks():
    for i, (name, sig) in enumerate(numm.async.callbacks):
        path = os.path.join(outdir, "%s.py" % (name))
        code = open(path).read()
        nummWidgets[name]["code"].setPlainText(code)
        nummTabs.setCurrentIndex(i)
        nummWidgets[name]["button"].click()
