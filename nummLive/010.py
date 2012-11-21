def trigger():
    p.trigger_selection()

tbutton = QtGui.QPushButton("trigger")
tbutton.clicked.connect(trigger)
snipdom.addWidget(tbutton)