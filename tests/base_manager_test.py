import unittest
from unittest.mock import MagicMock

from logviewer.base_manager import *

class BaseManagerTest(unittest.TestCase):
    class FakeManager(BaseManager):
        def __init__(self, curses, curses_window):
            BaseManager.__init__(self, curses, curses_window)

        def wait(self):
            pass

    def _fake_getch(self):
        if self._getch_results:
            return self._getch_results.pop(0)
        return -1

    def setUp(self):
        self._getch_results = []
        self._curses = MagicMock()
        self._curses_window = MagicMock()
        self._curses_window.getch.side_effect = self._fake_getch
        self._window = MagicMock()
        self._manager = BaseManagerTest.FakeManager(self._curses,
            self._curses_window)

    def test_should_create_manager_without_window(self):
        self._manager.loop()

        self._curses_window.erase.assert_called_once_with()
        self._curses_window.noutrefresh.assert_called_once_with()
        self._curses.doupdate.assert_called_once_with()

    def test_should_refresh_one_window(self):
        self._manager.stack.append(self._window)

        self._manager.loop()

        self._window.refresh.assert_called_once_with()

    def test_should_refresh_two_windows(self):
        self._manager.stack.append(self._window)

        second_window = MagicMock()
        self._manager.stack.append(second_window)

        self._manager.loop()

        self._window.refresh.assert_called_once_with()
        second_window.refresh.assert_called_once_with()

    def test_should_not_handle_null_key(self):
        self._manager.stack.append(self._window)

        self._manager.loop()

        self.assertIsNone(self._window.handle_key.call_args)

    def test_should_handle_generic_key(self):
        self._manager.stack.append(self._window)

        self._getch_results.append(ord('q'))
        self._manager.loop()

        self._window.handle_key.assert_called_once_with(ord('q'))

    def test_should_handle_key_with_two_windows(self):
        self._manager.stack.append(self._window)

        second_window = MagicMock()
        self._manager.stack.append(second_window)

        self._getch_results.append(ord('q'))
        self._manager.loop()

        self.assertIsNone(self._window.handle_key.call_args)
        second_window.handle_key.assert_called_once_with(ord('q'))

    def test_should_handle_resize(self):
        self._manager.stack.append(self._window)

        second_window = MagicMock()
        self._manager.stack.append(second_window)

        self._curses_window.getmaxyx.return_value = (10, 20)
        self._getch_results.append(curses.KEY_RESIZE)
        self._manager.loop()

        self.assertIsNone(self._window.handle_key.call_args)
        self.assertIsNone(second_window.handle_key.call_args)
        self._window.resize.assert_called_once_with(10, 20)
        second_window.resize.assert_called_once_with(10, 20)

    def test_should_consume_getch_buffer_after_wait(self):
        self._manager.stack.append(self._window)

        self._getch_results.append(ord('a'))
        self._getch_results.append(ord('b'))
        self._manager.loop()

        self._window.refresh.assert_called_once_with()
        self.assertEqual([((ord('a'),),), ((ord('b'),),)],
            self._window.handle_key.call_args_list)
