from screen_buffer import ScreenBuffer

class SqlDriver(ScreenBuffer.Driver):
    def __init__(self, level=None):
        self._level = level

    def prepare_query(self, start, desc, count):
        parts = [
            "SELECT id, facility_num, level_num, host, datetime, program, pid, message",
            "FROM logs",
            self._where(self._id_where(start, desc)),
            self._order(desc),
            self._limit(count)
        ]
        return self.select(' '.join(p for p in parts if p))

    def _id_where(self, start, desc):
        if start is None:
            return
        if desc:
            fmt = 'id < {}'
        else:
            fmt = 'id > {}'
        return fmt.format(start)

    def _where(self, id_where):
        conds = []
        if id_where:
            conds.append(id_where)
        if not self._level is None:
            conds.append('level_num <= {}'.format(self._level))
        if not conds:
            return
        return 'WHERE {}'.format(' AND '.join(conds))

    def _order(self, desc):
        if desc:
            return 'ORDER BY id DESC'
        return 'ORDER BY id ASC'

    def _limit(self, count):
        return 'LIMIT {}'.format(count)
