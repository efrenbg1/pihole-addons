import os
import threading
import time
import db

lock = threading.Lock()

create = [
    "iptables -F addons",
    "iptables -D INPUT -p udp -m udp --dport 53 -j addons",
    "iptables -X addons",
    "iptables -N addons"
]

rule = "iptables -A addons --src {} -j ACCEPT"

finish = [
    "iptables -A addons -j DROP",
    "iptables -I INPUT -m udp -p udp --dport 53 -j addons"
]


def allow():
    with lock:
        ips = ["127.0.0.1"]
        q = db.query("SELECT ip FROM clients")
        for r in q:
            if r[0] not in ips:
                ips.append(r[0])
        print(ips)
        for command in create:
            os.system(command)
        for ip in ips:
            os.system(rule.format(ip))
        for command in finish:
            os.system(command)
