# button abstraction
def button(name, action):
    but = QtGui.QPushButton(name)
    but.clicked.connect(action)
    snipdom.addWidget(but)