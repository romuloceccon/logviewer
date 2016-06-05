#! /bin/bash

(( !$# )) && 1>&2 echo No arguments supplied! && exit 1

DBNAME=test.db

DBINPUT=$(mktemp --suffix=.sql)
#trap "exit 1" ERR SIGINT
#trap "rm -f $DBINPUT" 0

echo "Converting input file..." 1>&2
echo "PRAGMA foreign_keys = OFF;" >> $DBINPUT
echo "CREATE TABLE events (id INTEGER PRIMARY KEY, facility INTEGER,
  priority INTEGER, from_host TEXT, device_reported_time TEXT, received_at TEXT,
  info_unit_id INTEGER, syslog_tag TEXT, program_name TEXT, program_pid TEXT,
  message TEXT);" >> $DBINPUT
echo "BEGIN;" >> $DBINPUT
gzip -d -c $1 | sed -e 's/\\"/"/g' -e "s/\\\\'/''/g" -e 's/\([^\]\)\\n/\1\n/g' | python -c '
import sys
while True:
  line = sys.stdin.readline()
  if not line:
    break
  if len(line) < 1000:
    sys.stdout.write(line)
' >> $DBINPUT
echo 'COMMIT;' >> $DBINPUT

echo "Importing into sqlite3 database..." 1>&2
rm -f $DBNAME
sqlite3 $DBNAME < $DBINPUT

echo "Converting schema..." 1>&2

echo 'CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_num INTEGER,
  level_num INTEGER,
  host TEXT,
  datetime TEXT,
  program TEXT,
  pid TEXT,
  message TEXT);' | sqlite3 $DBNAME

echo 'INSERT INTO logs (facility_num, level_num, host, datetime, program, pid,
  message) SELECT facility, priority, from_host, device_reported_time,
  program_name, program_pid, message FROM events ORDER BY id;' | sqlite3 $DBNAME

echo 'DROP TABLE events;' | sqlite3 $DBNAME

echo "Done!" 1>&2
