import unittest
from unittest.mock import Mock, MagicMock, PropertyMock

import curses

from logviewer.screen_buffer import ScreenBuffer
from logviewer.windows import *

class BaseTest(unittest.TestCase):
    def setUp(self):
        self._curses = MagicMock()
        type(self._curses).A_REVERSE = PropertyMock(return_value=0x100)
        type(self._curses).A_BOLD = PropertyMock(return_value=0x200)
        self._curses.color_pair.side_effect = self._color_pair

        self._child_window = MagicMock()

        self._parent_window = MagicMock()
        self._parent_window.subwin.return_value = self._child_window

        self._manager = MagicMock()
        type(self._manager).curses_window = PropertyMock(return_value=self._parent_window)
        type(self._manager).curses = PropertyMock(return_value=self._curses)

    def _color_pair(self, arg):
        return arg

class LogTest(BaseTest):
    class FakeBuffer(object):
        def __init__(self, lines):
            self._lines = []
            dt = datetime.datetime(2016, 6, 4)
            for i, (line, is_continuation) in enumerate(lines):
                data = { 'id': i + 1, 'datetime': dt, 'host': 'test',
                    'program': 'example', 'facility_num': 0, 'level_num': 7,
                    'message': 'test message' }
                data.update(line)
                self._lines.append(ScreenBuffer.Line(data, is_continuation))

        def get_current_lines(self):
            return self._lines

    def setUp(self):
        BaseTest.setUp(self)

        self._pad = MagicMock()
        self._curses.newpad.return_value = self._pad

    def test_should_create_window(self):
        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, None, 200)

        self._curses.newpad.assert_called_with(9, 201)

    def test_should_resize_window(self):
        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, None, 200)

        win.resize(20, 40)
        self._pad.resize.assert_called_once_with(19, 201)

    def test_should_scroll_right(self):
        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, None, 36)

        self.assertEqual(0, win._pad_x)
        win.scroll_right()
        self.assertEqual(4, win._pad_x)
        win.scroll_right()
        self.assertEqual(6, win._pad_x)

    def test_should_scroll_left(self):
        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, None, 36)

        win.scroll_right()
        win.scroll_right()
        win.scroll_left()
        self.assertEqual(2, win._pad_x)
        win.scroll_left()
        self.assertEqual(0, win._pad_x)

    def test_should_update_pad_offset_after_resize(self):
        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, None, 36)

        win.scroll_right()
        win.scroll_right()

        win.resize(10, 32)
        self.assertEqual(4, win._pad_x)

    def test_should_draw_simple_debug_line(self):
        buf = LogTest.FakeBuffer([({}, False)])

        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, buf, 100)

        win.refresh()
        self._pad.erase.assert_called_once_with()
        self._pad.noutrefresh.assert_called_once_with(0, 0, 0, 0, 8, 29)

        self.assertEqual([
            ((0, 0, '06-04 00:00:00', 14, 0),),
            ((0, 15, 'test', 8, 0),),
            ((0, 24, 'example', 16, 0),),
            ((0, 41, 'KERN', 4, 0),),
            ((0, 46, 'DEBUG', 3, 0x206),),
            ((0, 50, 'test message', 50, 0),)], self._pad.addnstr.call_args_list)

    def test_should_draw_status_bar(self):
        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, LogTest.FakeBuffer([]), 100)

        win.refresh()
        self._parent_window.addnstr.assert_called_once_with(9, 0, ' [l]evel: '\
            'debug  [f]acility: ALL  [p]rogram: *  [h]ost: *  Go to [d]ate', 29)
        self._parent_window.chgat.assert_called_once_with(9, 0, 30, 0x300)
        self._parent_window.noutrefresh.assert_called_once_with()

    def test_should_draw_continuation_line(self):
        buf = LogTest.FakeBuffer([({}, False), ({}, True)])

        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, buf, 100)

        win.refresh()
        self.assertEqual([
            ((0, 0, '06-04 00:00:00', 14, 0),),
            ((0, 15, 'test', 8, 0),),
            ((0, 24, 'example', 16, 0),),
            ((0, 41, 'KERN', 4, 0),),
            ((0, 46, 'DEBUG', 3, 0x206),),
            ((0, 50, 'test message', 50, 0),),
            ((1, 50, 'test message', 50, 0),)], self._pad.addnstr.call_args_list)

    def test_should_draw_continuation_line_at_first_row(self):
        buf = LogTest.FakeBuffer([({}, True)])

        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, buf, 100)

        win.refresh()
        self.assertEqual([
            ((0, 0, '06-04 00:00:00', 14, 0),),
            ((0, 15, 'test', 8, 0),),
            ((0, 24, 'example', 16, 0),),
            ((0, 41, 'KERN', 4, 0),),
            ((0, 46, 'DEBUG', 3, 0x206),),
            ((0, 50, 'test message', 50, 0),)], self._pad.addnstr.call_args_list)

    def test_should_draw_line_on_scrolled_window(self):
        buf = LogTest.FakeBuffer([({}, True)])

        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, buf, 100)

        win.scroll_right()
        win.refresh()
        self._pad.noutrefresh.assert_called_once_with(0, 4, 0, 0, 8, 29)

    def test_should_draw_alert_line(self):
        buf = LogTest.FakeBuffer([({ 'level_num': 1 }, True)])

        self._parent_window.getmaxyx.return_value = (10, 30)
        win = Log(self._manager, buf, 100)

        win.refresh()
        self.assertEqual(((0, 46, 'ALERT', 3, 0x101),),
            self._pad.addnstr.call_args_list[4])

