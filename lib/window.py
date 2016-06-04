import curses

from screen_cursor import ScreenCursor
from text_input import TextInput
from utf8_parser import Utf8Parser

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

class CenteredWindow(Window):
    def __init__(self, window_manager, title, height, width, min_height,
            min_width):
        Window.__init__(self, window_manager)

        self._curses = window_manager.curses
        self._parent = window_manager.curses_window

        self._title = title

        self._border = 2
        self._padding = 2 * self._border
        self._height = height + self._padding
        self._width = width + self._padding
        self._min_height = min_height + self._padding
        self._min_width = min_width + self._padding

        self.resize(*(self._parent.getmaxyx()))

    def refresh(self):
        if not self._curses_window:
            return

        self._curses_window.clear()
        self._curses_window.border()
        t = '|{}|'.format(self._title)
        self._curses_window.addstr(0, (self._cur_width - len(t)) // 2, t)
        self._curses_window.noutrefresh()

    def resize(self, h, w):
        self._curses_window = None
        self._cur_height, self._cur_width = None, None
        self._y, self._x = None, None

        new_h, new_w = min(self._height, h), min(self._width, w)
        if new_h < self._min_height or new_w < self._min_width:
            return

        self._y, self._x = (h - new_h) // 2, (w - new_w) // 2
        self._curses_window = self._parent.subwin(new_h, new_w, self._y, self._x)
        self._cur_height, self._cur_width = new_h, new_w
        self._curses_window.bkgd(self._curses.color_pair(1))

class SelectWindow(CenteredWindow):
    def __init__(self, window_manager, title, items):
        if len(items) == 0:
            raise ValueError('Cannot create window with empty list')

        self._items = items
        self._count = len(items)
        self._cursor = ScreenCursor(self._count)

        CenteredWindow.__init__(self, window_manager, title,
            self._count, 16, 1, 16)

        self._pad = self._curses.newpad(self._count, 16)
        self._pad.bkgd(self._curses.color_pair(1))

    @property
    def position(self):
        return self._cursor.position

    @position.setter
    def position(self, val):
        if val < 0 or val >= self._count:
            raise IndexError('Invalid position {}'.format(val))
        self._cursor.position = val

    def handle_key(self, k):
        if k == ord('\n'):
            self.close(True)
        elif k == 27:
            self.close(False)
        elif k == curses.KEY_DOWN:
            self.position = min(self._count - 1, self.position + 1)
        elif k == curses.KEY_UP:
            self.position = max(0, self.position - 1)

    def refresh(self):
        CenteredWindow.refresh(self)

        if not self._curses_window:
            return

        for i, x in enumerate(self._items):
            prefix = '▶' if i == self.position else ' '
            self._pad.addnstr(i, 0, '{}{}'.format(prefix, x), self._cur_width)
        b = self._border
        self._pad.noutrefresh(self._cursor.offset, 0, self._y + b, self._x + b,
            self._y + self._cur_height - (b + 1), self._x + self._cur_width - (b + 1))

    def resize(self, h, w):
        CenteredWindow.resize(self, h, w)

        if self._curses_window:
            self._cursor.visible_count = self._cur_height - self._padding

class TextWindow(CenteredWindow):
    def __init__(self, window_manager, title, max_len):
        self._max_len = max_len
        self._text_input = TextInput(max_len=max_len)
        self._utf8_parser = Utf8Parser(self._text_input.put)

        CenteredWindow.__init__(self, window_manager, title, 1,
            self._text_input.width, 1, 2)

    def _update_text_width(self):
        if self._cur_width:
            self._text_input.width = self._cur_width - self._padding

    @property
    def text(self):
        return self._text_input.text

    @text.setter
    def text(self, val):
        self._text_input = TextInput(max_len=self._max_len, text=val)
        self._update_text_width()

    def handle_key(self, k):
        if k == ord('\n'):
            self.close(True)
        elif k == 27:
            if self._parent.getch() == -1:
                self.close(False)
        elif k >= curses.KEY_MIN:
            self._text_input.put(k)
        else:
            self._utf8_parser.put_key(k)

    def refresh(self):
        CenteredWindow.refresh(self)

        if not self._curses_window:
            return

        self._curses_window.addstr(self._border, self._border,
            ' ' * self._text_input.width, self._curses.color_pair(2))
        self._curses_window.move(2, 2)
        self._curses_window.addstr(self._border, self._border,
            self._text_input.visible_text, self._curses.color_pair(2))
        self._curses_window.move(2, 2 + self._text_input.cursor)
        self._curses_window.noutrefresh()

    def resize(self, h, w):
        CenteredWindow.resize(self, h, w)
        self._update_text_width()

    def start(self):
        self._curses.curs_set(1)

    def finish(self):
        self._curses.curs_set(0)
