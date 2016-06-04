import sqlite3
import datetime

import sql_driver
import screen_buffer

class Sqlite3Driver(sql_driver.SqlDriver):
    class Factory(object):
        def __init__(self, filename):
            self._filename = filename
            self._level = None
            self._max_level = len(screen_buffer.ScreenBuffer.Line.LEVELS) - 1
            self._facility = None
            self._host = None
            self._program = None

        # Level: None means maximum messages (i.e., level_num=6)
        @property
        def level(self):
            if self._level is None:
                return self._max_level
            return self._level

        @level.setter
        def level(self, val):
            if val == self._max_level:
                self._level = None
            else:
                self._level = val

        # Facility: None means all facilities
        @property
        def facility(self):
            return self._facility

        @facility.setter
        def facility(self, val):
            self._facility = val

        @property
        def host(self):
            if self._host is None:
                return ''
            return self._host

        @host.setter
        def host(self, val):
            self._host = val

        @property
        def program(self):
            if self._program is None:
                return ''
            return self._program

        @program.setter
        def program(self, val):
            self._program = val

        def create_driver(self):
            return Sqlite3Driver(self._filename, level=self._level,
                facility=self._facility, host=self._host, program=self._program)

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
