# launch numm sketch
h,w = p.draw().shape[:2]
nummOut = numm.Run(width=w,height=h,midiname="padKONTROL MIDI 2",fps=15)
threading.Thread(target=nummOut.run).start()
