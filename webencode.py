import subprocess

def enc(src):
    subprocess.Popen(['ffmpeg', '-y', '-i', src, '-ab', '128K', '-acodec', 'libvorbis', src+'.ogg']).wait()
    subprocess.Popen(['ffmpeg', '-y', '-i', src, '-ab', '128K', src+'.mp3']).wait()

if __name__=='__main__':
    import sys
    for afile in sys.argv[1:]:
        enc(afile)
