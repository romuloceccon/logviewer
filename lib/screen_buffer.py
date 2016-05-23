class ScreenBuffer(object):
    class Line(object):
        def __init__(self, data):
            self._id = data['id']
            self._message = data['message']

        @property
        def id(self):
            return self._id

        @property
        def message(self):
            return self._message

    def __init__(self, message_driver, step_size, buffer_size=None,
            low_buffer_threshold=None):
        self._message_driver = message_driver

        self._step_size = step_size
        self._buffer_size = buffer_size \
            if not buffer_size is None else step_size * 5
        self._low_buffer_threshold = low_buffer_threshold \
            if not low_buffer_threshold is None else step_size

        n = self._buffer_size + self._step_size
        self._lines = self._fetch_lines(None, True, n)

        self._set_position(len(self._lines) - self._step_size)

    def _fetch_lines(self, start, desc, count):
        result = [ScreenBuffer.Line(x) for x in
            self._message_driver.get_records(start, desc, count)]
        if desc:
            result.reverse()
        return result

    def _set_position(self, pos):
        p_min, p_max = 0, len(self._lines) - self._step_size
        if pos < p_min:
            self._position = p_min
        elif pos > p_max:
            self._position = p_max
        else:
            self._position = pos

    def _check_backward_buffer(self):
        if self._position <= self._low_buffer_threshold:
            new_lines = self._fetch_lines(self._lines[0].id, True,
                self._buffer_size)
            self._lines = new_lines + self._lines
            self._position += len(new_lines)
            self._check_step_size()

    def _check_forward_buffer(self):
        # To be symetric with move_backward we need to check the number of lines
        # after the last line of the *next* page, and not of the current one.
        hi_threshold = len(self._lines) - self._low_buffer_threshold
        if self._position + self._step_size >= hi_threshold:
            new_lines = self._fetch_lines(self._lines[-1].id, False,
                self._buffer_size)
            self._lines = self._lines + new_lines

    def _check_step_size(self):
        if self._position + self._step_size > len(self._lines):
            self._set_position(len(self._lines) - self._step_size)

    @property
    def step_size(self):
        return self._step_size

    @step_size.setter
    def step_size(self, val):
        self._step_size = val

        self._check_step_size()

        self._check_backward_buffer()
        self._check_forward_buffer()

    def get_current_lines(self):
        p = self._position
        q = p + self._step_size
        return self._lines[p:q]

    def move_backward(self):
        self._set_position(self._position - self._step_size)
        self._check_backward_buffer()

    def move_forward(self):
        self._set_position(self._position + self._step_size)
        self._check_forward_buffer()
