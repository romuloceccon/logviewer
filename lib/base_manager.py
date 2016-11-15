import curses

class BaseManager(object):
    def __init__(self, curses, curses_window):
        curses.start_color()

        curses.curs_set(0)
        curses_window.nodelay(1)

        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)

        self._curses = curses
        self._curses_window = curses_window

        self._stack = list()

    def loop(self):
        self._curses_window.erase()
        self._curses_window.noutrefresh()

        for window in self._stack:
            window.refresh()

        self._curses.doupdate()

        self.wait()
        for k in self._get_chars():
            if k == curses.KEY_RESIZE:
                h, w = self._curses_window.getmaxyx()
                for window in self._stack:
                    window.resize(h, w)
            elif self._stack:
                self._stack[-1].handle_key(k)

    def _get_chars(self):
        while True:
            key = self._curses_window.getch()
            if key == -1:
                return
            yield key

    @property
    def curses(self):
        return self._curses

    @property
    def curses_window(self):
        return self._curses_window

    @property
    def stack(self):
        return self._stack

    def run(self, window):
        window.show()

    def wait(self):
        raise RuntimeError('Not implemented')
