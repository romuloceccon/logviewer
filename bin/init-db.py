#! /usr/bin/python

import sys
import datetime

sys.stdout.write('''BEGIN;
''')

sys.stdout.write('''CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  datetime TEXT,
  host TEXT,
  program TEXT,
  facility TEXT,
  level TEXT,
  message TEXT);
''')

now = datetime.datetime.now() - datetime.timedelta(hours=1)
inc = datetime.timedelta(seconds=13)

for i in range(200):
    dt = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
    now += inc
    sys.stdout.write('''INSERT INTO logs (datetime, host, program, facility,
  level, message) VALUES ('{}', 'oasis', 'test', 'user', 'notice', 'line {}/1
line {}/2');
'''.format(dt, i + 1, i + 1))

sys.stdout.write('''COMMIT;
''')
