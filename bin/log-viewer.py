import os
import curses

from log_view import EventPoll, MainWindow, LevelWindow, Manager

def run_app(window):
    manager = Manager(window)
    main_window = MainWindow(manager)
    manager.run(main_window)

if __name__ == '__main__':
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(run_app)
