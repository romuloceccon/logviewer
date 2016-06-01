#! /usr/bin/python

import sys
import datetime
import random

sys.stdout.write('''BEGIN;
''')

sys.stdout.write('''CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_num INTEGER,
  level_num INTEGER,
  host TEXT,
  datetime TEXT,
  program TEXT,
  pid TEXT,
  message TEXT);
''')

now = datetime.datetime.now() - datetime.timedelta(hours=1)
inc = datetime.timedelta(seconds=13)

for i in range(200):
    dt = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
    now += inc
    sys.stdout.write('''INSERT INTO logs (facility_num, level_num, host,
datetime, program, pid, message) VALUES ('{}', '{}', 'oasis', '{}', 'test', '100',
'line {}/1
line {}/2');
'''.format(random.randint(0, 23), random.randint(0, 7), dt, i + 1, i + 1))

sys.stdout.write('''COMMIT;
''')
