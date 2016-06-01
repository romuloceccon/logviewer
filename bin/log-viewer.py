import os
import curses

from log_view import MainWindow, Manager
from sqlite3_driver import Sqlite3Driver

def run_app(window):
    manager = Manager(window)
    main_window = MainWindow(manager, Sqlite3Driver.Factory('test.db'))
    manager.run(main_window)

if __name__ == '__main__':
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(run_app)
