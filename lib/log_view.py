import os
import sys
import select
import curses
import datetime

class SelfPipe(object):
    def __init__(self):
        self._r, self._w = os.pipe()

    def notify(self):
        os.write(self._w, b'0')

    def read(self):
        return os.read(self._r, 256)

    @property
    def handle(self):
        return self._r

class EventPoll(object):
    def __init__(self, window):
        self._window = window

        self._self_pipe = SelfPipe()

        self._poll = select.epoll()
        self._poll.register(sys.stdin.fileno(), select.POLLIN)
        self._poll.register(self._self_pipe.handle, select.POLLIN)

    @property
    def observer(self):
        return self._self_pipe.notify

    def wait_char(self):
        while True:
            try:
                result_poll = self._poll.poll()
                if result_poll:
                    if result_poll[0][0] == self._self_pipe.handle:
                        self._self_pipe.read()
                    break
            except InterruptedError:
                break

        return self._window.getch()

class MainWindow(object):
    MAX_WIDTH = 200
    WIDTHS = [14, 8, 16, 4, 3]

    def __init__(self, window):
        self._window = window
        h, w = window.getmaxyx()
        self._pad = curses.newpad(h, MainWindow.MAX_WIDTH)
        self._pad_x = 0
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)

    def _pos(self, i):
        return sum(MainWindow.WIDTHS[:i]) + i

    def _width(self, i):
        if i >= len(MainWindow.WIDTHS):
            return MainWindow.MAX_WIDTH - sum(MainWindow.WIDTHS) - len(MainWindow.WIDTHS)
        return MainWindow.WIDTHS[i]

    def _update_line(self, y, p, val):
        self._pad.addnstr(y, self._pos(p), val, self._width(p))

    def update(self, lines):
        self._window.clear()
        self._pad.clear()

        for i, line in enumerate(lines):
            if not line.is_continuation or i == 0:
                dt_str = datetime.datetime.strftime(line.datetime, '%m-%d %H:%M:%S')
                self._update_line(i, 0, dt_str)
                self._update_line(i, 1, line.host)
                self._update_line(i, 2, line.program)
                self._update_line(i, 3, line.facility.upper())
                self._update_line(i, 4, line.level.upper())
            self._update_line(i, 5, line.message)

        self._window.noutrefresh()
        y, x = self._window.getmaxyx()
        self._pad.noutrefresh(0, self._pad_x, 0, 0, y - 1, x - 1)
        curses.doupdate()

    def go_right(self):
        self._pad_x = min(self._pad_x + 4, self._pad_x_max)

    def go_left(self):
        self._pad_x = max(self._pad_x - 4, 0)

    def resize(self):
        h, w = self._window.getmaxyx()
        self._pad.resize(h, MainWindow.MAX_WIDTH)
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)
        self._pad_x = min(self._pad_x, self._pad_x_max)
