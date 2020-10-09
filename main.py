import re, time, queue, threading

import jack

cli = jack.Client('jack-ard')
con_q = queue.Queue()

class ConnectionThread(threading.Thread):
    def run(self):
        while True:
            f, t = con_q.get()
            print(f'{self}: connecting {f} to {t}')
            try:
                cli.connect(f, t)
            except jack.JackError as e:
                print(e)

ct = ConnectionThread()
ct.setDaemon(True)
ct.start()

class Rule(object):
    def __init__(self, from_re, to_re):
        self.from_re = from_re
        self.to_re = to_re

    def __repr__(self):
        return f'Rule {self.from_re} -> {self.to_re}'

    def __call__(self):
        from_set = cli.get_ports(self.from_re)
        to_set = cli.get_ports(self.to_re)
        for f in from_set:
            for t in to_set:
                con_q.put((f, t))

class RuleList(object):
    def __init__(self):
        self.rules = []

    def clear(self):
        del self.rules[:]

    def load_from_file(self, f):
        self.clear()
        for line in f:
            l, sep, r = line.partition('->')
            if (not sep) and line.strip():
                print('Ignoring line:', line)
                continue
            self.rules.append(Rule(l.strip(), r.strip()))

    def run(self):
        for r in self.rules:
            r()

    def ports_change(self, port, register):
        print('Connectivity change:', 'add' if register else 'remove', port)
        self.run()

rl = RuleList()
rl.load_from_file(open('rules'))

cli.set_port_registration_callback(rl.ports_change, False)
cli.activate()
print('Ports:', cli.get_ports())

rl.run()

while True:
    time.sleep(3600)
