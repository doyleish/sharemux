import os, pexpect, time, socket    # pty io + control
from multiprocessing import Process, Manager  # Threading
from flask import Flask, Response, send_from_directory   # www Hosting
import click, logging, json, base64   #Misc


# Share a stream and some state accross child Process
mgr = Manager()
state = mgr.dict()
stream = mgr.list([])

# app def
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

@app.route('/snapshotstream')
def serve_snapshot():
    def gen():
        inc = 0
        while True:
            while inc>=len(stream):
                time.sleep(0.03)
            yield "data: "
            yield base64.b64encode(stream[inc])
            yield "\n\n"
            inc+=1
    return Response(gen(), mimetype="text/event-stream")

@app.route('/info')
def info():
    return json.dumps({
              'session': state['session'],
              'rows': state['rows'],
              'columns': state['columns']
           })

def stream_pusher(tmux_proc):
    while(True):
        stream.append(bytes(os.read(tmux_proc.fileno(), 32768)))

def start_app(app, port):
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, processes=20)

@click.command()
@click.argument('session', nargs=1)
@click.option('-r', '--rows', default=38)
@click.option('-c', '--columns', default=160)
@click.option('-p', '--port', default=5908)
def cli(session, rows, columns, port):
    state['session'] = session
    state['rows'] = rows
    state['columns'] = columns

    # Child proc #1 spawns pty. 6k read buffer should be optimal
    tmux_proc = pexpect.spawn("/usr/bin/tmux", args=["a", "-t", session], maxread=32768, dimensions=(rows, columns))
    
    # Process(target=start_app, args=(app,)).start() 
    Process(target=stream_pusher, args=(tmux_proc, )).start()
    print('http://{}:{}'.format(socket.gethostname(), port))

    # stream_pusher(tmux_proc)
    start_app(app, port) 
