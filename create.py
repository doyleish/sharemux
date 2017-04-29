import os, pty, subprocess,time
from flask import Flask, send_from_directory
from multiprocessing import Process, Manager

child, fd = pty.fork()

if child==0:
    p = subprocess.Popen(["/usr/bin/tmux", "a", "-t", "test"], stdout=fd, stderr=fd, bufsize=10000)
    p.wait()
    exit(1)

mgr = Manager()
stack = mgr.list([])
app = Flask(__name__, static_url_path='/static')

@app.route('/xterm/<path:path>')
def serve_xterm(path):
    return send_from_directory('static/xterm', path)


@app.route('/jquery/<path:path>')
def serve_jquery(path):
    return send_from_directory('static/jquery', path)


@app.route('/')
def serve_index():
    return app.send_static_file('index.html')


@app.route('/snapshot/<inc>')
def serve_snapshot(inc):
    inc = int(inc)
    while len(stack)<=inc:
        time.sleep(0.05)
    return stack[inc]


def stack_pusher(stack):
    while(True):
        stack.append(os.read(fd, 10000))


if __name__ == "__main__":
    p = Process(target=stack_pusher, args=(stack,))
    p.start()
    app.run(host='0.0.0.0', port=5893, processes=20)
    p.join()
