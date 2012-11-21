import os
outdir = '/home/rmo/src/connectomusic/nummLive'
if not os.path.exists(outdir):
    os.makedirs(outdir)
def save():
    for i, code in enumerate(runList):
        open(os.path.join(outdir,"%03d.py" % (i)), 'w').write(code)
    for name, sig in numm.async.callbacks:
        open(os.path.join(outdir, "%s.py" % (name)), 'w').write(str(nummWidgets[name]["code"].toPlainText()))

saveButton = QtGui.QPushButton('save')
saveButton.clicked.connect(save)
snipdom.addWidget(saveButton)