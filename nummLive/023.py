soundList = ["first order", "second order", "neu"]
soundBox = QtGui.QComboBox()
soundBox.addItems(soundList)
soundBox.setCurrentIndex(0)
def onSoundChange(idx):
    p.set_sound_version(idx)
soundBox.currentIndexChanged.connect(onSoundChange)
snipdom.addWidget(soundBox)