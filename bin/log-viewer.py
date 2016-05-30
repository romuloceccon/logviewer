import curses
import datetime

from screen_buffer import ScreenBuffer
from sqlite3_driver import Sqlite3Driver
from log_view import EventPoll, MainWindow

def run_app(window):
    curses.curs_set(0)
    window.nodelay(1)

    poll = EventPoll(window)
    screen = MainWindow(window)

    buf = ScreenBuffer(page_size=window.getmaxyx()[0])
    buf.add_observer(poll.observer)

    buf.start(Sqlite3Driver('test.db'))
    try:
        while True:
            screen.update(buf.get_current_lines())

            k = poll.wait_char()
            if k == ord('q'):
                return

            elif k == curses.KEY_NPAGE:
                buf.go_to_next_page()
            elif k == curses.KEY_PPAGE:
                buf.go_to_previous_page()
            elif k == curses.KEY_DOWN:
                buf.go_to_next_line()
            elif k == curses.KEY_UP:
                buf.go_to_previous_line()
            elif k == curses.KEY_RIGHT:
                screen.go_right()
            elif k == curses.KEY_LEFT:
                screen.go_left()
            elif k == curses.KEY_RESIZE:
                buf.page_size = window.getmaxyx()[0]
                screen.resize()
    finally:
        buf.stop()

if __name__ == '__main__':
    curses.wrapper(run_app)
