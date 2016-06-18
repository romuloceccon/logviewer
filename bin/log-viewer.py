import os
import sys
import curses

from log_view import MainWindow, Manager
from configuration import Configuration
from sqlite3_driver import Sqlite3Driver

def run_app(window):
    manager = Manager(window)
    conf_file = sys.argv[1] if len(sys.argv) >= 2 else '/etc/logviewer.conf'
    drivers = { 'sqlite3': Sqlite3Driver.Factory }
    main_window = MainWindow(manager, Configuration(conf_file, drivers))
    manager.run(main_window)

if __name__ == '__main__':
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(run_app)
