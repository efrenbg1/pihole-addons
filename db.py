import sqlite3
import random
import string
from threading import Lock


def rand(size):
    return ''.join(random.SystemRandom().choice(
        string.ascii_letters + string.digits) for _ in range(size))


db = sqlite3.connect('db', check_same_thread=False)
ldb = Lock()
c = db.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS clients (key text NOT NULL PRIMARY KEY, ip text NOT NULL, count INTEGER NOT NULL, last real NOT NULL, name text)''')
c.execute(
    '''CREATE TABLE IF NOT EXISTS temp (key text NOT NULL PRIMARY KEY, value text NOT NULL)''')
db.commit()


def query(query, *param):
    with ldb:
        c = db.cursor()
        result = c.execute(query, param)
        db.commit()
        return result.fetchall()


def get_session():
    q = query("SELECT value FROM temp WHERE key='session'")
    if len(q) == 0:
        session = rand(100)
        query("INSERT INTO temp VALUES ('session', ?)", session)
        return session
    return q[0][0]


def set_session(value):
    query("UPDATE temp SET value=? WHERE key='session'", value)


def get_admin():
    q = query("SELECT value FROM temp WHERE key='admin'")
    if len(q) == 0:
        pw = rand(15)
        query("INSERT INTO temp VALUES ('admin', ?)", pw)
        return pw
    return q[0][0]


def set_admin(value):
    query("UPDATE temp SET value=? WHERE key='admin'", value)
