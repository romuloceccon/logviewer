import sqlite3
import datetime

import sql_driver

class Sqlite3Driver(sql_driver.SqlDriver):
    def __init__(self, filename, **kwargs):
        sql_driver.SqlDriver.__init__(self, **kwargs)
        self._filename = filename

    def start_connection(self):
        self._connection = sqlite3.connect(self._filename)

    def stop_connection(self):
        self._connection.close()

    def select(self, cmd):
        return self._connection.execute(cmd)

    def fetch_record(self, query):
        rec = query.fetchone()
        if rec is None:
            return
        dt = datetime.datetime.strptime(rec[4], '%Y-%m-%d %H:%M:%S')
        return { 'id': rec[0], 'facility_num': str(rec[1]),
            'level_num': str(rec[2]), 'host': rec[3], 'datetime': dt,
            'program': rec[5], 'pid': rec[6], 'message': rec[7] }
