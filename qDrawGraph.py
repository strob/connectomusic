import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

from svgToGraph import Graph
import numm
graph = Graph('node_map.svg')

app = QtGui.QApplication(sys.argv)
app.setApplicationName('connectomusic')

scene = QtGui.QGraphicsScene()
view = QtGui.QGraphicsView(scene)

# left = QtGui.QPixmap('linke_seite.png')
# scene.addPixmap(left)
 
right = QtGui.QPixmap('right_aligned.png')
scene.addPixmap(right)

nodebrush = QtGui.QBrush(QtGui.QColor('yellow'));

for node in graph.right_nodes:
# for node in graph.left_nodes:
    x,y = node.get_center()
    r = node.get_radius()
    ellipse = QtGui.QGraphicsEllipseItem(x-r, y-r, 2*r, 2*r)
    ellipse.setBrush(nodebrush)
    scene.addItem(ellipse)

view.show()

if __name__=='__main__':
    app.exec_()
