import sys
import curses
import datetime
import select

from screen_buffer import ScreenBuffer
from sqlite3_driver import Sqlite3Driver

MAX_WIDTH = 200
WIDTHS = [14, 8, 16, 4, 3]

def pos(i):
    return sum(WIDTHS[:i]) + i

def width(i):
    if i >= len(WIDTHS):
        return MAX_WIDTH - sum(WIDTHS) - len(WIDTHS)
    return WIDTHS[i]

def run_app(window):
    curses.curs_set(0)
    window.nodelay(1)

    msg = Sqlite3Driver('test.db')
    h, w = window.getmaxyx()
    buf = ScreenBuffer(msg, page_size=h)
    pad = curses.newpad(h, MAX_WIDTH)
    pad_x = 0
    pad_x_max = max(0, MAX_WIDTH - w)

    poll = select.epoll()
    poll.register(sys.stdin.fileno(), select.POLLIN)

    while True:
        window.clear()
        pad.clear()

        for i, line in enumerate(buf.get_current_lines()):
            if not line.is_continuation or i == 0:
                pad.addnstr(i, pos(0), datetime.datetime.strftime(line.datetime, '%m-%d %H:%M:%S'), width(0))
                pad.addnstr(i, pos(1), line.host, width(1))
                pad.addnstr(i, pos(2), line.program, width(2))
                pad.addnstr(i, pos(3), line.facility.upper(), width(3))
                pad.addnstr(i, pos(4), line.level.upper(), width(4))
            pad.addnstr(i, pos(5), line.message, width(5))

        window.noutrefresh()
        y, x = window.getmaxyx()
        pad.refresh(0, pad_x, 0, 0, y - 1, x - 1)

        while True:
            try:
                if poll.poll():
                    break
            except InterruptedError:
                break

        k = window.getch()
        if k == ord('q'):
            return

        if k == ord('e'):
            buf.message_driver = Sqlite3Driver('test.db', True)
        elif k == ord('a'):
            buf.message_driver = Sqlite3Driver('test.db')
        elif k == curses.KEY_NPAGE:
            buf.go_to_next_page()
        elif k == curses.KEY_PPAGE:
            buf.go_to_previous_page()
        elif k == curses.KEY_DOWN:
            buf.go_to_next_line()
        elif k == curses.KEY_UP:
            buf.go_to_previous_line()
        elif k == curses.KEY_RIGHT:
            pad_x = min(pad_x + 4, pad_x_max)
        elif k == curses.KEY_LEFT:
            pad_x = max(pad_x - 4, 0)
        elif k == curses.KEY_RESIZE:
            h, w = window.getmaxyx()
            buf.page_size = h
            pad.resize(h, MAX_WIDTH)
            pad_x_max = max(0, MAX_WIDTH - w)
            pad_x = min(pad_x, pad_x_max)

if __name__ == '__main__':
    curses.wrapper(run_app)
