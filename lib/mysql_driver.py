import mysql.connector

import sql_driver
import screen_buffer

class MySQLDriver(sql_driver.SqlDriver):
    class Factory(object):
        def __init__(self, **mysql_conf):
            self._mysql_conf = mysql_conf
            if 'port' in self._mysql_conf:
                self._mysql_conf['port'] = int(self._mysql_conf['port'])

        def create_driver(self, state):
            return MySQLDriver(self._mysql_conf, level=state.level,
                facility=state.facility, host=state.host, program=state.program)

    def __init__(self, mysql_conf, **kwargs):
        sql_driver.SqlDriver.__init__(self, **kwargs)
        self._mysql_conf = mysql_conf

    def start_connection(self):
        self._connection = mysql.connector.connect(**(self._mysql_conf))

    def stop_connection(self):
        self._connection.close()

    def select(self, cmd):
        result = self._connection.cursor()
        result.execute(cmd)
        return result

    def fetch_record(self, query):
        rec = query.fetchone()
        if rec is None:
            query.close()
            self._connection.rollback()
            return
        return { 'id': rec[0], 'facility_num': str(rec[1]),
            'level_num': str(rec[2]), 'host': rec[3], 'datetime': rec[4],
            'program': rec[5], 'pid': rec[6], 'message': rec[7] }
