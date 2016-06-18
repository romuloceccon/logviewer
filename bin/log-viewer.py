import os
import sys
import curses

from log_view import MainWindow, Manager
from configuration import Configuration

def get_drivers():
    result = {}
    try:
        import sqlite3_driver
        result['sqlite3'] = sqlite3_driver.Sqlite3Driver.Factory
    except ImportError:
        pass
    try:
        import mysql_driver
        result['mysql'] = mysql_driver.MySQLDriver.Factory
    except ImportError:
        pass
    return result

def run_app(window):
    manager = Manager(window)
    conf_file = sys.argv[1] if len(sys.argv) >= 2 else '/etc/logviewer.conf'
    main_window = MainWindow(manager, Configuration(conf_file, get_drivers()))
    manager.run(main_window)

if __name__ == '__main__':
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(run_app)