class CenteredTest(BaseTest):
    def test_should_create_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Centered(self._manager, 'Test', 3, 16, 1, 6)

        self._parent_window.subwin.assert_called_with(7, 20, 1, 5)
        self._child_window.bkgd.assert_called_with(256)

    def test_should_squeeze_into_small_window(self):
        self._parent_window.getmaxyx.return_value = (5, 30)
        win = Centered(self._manager, 'Test', 3, 16, 1, 6)

        self._parent_window.subwin.assert_called_with(5, 20, 0, 5)

    def test_should_create_window_not_perfectly_centerable(self):
        self._parent_window.getmaxyx.return_value = (8, 29)
        win = Centered(self._manager, 'Test', 3, 16, 1, 6)

        self._parent_window.subwin.assert_called_with(7, 20, 0, 4)

    def test_should_not_create_too_small_window(self):
        self._parent_window.getmaxyx.return_value = (4, 30)
        win = Centered(self._manager, 'Test', 3, 16, 1, 6)

        self.assertEqual(0, self._parent_window.subwin.call_count)

    def test_should_refresh_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Centered(self._manager, 'Test', 3, 16, 1, 6)

        win.refresh()
        self._child_window.erase.assert_called_with()
        self._child_window.border.assert_called_with()
        self._child_window.addstr.assert_called_with(0, 7, '|Test|')
        self._child_window.noutrefresh.assert_called_with()

    def test_should_not_refresh_invisible_window(self):
        self._parent_window.getmaxyx.return_value = (4, 30)
        win = Centered(self._manager, 'Test', 3, 16, 1, 6)

        win.refresh()
        self._child_window.clear.assert_not_called()

class SelectTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)

        self._pad = MagicMock()
        self._curses.newpad.return_value = self._pad

    def test_should_create_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        self._curses.newpad.assert_called_with(3, 16)
        self._parent_window.subwin.assert_called_with(7, 20, 1, 5)
        self._child_window.bkgd.assert_called_with(256)
        self._pad.bkgd.assert_called_with(256)

    def test_should_not_create_empty_window(self):
        self.assertRaises(ValueError, Select, self._manager, 'x', [])

    def test_should_refresh_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.refresh()
        self._child_window.erase.assert_called_with()
        self._child_window.border.assert_called_with()
        self._child_window.addstr.assert_called_with(0, 6, '|Letter|')
        self._child_window.noutrefresh.assert_called_with()
        self.assertEqual([((0, 0, '▶a', 20),), ((1, 0, ' b', 20),),
            ((2, 0, ' c', 20),)], self._pad.addnstr.call_args_list)
        self._pad.noutrefresh.assert_called_with(0, 0, 3, 7, 5, 22)

    def test_should_change_position(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.position = 2
        win.refresh()
        self.assertEqual([((0, 0, ' a', 20),), ((1, 0, ' b', 20),),
            ((2, 0, '▶c', 20),)], self._pad.addnstr.call_args_list)

    def test_should_not_set_invalid_position(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        self.assertRaises(IndexError, setattr, win, 'position', -1)
        self.assertRaises(IndexError, setattr, win, 'position', 3)

    def test_should_move_pad_down_if_position_would_be_off_of_screen(self):
        self._parent_window.getmaxyx.return_value = (6, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c', 'd'])

        win.position = 2
        win.refresh()
        self._pad.noutrefresh.assert_called_with(1, 0, 2, 7, 3, 22)

    def test_should_handle_key_down(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.handle_key(curses.KEY_DOWN)
        self.assertEqual(1, win.position)

    def test_should_handle_key_down_at_end_of_screen(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.handle_key(curses.KEY_DOWN)
        win.handle_key(curses.KEY_DOWN)
        win.handle_key(curses.KEY_DOWN)
        self.assertEqual(2, win.position)

    def test_should_handle_key_up(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.handle_key(curses.KEY_DOWN)
        win.handle_key(curses.KEY_UP)
        self.assertEqual(0, win.position)

    def test_should_handle_carriage_return(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.handle_key(10)
        self.assertTrue(win.closed)
        self.assertTrue(win.result)

    def test_should_handle_escape(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Select(self._manager, 'Letter', ['a', 'b', 'c'])

        win.handle_key(27)
        self.assertTrue(win.closed)
        self.assertFalse(win.result)

class TextTest(BaseTest):
    def test_should_create_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Text(self._manager, 'Test', 19)

        self._parent_window.subwin.assert_called_with(5, 24, 2, 3)
        self._child_window.bkgd.assert_called_with(256)

    def test_should_start_and_stop_cursor(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Text(self._manager, 'Test', 19)

        win.start()
        win.finish()

        self.assertEqual([((1,),), ((0,),)],
            self._curses.curs_set.call_args_list)

    def test_should_refresh_empty_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Text(self._manager, 'Test', 19)

        win.refresh()

        self.assertEqual([((0, 9, '|Test|'),), ((2, 2, ''),)],
            self._child_window.addstr.call_args_list)
        self.assertEqual([((2, 2),), ((2, 2),)],
            self._child_window.move.call_args_list)
        self.assertEqual([((2, 2, 20, 0),)],
            self._child_window.chgat.call_args_list)

    def test_should_refresh_window_with_text(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Text(self._manager, 'Test', 19)

        win.text = 'test text'
        win.refresh()

        self.assertEqual([((0, 9, '|Test|'),), ((2, 2, 'test text'),)],
            self._child_window.addstr.call_args_list)
        self.assertEqual([((2, 2),), ((2, 11),)],
            self._child_window.move.call_args_list)

    def test_should_refresh_narrow_text_window(self):
        self._parent_window.getmaxyx.return_value = (9, 20)
        win = Text(self._manager, 'Test', 19)

        win.text = 'a longer test text'
        win.refresh()

        self.assertEqual([((0, 7, '|Test|'),), ((2, 2, 'onger test text'),)],
            self._child_window.addstr.call_args_list)

    def test_should_handle_key_after_text_change(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Text(self._manager, 'Test', 19)

        win.text = 'test text'
        win.handle_key(ord('x'))
        self.assertEqual('test textx', win.text)

class DatetimeTest(BaseTest):
    def test_should_create_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        win = Datetime(self._manager, 'Date', datetime.datetime.utcnow())

        self._parent_window.subwin.assert_called_with(5, 23, 2, 3)
        self._child_window.bkgd.assert_called_with(256)

    def test_should_refresh_window(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        dt = datetime.datetime(2016, 6, 27, 21, 45, 47)

        win = Datetime(self._manager, 'Date', dt)
        win.refresh()

        self.assertEqual([((0, 8, '|Date|'),), ((2, 2, '2016-06-27 21:45:47'),)],
            self._child_window.addstr.call_args_list)
        self._child_window.chgat.assert_called_once_with(2, 2, 4, 0)
        self._child_window.noutrefresh.assert_called_with()

    def test_should_handle_key_right(self):
        self._parent_window.getmaxyx.return_value = (9, 30)

        win = Datetime(self._manager, 'Date', datetime.datetime.utcnow())
        win.handle_key(curses.KEY_RIGHT)
        win.refresh()

        self._child_window.chgat.assert_called_once_with(2, 7, 2, 0)

    def test_should_handle_key_left(self):
        self._parent_window.getmaxyx.return_value = (9, 30)

        win = Datetime(self._manager, 'Date', datetime.datetime.utcnow())
        win.handle_key(curses.KEY_RIGHT)
        win.handle_key(curses.KEY_LEFT)
        win.refresh()

        self._child_window.chgat.assert_called_once_with(2, 2, 4, 0)

    def test_should_handle_key_up(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        dt = datetime.datetime(2016, 6, 27, 22, 6, 28)

        win = Datetime(self._manager, 'Date', dt)
        win.handle_key(curses.KEY_UP)
        win.refresh()

        self.assertEqual([((0, 8, '|Date|'),), ((2, 2, '2017-06-27 22:06:28'),)],
            self._child_window.addstr.call_args_list)

    def test_should_handle_key_down(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        dt = datetime.datetime(2016, 6, 27, 22, 7, 41)

        win = Datetime(self._manager, 'Date', dt)
        win.handle_key(curses.KEY_DOWN)
        win.refresh()

        self.assertEqual([((0, 8, '|Date|'),), ((2, 2, '2015-06-27 22:07:41'),)],
            self._child_window.addstr.call_args_list)

    def test_should_return_current_value(self):
        self._parent_window.getmaxyx.return_value = (9, 30)
        dt = datetime.datetime(2016, 6, 28, 0, 20, 46)

        win = Datetime(self._manager, 'Date', dt)
        win.handle_key(curses.KEY_DOWN)
        self.assertEqual(dt.replace(year=2015), win.value)
