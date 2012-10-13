import pygame.midi as midi

device = "padKONTROL MIDI 2"

midi.init()
nmidi = midi.get_count()
for mid in range(nmidi):
    info = midi.get_device_info(mid)
    if device in info[1] and info[2]:
        print mid, info
        break

inp = midi.Input(mid)
def events():
    while True:
        for data,ts in inp.read(1):
            yield data

if __name__=='__main__':
    for ev in events():
        print ev
