import os  # pty io + control
import pexpect
import socket

from multiprocessing import Process, Manager, Queue  # Threading

from flask import Flask, Response, send_from_directory, request   # www Hosting

import click  # Misc
import logging
import json
import base64
import time


# Share a stream and some state accross child Process
mgr = Manager()
state = mgr.dict()
master = mgr.list([])
STREAM_STACK_MAX = 256
streams = [Queue() for x in range(0, STREAM_STACK_MAX)]

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


def start_app(app, port):
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, processes=30)


@click.command()
@click.argument('session', nargs=1)
@click.option('-r', '--rows', default=38)
@click.option('-c', '--columns', default=160)
@click.option('-p', '--port', default=5908)
def cli(session, rows, columns, port):
    state['session'] = session
    state['rows'] = rows
    state['columns'] = columns
    state['num_consumers'] = 0

    print('[[ SHAREMUX ]]')
    print('^C to Stop')
    print('--help for options')

    # Child proc #1 spawns pty. 6k read buffer should be optimal
    tmux_proc = pexpect.spawn("/usr/bin/tmux",
                              args=["a", "-t", session],
                              maxread=32768,
                              dimensions=(rows, columns))

    # Process(target=start_app, args=(app,)).start()
    Process(target=stream_pusher, args=(tmux_proc, )).start()
    print('http://{}:{}'.format(socket.gethostname(), port))

    # stream_pusher(tmux_proc)
    start_app(app, port)
    print('Closing...')
