import os, pty, subprocess, time

args = "/bin/bash"

child, fd = pty.fork()

if child==0:
    p = subprocess.Popen(["/usr/bin/tmux", "a", "-t", "test"], stdout=fd, stderr=fd)
else:
    time.sleep(2)
    data = os.read(fd, 250000)
    print(data.decode('ascii'))
    time.sleep(1)
