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

    def __init__(self, message_driver):
        self._message_driver = message_driver
        self._buffer_size = 5
        self._low_buffer_threshold = 2
        self._step_size = 2

        n = self._buffer_size + self._step_size
        self._lines = self._fetch_lines(None, False, n)

        self._position = self._buffer_size

    def _fetch_lines(self, start, desc, count):
        return [ScreenBuffer.Line(x) for x in
            self._message_driver.get_records(start, desc, count)]

    def get_current_lines(self):
        p = self._position
        q = p + self._step_size
        return self._lines[p:q]

    def move_backward(self):
        self._position -= self._step_size
        if self._position <= self._low_buffer_threshold:
            new_lines = self._fetch_lines(self._lines[0].id, True,
                self._buffer_size)
            self._lines = new_lines + self._lines
            self._position += len(new_lines)

    def move_forward(self):
        self._position += self._step_size
        if self._position >= len(self._lines) - self._low_buffer_threshold:
            new_lines = self._fetch_lines(self._lines[-1].id, False,
                self._buffer_size)
            self._lines = self._lines + new_lines
