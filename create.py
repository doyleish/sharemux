import os, pty, subprocess, time
from ansi2html import Ansi2HTMLConverter

args = "/bin/bash"

child, fd = pty.fork()

if child==0:
    p = subprocess.Popen(["/usr/bin/tmux", "a", "-t", "test"], stdout=fd, stderr=fd)
else:
    time.sleep(2)
    a2h = Ansi2HTMLConverter()
    data = os.read(fd, 250000)
    print(data)
    time.sleep(1)
