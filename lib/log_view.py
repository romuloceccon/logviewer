import os
import sys
import select
import curses
import datetime
import struct

from screen_buffer import ScreenBuffer
from text_input import TextInput
from utf8_parser import Utf8Parser
from window import BaseManager
from window import Window, LogWindow, SelectWindow, TextWindow, DatetimeWindow
from window import FilterState

class EventPoll(object):
    def __init__(self):
        self._r, self._w = os.pipe()

        self._poll = select.epoll()
        self._poll.register(sys.stdin.fileno(), select.POLLIN)
        self._poll.register(self._r, select.POLLIN)

    def _notify(self):
        os.write(self._w, b'0')

    @property
    def observer(self):
        return self._notify

    def wait(self):
        while True:
            try:
                result_poll = self._poll.poll()
                if result_poll:
                    if result_poll[0][0] == self._r:
                        os.read(self._r, 256)
                    break
            except InterruptedError:
                break

class Manager(BaseManager):
    def __init__(self, curses, curses_window):
        BaseManager.__init__(self, curses, curses_window)
        self._poll = EventPoll()

    @property
    def poll(self):
        return self._poll

    def wait(self):
        return self._poll.wait()

class MainWindow(LogWindow):
    def __init__(self, window_manager, configuration):
        curses_window = window_manager.curses_window
        h, w = curses_window.getmaxyx()

        self._buf = ScreenBuffer(page_size=h - 1, timeout=configuration.timeout)
        self._buf.add_observer(window_manager.poll.observer)

        LogWindow.__init__(self, window_manager, self._buf, 500)

        self._driver_factory = configuration.get_factory()

    def _change_date(self):
        lines = self._buf.get_current_lines()
        dt = lines[0].datetime if len(lines) > 0 else datetime.datetime.utcnow()
        window = DatetimeWindow(self.window_manager, 'Date', dt)
        if window.show():
            self._restart_driver(window.value)

    def _change_level(self):
        window = LevelWindow(self.window_manager)
        window.position = self.filter_state.level
        if window.show():
            self.filter_state.level = window.position
            self._restart_driver()

    def _change_facility(self):
        window = FacilityWindow(self.window_manager)
        window.position = 0 if self.filter_state.facility is None else \
            self.filter_state.facility + 1
        if window.show():
            self.filter_state.facility = None if window.position == 0 else \
                window.position - 1
            self._restart_driver()

    def _change_host(self):
        window = TextWindow(self.window_manager, 'Host', 70)
        window.text = self.filter_state.host or ''
        if window.show():
            self.filter_state.host = window.text
            self._restart_driver()

    def _change_program(self):
        window = TextWindow(self.window_manager, 'Program', 70)
        window.text = self.filter_state.program or ''
        if window.show():
            self.filter_state.program = window.text
            self._restart_driver()

    def _restart_driver(self, start_date=None):
        options = {}

        if start_date:
            options['start_date'] = start_date
        else:
            lines = self._buf.get_current_lines()
            if len(lines) > 0:
                options['start_date'] = lines[0].datetime

        self._buf.restart(self._driver_factory.create_driver(
            self.filter_state, **options))

    def start(self):
        self._buf.start(self._driver_factory.create_driver(self.filter_state))

    def finish(self):
        self._buf.stop()

    def resize(self, h, w):
        LogWindow.resize(self, h, w)
        self._buf.page_size = h - 1

    def handle_key(self, k):
        if k == ord('q'):
            self.close(None)
        elif k == ord('d'):
            self._change_date()
        elif k == ord('l'):
            self._change_level()
        elif k == ord('f'):
            self._change_facility()
        elif k == ord('h'):
            self._change_host()
        elif k == ord('p'):
            self._change_program()
        elif k == curses.KEY_NPAGE:
            self._buf.go_to_next_page()
        elif k == curses.KEY_PPAGE:
            self._buf.go_to_previous_page()
        elif k == curses.KEY_DOWN:
            self._buf.go_to_next_line()
        elif k == curses.KEY_UP:
            self._buf.go_to_previous_line()
        elif k == curses.KEY_RIGHT:
            self.scroll_right()
        elif k == curses.KEY_LEFT:
            self.scroll_left()

class LevelWindow(SelectWindow):
    def __init__(self, window_manager):
        SelectWindow.__init__(self, window_manager, 'Level', ScreenBuffer.Line.LEVELS)

class FacilityWindow(SelectWindow):
    def __init__(self, window_manager):
        SelectWindow.__init__(self, window_manager, 'Facility',
            ['<ALL>'] + ScreenBuffer.Line.FACILITIES)
