import unittest
from unittest.mock import Mock, MagicMock, PropertyMock

from log_view import SelectWindow

class LogViewTest(unittest.TestCase):
    def setUp(self):
        self._pad = MagicMock()

        self._curses = MagicMock()
        self._curses.color_pair.return_value = 123
        self._curses.newpad.return_value = self._pad

        self._child_window = MagicMock()

        self._parent_window = MagicMock()
        self._parent_window.subwin.return_value = self._child_window

        self._manager = MagicMock()
        type(self._manager).curses_window = PropertyMock(return_value=self._parent_window)
        type(self._manager).curses = PropertyMock(return_value=self._curses)

    def test_should_create_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = SelectWindow(self._manager, 'Letter', ['a', 'b', 'c'])

        self._curses.newpad.assert_called_with(3, 16)
        self._parent_window.subwin.assert_called_with(7, 20, 1, 5)
        self._child_window.bkgd.assert_called_with(123)

    def test_should_create_window_not_perfectly_centerable(self):
        self._parent_window.getmaxyx.return_value = (8, 29)
        win = SelectWindow(self._manager, 'Letter', ['a', 'b', 'c'])

        self._parent_window.subwin.assert_called_with(7, 20, 0, 4)

    def test_should_squeeze_into_small_window(self):
        self._parent_window.getmaxyx.return_value = (5, 30)
        win = SelectWindow(self._manager, 'Letter', ['a', 'b', 'c'])

        self._parent_window.subwin.assert_called_with(5, 20, 0, 5)

    def test_should_not_create_too_small_window(self):
        self._parent_window.getmaxyx.return_value = (4, 30)
        win = SelectWindow(self._manager, 'Letter', ['a', 'b', 'c'])

        self.assertEqual(0, self._parent_window.subwin.call_count)

    def test_should_refresh_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = SelectWindow(self._manager, 'Letter', ['a', 'b', 'c'])

        win.refresh()
        self._child_window.clear.assert_called_with()
        self._child_window.border.assert_called_with()
        self._child_window.addstr.assert_called_with(0, 6, '|Letter|')
        self._child_window.noutrefresh.assert_called_with()
        self._pad.noutrefresh.assert_called_with(0, 0, 2, 2, 4, 17)
