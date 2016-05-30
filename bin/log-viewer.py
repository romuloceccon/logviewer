import curses

from log_view import EventPoll, MainWindow, LevelWindow

def run_app(window):
    curses.start_color()

    curses.curs_set(0)
    window.nodelay(1)

    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    poll = EventPoll()
    main_window = MainWindow(window, poll)
    dialog = None

    main_window.open()
    try:
        while True:
            main_window.refresh()
            if dialog:
                dialog.refresh()
            curses.doupdate()

            k = poll.wait_char(window)
            if k == ord('q'):
                return

            if k == ord('l') and not dialog:
                dialog = LevelWindow(window)
                continue

            if k == curses.KEY_RESIZE:
                main_window.resize()
                if dialog:
                    dialog.resize()
            elif dialog:
                if dialog.handle_key(k):
                    main_window.set_level(dialog.value)
                    dialog = None
            else:
                main_window.handle_key(k)
    finally:
        main_window.close()

if __name__ == '__main__':
    curses.wrapper(run_app)
