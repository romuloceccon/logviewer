import os
import sys
import select
import curses
import datetime

from screen_buffer import ScreenBuffer
from sqlite3_driver import Sqlite3Driver

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

        self._curses_window = curses_window
        self._poll = EventPoll()
        h, w = curses_window.getmaxyx()
        self._screen_buffer = ScreenBuffer(page_size=h)
        self._screen_buffer.add_observer(self._poll.observer)

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
    def screen_buffer(self):
        return self._screen_buffer

    @property
    def curses_window(self):
        return self._curses_window

    def run(self, main_window):
        main_window.show()

class Window(object):
    def __init__(self, window_manager):
        self._window_manager = window_manager
        # TODO: acabar com esse método. Não é necessário que o window manager
        # saiba qual é o curses window de cada janela
        self._curses_window = self.init_curses_window(window_manager)
        self._result = None
        self._closed = False

    @property
    def curses_window(self):
        return self._curses_window

    @property
    def window_manager(self):
        return self._window_manager

    def show(self):
        self._window_manager._stack.append(self)
        self.start()
        try:
            while not self._closed:
                self._window_manager._loop()
            return self._result
        finally:
            self.finish()
            self._window_manager._stack.pop()

    def close(self, result):
        self._result = result
        self._closed = True

    def start(self):
        pass

    def finish(self):
        pass

    def refresh(self):
        pass

    def resize(self, height, width):
        pass

class MainWindow(Window):
    MAX_WIDTH = 200
    WIDTHS = [14, 8, 16, 4, 3]

    def init_curses_window(self, window_manager):
        curses_window = window_manager.curses_window
        h, w = curses_window.getmaxyx()

        self._pad = curses.newpad(h, MainWindow.MAX_WIDTH)
        self._pad_x = 0
        self._pad_x_max = max(0, MainWindow.MAX_WIDTH - w)

        self._buf = window_manager.screen_buffer

        return curses_window

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
        level = window.show()
        if not level is None:
            self._buf.restart(Sqlite3Driver('test.db', level=level))

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

class LevelWindow(Window):
    def init_curses_window(self, window_manager):
        self._parent = window_manager.curses_window
        self._pos = 0
        self._levels = ScreenBuffer.Line.LEVELS

        self._height = len(self._levels) + 4
        self._width = max([len(x) for x in self._levels]) + 5

        h_parent, w_parent = self._parent.getmaxyx()
        result = self._parent.subwin(self._height, self._width,
            (h_parent - self._height) // 2, (w_parent - self._width) // 2)
        result.bkgd(curses.color_pair(1))
        return result

    def handle_key(self, k):
        sys.stderr.write('{}\n'.format(k))
        sys.stderr.flush()
        if k == ord('\n'):
            self.close(self._pos)
        elif k == 27:
            self.close(None)
        elif k == curses.KEY_DOWN:
            self._pos = min(len(self._levels) - 1, self._pos + 1)
        elif k == curses.KEY_UP:
            self._pos = max(0, self._pos - 1)

    def refresh(self):
        self.curses_window.clear()
        self.curses_window.border()
        title = '|Level|'
        self.curses_window.addstr(0, (self._width - len(title)) // 2, title)
        for i, s in enumerate(self._levels):
            if i == self._pos:
                self.curses_window.addch(i + 2, 2, '▶')
            self.curses_window.addnstr(i + 2, 3, s, self._width - 5)
        self.curses_window.noutrefresh()

    def resize(self, h, w):
        self.curses_window.mvwin((h - self._height) // 2, (w - self._width) // 2)
