import re

from .screen_buffer import ScreenBuffer

class SQLDriver(ScreenBuffer.Driver):
    def __init__(self, level=None, facility=None, host=None, program=None,
            start_date=None):
        self._level = level
        self._facility = facility
        self._host = host
        self._program = program
        self._start_date = start_date

    def has_start_date(self):
        return not (not self._start_date)

    def prepare_datetime_query(self):
        dt_str = self._start_date.strftime('%Y-%m-%d %H:%M:%S')

        return self.select("SELECT id, facility_num, level_num, host, "\
            "datetime, program, pid, message FROM logs WHERE datetime >= "\
            "'{}' ORDER BY datetime ASC LIMIT 1".format(dt_str))

    def prepare_query(self, start, desc, count):
        parts = [
            "SELECT id, facility_num, level_num, host, datetime, program, pid, message",
            "FROM logs",
            self._where(self._id_where(start, desc)),
            self._order(desc),
            self._limit(count)
        ]
        return self.select(' '.join(p for p in parts if p))

    def _build_one_filter(self, value):
        is_wildcard, is_negative = False, False

        match = re.search('(.+)\*$', value)
        if match:
            value = match.group(1)
            is_wildcard = True

        match = re.search('^!(.+)', value)
        if match:
            value = match.group(1)
            is_negative = True

        if not is_wildcard and not is_negative:
            return "= '{}'".format(value)
        elif not is_wildcard:
            return "<> '{}'".format(value)
        elif not is_negative:
            return "LIKE '{}%'".format(value)
        else:
            return "NOT LIKE '{}%'".format(value)

    def _get_separate_conditions(self, column, list):
        return ["{} {}".format(column, self._build_one_filter(x)) for x in list]

    def _get_include_and_exclude_conditions(self, conditions):
        include = []
        exclude = []
        for val in conditions.split(' '):
            if not val:
                continue
            if re.search('^!', val):
                exclude.append(val)
            else:
                include.append(val)
        return (include, exclude)

    def _get_string_condition(self, column, conditions):
        include, exclude = self._get_include_and_exclude_conditions(conditions)
        parts = []
        if include:
            list = " OR ".join(self._get_separate_conditions(column, include))
            parts.append("({})".format(list))
        parts += self._get_separate_conditions(column, exclude)
        return " AND ".join(parts)

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
        if not self._facility is None:
            conds.append('facility_num = {}'.format(self._facility))
        if not self._host is None:
            conds.append(self._get_string_condition('host', self._host))
        if not self._program is None:
            conds.append(self._get_string_condition('program', self._program))
        if not conds:
            return
        return 'WHERE {}'.format(' AND '.join(conds))

    def _order(self, desc):
        if desc:
            return 'ORDER BY id DESC'
        return 'ORDER BY id ASC'

    def _limit(self, count):
        return 'LIMIT {}'.format(count)
