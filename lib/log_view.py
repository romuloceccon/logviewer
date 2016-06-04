import os
import sys
import select
import curses
import datetime
import struct

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

class Window(object):
    def __init__(self, window_manager):
        self._window_manager = window_manager
        self._result = None
        self._closed = False

    @property
    def closed(self):
        return self._closed

    @property
    def result(self):
        return self._result

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

    def handle_key(self, k):
        raise RuntimeError('Not implemented')

    def refresh(self):
        raise RuntimeError('Not implemented')

    def resize(self, height, width):
        raise RuntimeError('Not implemented')

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
            window = TextWindow(self.window_manager)
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

class SelectWindow(Window):
    def __init__(self, window_manager, title, items):
        Window.__init__(self, window_manager)

        self._curses = window_manager.curses
        self._parent = window_manager.curses_window

        self._title = title

        if len(items) == 0:
            raise ValueError('Cannot create window with empty list')

        self._items = items
        self._count = len(items)
        self._position = 0
        self._offset = 0

        self._border = 2
        self._height = self._count + 2 * self._border
        self._width = 20
        self._min_height = 5
        self._min_width = 20

        self._pad = self._curses.newpad(self._count, 16)
        self._pad.bkgd(self._curses.color_pair(1))

        self.resize(*(self._parent.getmaxyx()))

    def _update_offset(self):
        pos = self._position
        self._offset = min(pos, self._count - self._list_height,
            max(self._offset, pos - self._list_height + 1))

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, val):
        if val < 0 or val >= self._count:
            raise IndexError('Invalid position {}'.format(val))
        self._position = val
        self._update_offset()

    def handle_key(self, k):
        if k == ord('\n'):
            self.close(True)
        elif k == 27:
            self.close(False)
        elif k == curses.KEY_DOWN:
            self.position = min(self._count - 1, self._position + 1)
        elif k == curses.KEY_UP:
            self.position = max(0, self._position - 1)

    def refresh(self):
        if not self._curses_window:
            return

        self._curses_window.clear()
        self._curses_window.border()
        t = '|{}|'.format(self._title)
        self._curses_window.addstr(0, (self._cur_width - len(t)) // 2, t)
        self._curses_window.noutrefresh()
        for i, x in enumerate(self._items):
            prefix = '▶' if i == self._position else ' '
            self._pad.addnstr(i, 0, '{}{}'.format(prefix, x), self._cur_width)
        b = self._border
        self._pad.noutrefresh(self._offset, 0, self._y + b, self._x + b,
            self._y + self._cur_height - (b + 1), self._x + self._cur_width - (b + 1))

    def resize(self, h, w):
        self._curses_window = None
        self._cur_height, self._cur_width, self._list_height = None, None, None
        self._y, self._x = None, None

        new_h, new_w = min(self._height, h), min(self._width, w)
        if new_h < self._min_height or new_w < self._min_width:
            return

        self._y, self._x = (h - new_h) // 2, (w - new_w) // 2
        self._curses_window = self._parent.subwin(new_h, new_w, self._y, self._x)
        self._cur_height, self._cur_width = new_h, new_w
        self._list_height = self._cur_height - 2 * self._border
        self._curses_window.bkgd(self._curses.color_pair(1))

        self._update_offset()

class LevelWindow(SelectWindow):
    def __init__(self, window_manager):
        SelectWindow.__init__(self, window_manager, 'Level', ScreenBuffer.Line.LEVELS)

class FacilityWindow(SelectWindow):
    def __init__(self, window_manager):
        SelectWindow.__init__(self, window_manager, 'Facility',
            ['<ALL>'] + ScreenBuffer.Line.FACILITIES)

class TextWindow(Window):
    def __init__(self, window_manager):
        Window.__init__(self, window_manager)

        self._curses = window_manager.curses
        self._parent = window_manager.curses_window

        self._height = 10
        self._width = 30
        self._text = ''
        self._char = None
        self._offset = 0

        self.resize(*(self._parent.getmaxyx()))

    def handle_key(self, k):
        if k == ord('\n'):
            self.close(True)
        elif k == 27:
            self.close(False)
        elif k == curses.KEY_BACKSPACE:
            if self._offset < 0:
                self._text = self._text[:self._offset - 1] + self._text[self._offset:]
            else:
                self._text = self._text[:-1]
        elif k == curses.KEY_LEFT:
            self._offset = max(-len(self._text), self._offset - 1)
            sys.stderr.write('{}\n'.format(self._offset))
        elif k == curses.KEY_RIGHT:
            self._offset = min(0, self._offset + 1)
            sys.stderr.write('{}\n'.format(self._offset))
        elif k & 0xe0 == 0xc0:
            self._char = k
        elif not self._char is None:
            if self._offset < 0:
                self._text = self._text[:self._offset] + struct.pack('<BB', self._char, k).decode('utf-8') + self._text[self._offset:]
            else:
                self._text += struct.pack('<BB', self._char, k).decode('utf-8')
            self._char = None
        else:
            if self._offset < 0:
                self._text = self._text[:self._offset] + chr(k) + self._text[self._offset:]
            else:
                self._text += chr(k)

    def refresh(self):
        self._curses_window.clear()
        self._curses_window.border()
        self._curses_window.addstr(1, 1, self._text)
        y, x = self._curses_window.getyx()
        self._curses_window.move(y, x + self._offset)
        sys.stderr.write('{} {} => {} {}\n'.format(y, x, y, x + self._offset))
        self._curses_window.noutrefresh()

    def resize(self, h, w):
        new_h, new_w = min(self._height, h), min(self._width, w)
        self._y, self._x = (h - new_h) // 2, (w - new_w) // 2
        self._curses_window = self._parent.subwin(new_h, new_w, self._y, self._x)
        self._curses_window.bkgd(self._curses.color_pair(1))
        self._curses_window.nodelay(0)

    def start(self):
        curses.curs_set(1)
        curses.echo()

    def finish(self):
        curses.curs_set(0)
        curses.noecho()
