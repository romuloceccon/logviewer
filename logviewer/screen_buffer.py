import threading

class ScreenBuffer(object):
    STOP = 1
    GET_RECORDS = 2
    TIMEOUT = 3

    class Driver(object):
        def has_start_date(self):
            pass

        def start_connection(self):
            pass

        def stop_connection(self):
            pass

        def prepare_datetime_query(self):
            pass

        def prepare_query(self, start, desc, count):
            pass

        def fetch_record(self, query):
            pass

    class Thread(threading.Thread):
        def __init__(self, screen_buffer, driver):
            threading.Thread.__init__(self)
            self._screen_buffer = screen_buffer
            self._driver = driver

        def run(self):
            self._screen_buffer.clear()
            self._driver.start_connection()
            try:
                timeout = None
                while True:
                    cmd = self._screen_buffer._wait_event(timeout)
                    if cmd == ScreenBuffer.STOP:
                        return
                    timeout = self._screen_buffer.get_records(self._driver)
            finally:
                self._driver.stop_connection()

    class Line(object):
        FACILITIES = ['kern', 'user', 'mail', 'daemon', 'auth', 'syslog', 'lpr',
            'news', 'uucp', '9', 'authpriv', 'ftp', '12', '13', '14', 'cron',
            'local0', 'local1', 'local2', 'local3', 'local4', 'local5',
            'local6', 'local7']
        LEVELS = ['emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info',
            'debug']

        def __init__(self, data, is_continuation):
            self._id = data['id']
            self._datetime = data['datetime']
            self._host = data['host']
            self._program = data['program']
            self._facility = self._translate(ScreenBuffer.Line.FACILITIES, data['facility_num'])
            self._level = self._translate(ScreenBuffer.Line.LEVELS, data['level_num'])
            self._message = data['message']
            self._is_continuation = is_continuation

        def _translate(self, table, val):
            if not isinstance(val, int):
                if not isinstance(val, str) or not val.isdigit():
                    return ''
                val = int(val)
            if val < 0 or val >= len(table):
                return ''
            return table[val]

        @property
        def id(self):
            return self._id

        @property
        def datetime(self):
            return self._datetime

        @property
        def host(self):
            return self._host

        @property
        def program(self):
            return self._program

        @property
        def facility(self):
            return self._facility

        @property
        def level(self):
            return self._level

        @property
        def message(self):
            return self._message

        @property
        def is_continuation(self):
            return self._is_continuation

    def __init__(self, page_size, buffer_size=None, low_buffer_threshold=None,
            timeout=None):
        self._observers = set()

        self._page_size = page_size
        self._buffer_size = buffer_size \
            if not buffer_size is None else page_size * 5
        self._low_buffer_threshold = low_buffer_threshold \
            if not low_buffer_threshold is None else page_size
        self._timeout = timeout

        self._auto_scroll = True
        self._lines = None
        self._position = None
        self._bottom_seen = None
        self._stopped = None
        self._invalid = None
        self._thread = None
        self._lock = threading.Lock()
        self._condition_var = threading.Condition(self._lock)

        self.clear()

    def _build_lines(self, rec):
        msgs = rec['message'].split('\n')
        for i, msg in enumerate(msgs):
            tmp = rec.copy()
            tmp['message'] = msg
            yield ScreenBuffer.Line(tmp, i > 0)

    def _set_position(self, pos):
        p_min, p_max = 0, max(len(self._lines) - self._page_size, 0)
        if pos < p_min:
            self._position = p_min
        elif pos > p_max:
            self._position = p_max
        else:
            self._position = pos

    def _check_page_size(self):
        if self._position + self._page_size > len(self._lines):
            self._set_position(len(self._lines) - self._page_size)

    def _notify_observers(self):
        for observer in self._observers:
            observer()

    def _wait_event(self, timeout=None):
        if not self._condition_var:
            return

        with self._condition_var:
            while not (self._stopped or self._invalid):
                if not self._condition_var.wait(timeout):
                    return ScreenBuffer.TIMEOUT
            if self._stopped:
                return ScreenBuffer.STOP
            self._invalid = False
            return ScreenBuffer.GET_RECORDS

    def _invalidate(self):
        if self._condition_var is None:
            return

        with self._condition_var:
            self._invalid = True
            self._condition_var.notify()

    @property
    def page_size(self):
        with self._lock:
            return self._page_size

    @page_size.setter
    def page_size(self, val):
        with self._lock:
            self._page_size = val
            self._check_page_size()

    def get_current_lines(self):
        with self._lock:
            p = self._position
            q = p + self._page_size
            return self._lines[p:q]

    def go_to_previous_line(self):
        with self._lock:
            self._set_position(self._position - 1)
        self._invalidate()

    def go_to_next_line(self):
        with self._lock:
            self._set_position(self._position + 1)
        self._invalidate()

    def go_to_previous_page(self):
        with self._lock:
            self._set_position(self._position - self._page_size)
        self._invalidate()

    def go_to_next_page(self):
        with self._lock:
            self._set_position(self._position + self._page_size)
        self._invalidate()

    def prepend_record(self, rec):
        with self._lock:
            cnt = 0
            old_pos = self._position
            for i, line in enumerate(self._build_lines(rec)):
                cnt += 1
                self._lines.insert(i, line)
            self._set_position(self._position + cnt)
            notify = old_pos + cnt != self._position
        if notify:
            self._notify_observers()

    def append_record(self, rec):
        with self._lock:
            old_len = len(self._lines)
            for line in self._build_lines(rec):
                self._lines.append(line)

            if old_len - self._position <= self._page_size and self._auto_scroll:
                notify = True
                self._set_position(len(self._lines) - self._page_size)
            elif old_len < self._page_size:
                notify = True
            else:
                notify = False

        if notify:
            self._notify_observers()

    def add_observer(self, observer):
        # TODO: add/remove observer will be called from different threads; make
        # them thread safe!
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def get_buffer_instructions(self, driver):
        result = []

        with self._lock:
            if self._lines:
                if self._position + self._page_size >= len(self._lines) - self._low_buffer_threshold:
                    result.append((self._lines[-1].id, False, self._buffer_size))
                if self._position <= self._low_buffer_threshold:
                    result.append((self._lines[0].id, True, self._buffer_size))
            else:
                rec, count = None, self._buffer_size + self._page_size
                if driver.has_start_date():
                    query = driver.prepare_datetime_query()
                    rec = tmp = driver.fetch_record(query)
                    while tmp:
                        tmp = driver.fetch_record(query)

                if rec:
                    self._auto_scroll = False
                    result.append((rec['id'] - 1, False, count))
                    result.append((rec['id'], True, self._buffer_size))
                else:
                    result.append((None, True, count))

        return tuple(result)

    def get_records(self, driver):
        result = None

        for start, desc, count in self.get_buffer_instructions(driver):
            if desc and self._bottom_seen:
                continue

            query = driver.prepare_query(start, desc, count)
            while True:
                rec = driver.fetch_record(query)
                if rec is None:
                    break
                count -= 1
                if desc:
                    self.prepend_record(rec)
                else:
                    self.append_record(rec)
            if desc and count > 0:
                self._bottom_seen = True
            if count > 0 and not desc or start is None:
                result = self._timeout

        self._auto_scroll = True
        return result

    def clear(self):
        with self._lock:
            old_len = 0
            if not self._lines is None:
                old_len = len(self._lines)
            self._lines = list()
            self._set_position(0)

        if old_len > 0:
            self._notify_observers()

    def start(self, driver):
        if self._thread:
            raise ValueError('{} driver is already started'.format(self.__class__.__name__))

        self._bottom_seen = False
        self._stopped = False
        self._invalid = True

        self._thread = ScreenBuffer.Thread(self, driver)
        self._thread.start()

    def stop(self):
        self._thread, tmp = None, self._thread

        with self._condition_var:
            self._stopped = True
            if tmp:
                self._condition_var.notify()
        if tmp:
            tmp.join()

    def restart(self, driver):
        self.stop()
        self.start(driver)
