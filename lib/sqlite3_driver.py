import sqlite3
import datetime

class Sqlite3Driver(object):
    def __init__(self, filename, even_only=False):
        self._connection = sqlite3.connect(filename)
        self._even_only = even_only

    def get_records(self, start, desc, count):
        if desc:
            order, id_cond = 'DESC', 'id < ?'
        else:
            order, id_cond = 'ASC', 'id > ?'

        if start is None:
            conds, args = [], (count,)
        else:
            conds, args = [id_cond], (str(start), count)

        if self._even_only:
            conds = conds + ['id % 2 = 0']

        cur = self._connection.execute('''SELECT "id", "datetime", "host",
            "program", "facility", "level", "message" FROM logs {} ORDER
            BY id {} LIMIT ?'''.format(self._build_where(conds), order), args)

        result = []
        while True:
            rec = cur.fetchone()
            if rec is None:
                return result
            result.append({ 'id': rec[0],
                'datetime': datetime.datetime.strptime(rec[1], '%Y-%m-%d %H:%M:%S'),
                'host': rec[2], 'program': rec[3], 'facility': rec[4],
                'level': rec[5], 'message': rec[6] })

    def _build_where(self, conds):
        if not conds:
            return ''
        return 'WHERE {}'.format(' AND '.join(['({})'.format(x) for x in conds]))
