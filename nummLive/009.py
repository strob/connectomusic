def trigger():
    p.trigger_selection()

tbutton = QtGui.QButton("trigger")
tbutton.clicked.connect(trigger)
snipdom.addWidget(tbutton)