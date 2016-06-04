import curses

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
