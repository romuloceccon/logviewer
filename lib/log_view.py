import os
import sys
import select
import curses
import datetime

from screen_buffer import ScreenBuffer
from sqlite3_driver import Sqlite3Driver

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
    def __init__(self):
        self._self_pipe = SelfPipe()

        self._poll = select.epoll()
        self._poll.register(sys.stdin.fileno(), select.POLLIN)
        self._poll.register(self._self_pipe.handle, select.POLLIN)

    @property
    def observer(self):
        return self._self_pipe.notify

    def wait_char(self, window):
        while True:
            try:
                result_poll = self._poll.poll()
                if result_poll:
                    if result_poll[0][0] == self._self_pipe.handle:
                        self._self_pipe.read()
                    break
            except InterruptedError:
                break

        return window.getch()

class MainWindow(object):
    MAX_WIDTH = 200
    WIDTHS = [14, 8, 16, 4, 3]

    def __init__(self, window, poll):
        self._window = window
        h, w = window.getmaxyx()

        self._pad = curses.newpad(h, MainWindow.MAX_WIDTH)
        self._pad_x = 0
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)

        self._buf = ScreenBuffer(page_size=h)
        self._buf.add_observer(poll.observer)

    def _pos(self, i):
        return sum(MainWindow.WIDTHS[:i]) + i

    def _width(self, i):
        if i >= len(MainWindow.WIDTHS):
            return MainWindow.MAX_WIDTH - sum(MainWindow.WIDTHS) - len(MainWindow.WIDTHS)
        return MainWindow.WIDTHS[i]

    def _update_line(self, y, p, val):
        self._pad.addnstr(y, self._pos(p), val, self._width(p))

    def _go_right(self):
        self._pad_x = min(self._pad_x + 4, self._pad_x_max)

    def _go_left(self):
        self._pad_x = max(self._pad_x - 4, 0)

    def open(self):
        self._buf.start(Sqlite3Driver('test.db'))

    def close(self):
        self._buf.stop()

    def refresh(self):
        self._window.clear()
        self._pad.clear()

        for i, line in enumerate(self._buf.get_current_lines()):
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

    def resize(self):
        h, w = self._window.getmaxyx()
        self._buf.page_size = h
        self._pad.resize(h, MainWindow.MAX_WIDTH)
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)
        self._pad_x = min(self._pad_x, self._pad_x_max)

    def handle_key(self, k):
        if k == curses.KEY_NPAGE:
            self._buf.go_to_next_page()
        elif k == curses.KEY_PPAGE:
            self._buf.go_to_previous_page()
        elif k == curses.KEY_DOWN:
            self._buf.go_to_next_line()
        elif k == curses.KEY_UP:
            self._buf.go_to_previous_line()
        elif k == curses.KEY_RIGHT:
            self._go_right()
        elif k == curses.KEY_LEFT:
            self._go_left()

    def set_level(self, val):
        self._buf.restart(Sqlite3Driver('test.db', level=val))

class LevelWindow(object):
    def __init__(self, parent):
        self._parent = parent
        self._pos = 0
        self._levels = ScreenBuffer.Line.LEVELS
        self._height = len(self._levels) + 4
        self._width = max([len(x) for x in self._levels]) + 5
        self.resize()

    @property
    def value(self):
        return self._pos

    def handle_key(self, k):
        if k == ord('\n'):
            return True
        if k == curses.KEY_DOWN:
            self._pos = min(len(self._levels) - 1, self._pos + 1)
        elif k == curses.KEY_UP:
            self._pos = max(0, self._pos - 1)

    def refresh(self):
        self._window.clear()
        self._window.border()
        title = '|Level|'
        self._window.addstr(0, (self._width - len(title)) // 2, title)
        for i, s in enumerate(self._levels):
            if i == self._pos:
                self._window.addch(i + 2, 2, '▶')
            self._window.addnstr(i + 2, 3, s, self._width - 5)
        self._window.noutrefresh()

    def resize(self):
        h_parent, w_parent = self._parent.getmaxyx()
        self._window = self._parent.subwin(self._height, self._width,
            (h_parent - self._height) // 2, (w_parent - self._width) // 2)
        self._window.bkgd(curses.color_pair(1))
