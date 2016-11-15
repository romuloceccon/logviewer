import calendar
import datetime

from .screen_buffer import ScreenBuffer

class Filter(object):
    def __init__(self):
        self._level = None
        self._max_level = len(ScreenBuffer.Line.LEVELS) - 1
        self._facility = None
        self._host = None
        self._program = None

    # Facility: None means all facilities
    @property
    def facility(self):
        return self._facility

    @facility.setter
    def facility(self, val):
        self._facility = val

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, val):
        if val:
            self._host = val
        else:
            self._host = None

    # Level: None means maximum messages (i.e., level_num=7)
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

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, val):
        if val:
            self._program = val
        else:
            self._program = None

    def get_summary(self):
        if self.facility is None:
            facility = ('[f]acility', 'ALL')
        else:
            facility = ('[f]acility', ScreenBuffer.Line.FACILITIES[self.facility])
        level = ('[l]evel', ScreenBuffer.Line.LEVELS[self.level])
        program = ('[p]rogram', self.program or '*')
        host = ('[h]ost', self.host or '*')
        return (level, facility, program, host)

class Datetime(object):
    class YearField(object):
        def _change_year(self, dt, year):
            if dt.month == 2 and dt.day == 29 and not calendar.isleap(year):
                return dt.replace(year=year, month=2, day=28)
            return dt.replace(year=year)

        def increment(self, dt):
            return self._change_year(dt, dt.year + 1)

        def decrement(self, dt):
            return self._change_year(dt, dt.year - 1)

    class MonthField(object):
        def _inc_month(self, dt, delta):
            month_0 = dt.month - 1 + delta
            year = dt.year + month_0 // 12
            month = month_0 % 12 + 1
            day = min(dt.day, calendar.monthrange(year, month)[1])
            return dt.replace(year=year, month=month, day=day)

        def increment(self, dt):
            return self._inc_month(dt, 1)

        def decrement(self, dt):
            return self._inc_month(dt, -1)

    class TimeField(object):
        def __init__(self, key):
            self._key = key

        def increment(self, dt):
            return dt + datetime.timedelta(**({ self._key: 1 }))

        def decrement(self, dt):
            return dt + datetime.timedelta(**({ self._key: -1 }))

    FIELDS = (
        ((0, 4), YearField()),
        ((5, 2), MonthField()),
        ((8, 2), TimeField('days')),
        ((11, 2), TimeField('hours')),
        ((14, 2), TimeField('minutes')),
        ((17, 2), TimeField('seconds')))

    def __init__(self, dt):
        self._datetime = dt
        self._current_field = 0

    def _change_year(self, new_year):
        dt = self._datetime
        if dt.month == 2 and dt.day == 29 and not calendar.isleap(new_year):
            dt = dt.replace(month=2, day=28)
        self._datetime = dt.replace(year=new_year)

    def decrement(self):
        self._datetime = Datetime.FIELDS[self._current_field][1]. \
            decrement(self._datetime)

    def increment(self):
        self._datetime = Datetime.FIELDS[self._current_field][1]. \
            increment(self._datetime)

    def move_left(self):
        self._current_field = max(0, self._current_field - 1)

    def move_right(self):
        self._current_field = min(len(Datetime.FIELDS) - 1,
            self._current_field + 1)

    @property
    def position(self):
        return Datetime.FIELDS[self._current_field][0]

    @property
    def text(self):
        return self._datetime.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def value(self):
        return self._datetime
