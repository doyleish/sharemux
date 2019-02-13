import base64
import click
import json
import logging
import os
import pexpect
import socket
import time

from flask import Flask, Response, send_from_directory, request
from multiprocessing import Process, Manager, Queue  # Threading


# Share a stream and some state accross flask child Process
mgr = Manager()
state = mgr.dict()
master = mgr.list([])
STREAM_STACK_MAX = 256
streams = [Queue() for x in range(0, STREAM_STACK_MAX)]

app = Flask(__name__, static_url_path='/static')


# JS Libs
# ==================
@app.route('/xterm/<path:path>')
def serve_xterm(path):
    return send_from_directory('static/xterm', path)


@app.route('/jquery/<path:path>')
def serve_jquery(path):
    return send_from_directory('static/jquery', path)


# Terminal page
# ==================
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')


# Pty stream
# ==================
@app.route('/snapshotstream/<cid>')
def snapshotstream(cid):
    cid = int(cid)

    def gen():
        inc = 0
        try:
            while True:
                data = streams[cid].get()
                if data == "EOF":
                    print("  Terminating consumer {}'s stream...".format(cid))
                    yield "data: "
                    yield "EOF"
                    yield "\n\n"
                    break
                yield "data: "
                yield data
                yield "\n\n"
                inc += 1
        except KeyboardInterrupt:
            print("  Terminating consumer {}'s stream...".format(cid))
            yield "data: "
            yield "EOF"
            yield "\n\n"
    return Response(gen(), mimetype="text/event-stream")


# Pty stream
# ==================
@app.route('/register/<uid>')
def register(uid):
    consumer_id = state['num_consumers']
    if consumer_id >= STREAM_STACK_MAX:
        return json.dumps({
                   'session': 'STACK MAX EXCEEDED',
                   'rows': state['rows'],
                   'columns': state['columns']
               })
    for item in master:
        streams[consumer_id].put(item)
    state['num_consumers'] += 1
    print("  [{}] registered as consumer {} at {}".format(
                                                     request.remote_addr,
                                                     consumer_id,
                                                     time.strftime("%H:%M:%S")
                                                 ))
    return json.dumps({
               'session': state['session'],
               'rows': state['rows'],
               'columns': state['columns'],
               'consumer_id': consumer_id
           })


def stream_pusher(tmux_proc):
    try:
        while(True):
            data = base64.b64encode(os.read(tmux_proc.fileno(), 32768))
            master.append(data)
            for s in streams[0:state['num_consumers']]:
                s.put(data)
    except KeyboardInterrupt:
        print("  Cleaning up pty...")
        return
    except OSError:
        print("  Encountered read error. tmux proc likely ended")
        for s in streams[0:state['num_consumers']]:
            s.put("EOF")


def start_flask_app(app, port):
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, threaded=False, processes=30)


@click.command()
@click.argument('session', nargs=1)
@click.option('-r', '--rows', default=38)
@click.option('-c', '--columns', default=160)
@click.option('-p', '--port', default=5908)
def cli_websrv_start(session, rows, columns, port):
    print('[[-- SHAREMUX --]]')

    # Args
    # ====
    state['session'] = session
    state['rows'] = rows
    state['columns'] = columns
    state['num_consumers'] = 0

    # Setup
    # ======
    ## Find where tmux lives
    tmux_path=""
    for path in os.environ['PATH'].split(os.pathsep):
        potential_path = os.path.join(path,'tmux')
        if os.path.exists(potential_path):
            tmux_path = potential_path
            break

    ## Bail if tmux not available
    if not tmux_path:
        print('Looks like you don\'t have tmux installed.')
        print('Please install tmux and be sure it is in your PATH')
        exit(1)

    print('^C to Stop')
    print('--help for options')

    # Child Processes
    # ===============

    # Child proc #1
    # spawns pty. 32k read buffer should be optimal
    tmux_proc = pexpect.spawn(tmux_path,
                              args=["a", "-t", session],
                              maxread=32768,
                              dimensions=(rows, columns))

    # Child proc #2
    # spawn stream pusher.  tails pty into queues
    Process(target=stream_pusher, args=(tmux_proc, )).start()
    print('http://{}:{}'.format(socket.gethostname(), port))

    # Main proc
    # spawn flask app to serve queues via api endpoints
    start_flask_app(app, port)

    # Join up and die
    print('Closing...')
