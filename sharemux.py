import os, pexpect

import time

from multiprocessing import Process, Manager

from flask import Flask, send_from_directory

tmux_proc = pexpect.spawn("/usr/bin/tmux", args=["a", "-t", "test"], maxread=10000, dimensions=(38,160))

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
        stack.append(os.read(tmux_proc.fileno(), 10000))

def start_app(app):
    app.run(host='0.0.0.0', port=5893, processes=20)

if __name__ == "__main__":

    app.stack = stack
    Process(target=start_app, args=(app,)).start()
    
    stack_pusher(stack)
