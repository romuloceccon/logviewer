import os
import sys
import select
import curses
import datetime
import struct

from screen_buffer import ScreenBuffer
from sqlite3_driver import Sqlite3Driver
from text_input import TextInput
from utf8_parser import Utf8Parser
from window import Window, SelectWindow, TextWindow

class EventPoll(object):
    def __init__(self):
        self._r, self._w = os.pipe()

        self._poll = select.epoll()
        self._poll.register(sys.stdin.fileno(), select.POLLIN)
        self._poll.register(self._r, select.POLLIN)

    def _notify(self):
        os.write(self._w, b'0')

    @property
    def observer(self):
        return self._notify

    def wait_char(self, window):
        while True:
            try:
                result_poll = self._poll.poll()
                if result_poll:
                    if result_poll[0][0] == self._r:
                        os.read(self._r, 256)
                    break
            except InterruptedError:
                break

        return window.getch()

class Manager(object):
    def __init__(self, curses_window):
        curses.start_color()

        curses.curs_set(0)
        curses_window.nodelay(1)

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

        self._curses_window = curses_window
        self._poll = EventPoll()
        h, w = curses_window.getmaxyx()

        self._stack = list()

    def _loop(self):
        self._curses_window.clear()
        self._curses_window.noutrefresh()

        for window in self._stack:
            window.refresh()

        curses.doupdate()

        k = self._poll.wait_char(self.curses_window)
        if k == curses.KEY_RESIZE:
            h, w = self._curses_window.getmaxyx()
            for window in self._stack:
                window.resize(h, w)
        else:
            self._stack[-1].handle_key(k)

    @property
    def poll(self):
        return self._poll

    @property
    def curses(self):
        return curses

    @property
    def curses_window(self):
        return self._curses_window

    def run(self, main_window):
        main_window.show()

class MainWindow(Window):
    MAX_WIDTH = 200
    WIDTHS = [14, 8, 16, 4, 3]

    def __init__(self, window_manager, driver_factory):
        Window.__init__(self, window_manager)

        curses_window = window_manager.curses_window
        h, w = curses_window.getmaxyx()

        self._driver_factory = driver_factory

        self._pad = curses.newpad(h, MainWindow.MAX_WIDTH)
        self._pad_x = 0
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)

        self._buf = ScreenBuffer(page_size=h)
        self._buf.add_observer(window_manager.poll.observer)

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

    def _change_level(self):
        window = LevelWindow(self.window_manager)
        window.position = self._driver_factory.level
        if window.show():
            self._driver_factory.level = window.position
            self._buf.restart(self._driver_factory.create_driver())

    def _change_facility(self):
        window = FacilityWindow(self.window_manager)
        window.position = 0 if self._driver_factory.facility is None else \
            self._driver_factory.facility + 1
        if window.show():
            self._driver_factory.facility = None if window.position == 0 else \
                window.position - 1
            self._buf.restart(self._driver_factory.create_driver())

    def start(self):
        self._buf.start(Sqlite3Driver('test.db'))

    def finish(self):
        self._buf.stop()

    def refresh(self):
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

        y, x = self.window_manager.curses_window.getmaxyx()
        self._pad.noutrefresh(0, self._pad_x, 0, 0, y - 1, x - 1)

    def resize(self, h, w):
        self._buf.page_size = h
        self._pad.resize(h, MainWindow.MAX_WIDTH)
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)
        self._pad_x = min(self._pad_x, self._pad_x_max)

    def handle_key(self, k):
        if k == ord('q'):
            self.close(None)
        elif k == ord('l'):
            self._change_level()
        elif k == ord('f'):
            self._change_facility()
        elif k == ord('t'):
            window = TextWindow(self.window_manager, 'Test', 30)
            window.show()
        elif k == curses.KEY_NPAGE:
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

class LevelWindow(SelectWindow):
    def __init__(self, window_manager):
        SelectWindow.__init__(self, window_manager, 'Level', ScreenBuffer.Line.LEVELS)

class FacilityWindow(SelectWindow):
    def __init__(self, window_manager):
        SelectWindow.__init__(self, window_manager, 'Facility',
            ['<ALL>'] + ScreenBuffer.Line.FACILITIES)
