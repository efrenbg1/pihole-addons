from flask import Flask, render_template, send_from_directory, request, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import platform
import iptables
import time
import db

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address
)

print("Admin password:", db.get_admin())
iptables.allow()


@app.route('/')
@limiter.limit("10 per minute")
def index():
    if db.get_session() != request.cookies.get('session'):
        return redirect('/login')

    clients = db.query(
        "SELECT name, key, ip, count, CAST(((?-last)/60) AS INTEGER) FROM clients", time.time())

    return render_template('index.html', node=platform.node(), clients=clients, url=request.base_url)


@app.route('/refresh')
@limiter.limit("10 per hour")
def refresh():
    key = request.args.get('key')
    ip = request.args.get('ip')
    if ip == None:
        ip = request.remote_addr

    q = db.query("SELECT key, ip FROM clients WHERE key=?", key)
    if len(q):
        db.query("UPDATE clients SET count=count+1, last=? WHERE key=?",
                 time.time(), key)

        if q[0][1] != ip:
            db.query("UPDATE clients SET ip=? WHERE key=?", ip, key)
            iptables.allow()

    return "New IP address is {}".format(ip)


@app.route('/name', methods=['POST'])
@limiter.limit("10 per minute")
def name():
    if db.get_session() != request.cookies.get('session'):
        return redirect('/login')

    db.query("UPDATE clients SET name=? WHERE key=?",
             request.form.get('name'), request.args.get('key'))

    return redirect('/')


@app.route('/add', methods=['POST'])
@limiter.limit("10 per minute")
def add():
    if db.get_session() != request.cookies.get('session'):
        return redirect('/login')

    q = [0]
    while len(q):
        key = db.rand(30)
        q = db.query("SELECT key FROM clients WHERE key=?", key)

    db.query("INSERT INTO clients VALUES (?, ?, ?, ?, '')",
             db.rand(30), request.remote_addr, 0, time.time())

    iptables.allow()

    return redirect('/')


@app.route('/delete', methods=['POST'])
@limiter.limit("10 per minute")
def delete():
    if db.get_session() != request.cookies.get('session'):
        return redirect('/login')

    db.query("DELETE FROM clients WHERE key=?", request.args.get('key'))

    iptables.allow()

    return redirect('/')


@app.route('/iptables', methods=['POST'])
@limiter.limit("1 per minute")
def iptables_refresh():
    if db.get_session() != request.cookies.get('session'):
        return redirect('/login')

    iptables.allow()

    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("6 per minute")
def login():
    if request.method == 'POST':
        if db.get_admin() != request.form.get('password'):
            return redirect('/login')

        session = db.rand(30)
        print(session)
        db.set_session(session)
        resp = make_response(redirect('/'))
        resp.set_cookie('session', session)
        return resp
    else:
        return render_template('login.html', node=platform.node())


@app.route('/logout', methods=['POST'])
@limiter.limit("6 per minute")
def logout():
    if db.get_session() != request.cookies.get('session'):
        return redirect('/login')

    db.set_session(db.rand(100))

    return redirect('/login')


@app.route('/<path:path>')
def content(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5004)
