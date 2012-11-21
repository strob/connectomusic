def add_spin(name, fn, min, max):
    label = QtGui.QLabel(name)

    spinner= QtGui.QSpinBox()
    spinner.setMinimum(min)
    spinner.setMaximum(max)

    spinner.valueChanged.connect(fn)

    split = QtGui.QSplitter()
    split.addWidget(label)
    split.addWidget(spinner)

    snipdom.addWidget(split)
def spin(name, min, max):
    def fn(val):
        setattr(p, name, val)
    add_spin(name, fn, min, max)
