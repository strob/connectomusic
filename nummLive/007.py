# selections

CENTER = [[602, 833]]
CORNERS = [[48, 1234], [1194, 1239], [1196, 47], [41, 73]]

def buttonFunction(k, v):
    def onclick():
        p.select_by_coords(v)
    return onclick

for k,v in [('center', CENTER), ('corner', CORNERS)]:
    selButton = QtGui.QPushButton(k)
    selButton.clicked.connect(buttonFunction(k,v))
    snipdom.addWidget(selButton)
