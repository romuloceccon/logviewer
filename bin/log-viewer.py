import os
import sys
import curses

from logviewer.application import MainWindow, Manager
from logviewer.configuration import Configuration

def get_drivers():
    result = {}
    try:
        import logviewer.sqlite3_driver as sqlite3_driver
        result['sqlite3'] = sqlite3_driver.SQLite3Driver.Factory
    except ImportError:
        pass
    try:
        import logviewer.mysql_driver as mysql_driver
        result['mysql'] = mysql_driver.MySQLDriver.Factory
    except ImportError:
        pass
    return result

def run_app(window):
    manager = Manager(curses, window)
    conf_file = sys.argv[1] if len(sys.argv) >= 2 else '/etc/logviewer.conf'
    main_window = MainWindow(manager, Configuration(conf_file, get_drivers()))
    manager.run(main_window)

if __name__ == '__main__':
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(run_app)
