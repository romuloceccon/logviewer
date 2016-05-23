import unittest
from unittest.mock import Mock, MagicMock

from screen_buffer import ScreenBuffer

class ScreenBufferTest(unittest.TestCase):
    class FakeDriver(object):
        def __init__(self, last_id):
            self._last_id = last_id
            self._calls = []

        @property
        def calls(self):
            return self._calls

        @property
        def last_id(self):
            return self._last_id

        @last_id.setter
        def last_id(self, val):
            self._last_id = val

        def get_records(self, start, desc, count):
            self._calls.append((start, desc, count))

            if start is None:
                r = range(self._last_id, max(self._last_id - count + 1, 0) - 1, -1)
            elif desc:
                r = range(start - 1, max(start - count, 0) - 1, -1)
            else:
                r = range(start + 1, min(start + count, self._last_id) + 1)

            return [{ 'id': i, 'message': str(i) } for i in r]

    def _get_line_range(self, begin, count, desc=True):
        result = [{ 'id': i, 'message': str(i) } for i in range(begin, begin + count)]
        if desc:
            result.reverse()
        return result

    def test_should_initialize_screen_buffer(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, low_buffer_threshold=2)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('99', cur[0].message)
        self.assertEqual('100', cur[1].message)

        msg.get_records.assert_called_once_with(None, True, 7)

    def test_should_initialize_screen_buffer_with_less_lines_than_buffer_size(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(1, 3))

        buf = ScreenBuffer(msg, page_size=2, buffer_size=10)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_initialize_screen_buffer_with_defaults(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(91, 10))

        buf = ScreenBuffer(msg, page_size=10)

        self.assertEqual(50, buf._buffer_size)
        self.assertEqual(10, buf._low_buffer_threshold)

    def test_should_go_to_previous_line(self):
        msg = ScreenBufferTest.FakeDriver(100)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.go_to_previous_line()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('98', cur[0].message)

    def test_should_go_to_next_line(self):
        msg = ScreenBufferTest.FakeDriver(100)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.go_to_previous_line()
        msg.last_id = 110
        buf.go_to_next_line()
        buf.go_to_next_line()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('100', cur[0].message)

    def test_should_go_to_previous_page(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, low_buffer_threshold=2)

        buf.go_to_previous_page()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('97', cur[0].message)
        self.assertEqual('98', cur[1].message)

        msg.get_records.assert_called_once_with(None, True, 7)

    def test_should_go_to_previous_page_after_initializing_with_less_lines_than_page_size(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(2, 1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, low_buffer_threshold=2)

        msg.get_records.return_value = self._get_line_range(1, 1)
        buf.go_to_previous_page()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)

    def test_should_go_to_next_page(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, low_buffer_threshold=0)

        buf.go_to_previous_page()
        buf.go_to_previous_page()
        buf.go_to_next_page()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('97', cur[0].message)
        self.assertEqual('98', cur[1].message)

        msg.get_records.assert_called_once_with(None, True, 7)

    def test_should_go_to_next_page_without_new_records(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(95, 6)
        buf = ScreenBuffer(msg, page_size=2)

        msg.get_records.return_value = []
        buf.go_to_next_page()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('99', cur[0].message)

    def test_should_get_more_records_when_buffer_is_low_going_to_previous_page(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(93, 8)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=6, low_buffer_threshold=2)

        buf.go_to_previous_page()

        msg.get_records.return_value = self._get_line_range(87, 6)
        buf.go_to_previous_page()

        self.assertEqual(2, msg.get_records.call_count)
        self.assertEqual((None, True, 8), msg.get_records.call_args_list[0][0])
        self.assertEqual((93, True, 6), msg.get_records.call_args_list[1][0])
        msg.get_records.reset_mock()

        buf.go_to_previous_page()
        buf.go_to_previous_page()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('91', cur[0].message)

        msg.get_records.assert_not_called()

    def test_should_get_more_records_when_buffer_is_low_going_to_next_page(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(91, 10)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=8, low_buffer_threshold=2)

        buf.go_to_previous_page()
        buf.go_to_previous_page()

        msg.get_records.return_value = self._get_line_range(101, 8, False)
        # After the next call position would be at 97. More records need to be
        # fetched because there would be only two lines past the current window
        # (99 and 100).
        buf.go_to_next_page()

        self.assertEqual(2, msg.get_records.call_count)
        self.assertEqual((None, True, 10), msg.get_records.call_args_list[0][0])
        self.assertEqual((100, False, 8), msg.get_records.call_args_list[1][0])
        msg.get_records.reset_mock()

        buf.go_to_next_page()
        buf.go_to_next_page()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('101', cur[0].message)

        msg.get_records.assert_not_called()

    def test_should_change_page_size_at_end_of_buffer(self):
        msg = ScreenBufferTest.FakeDriver(100)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.page_size = 3
        cur = buf.get_current_lines()
        self.assertEqual(3, len(cur))
        self.assertEqual('98', cur[0].message)

        self.assertEqual([(None, True, 7), (100, False, 5)], msg.calls)

    def test_should_change_page_size_before_end_of_buffer(self):
        msg = ScreenBufferTest.FakeDriver(100)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.go_to_previous_page()
        buf.page_size = 3
        cur = buf.get_current_lines()
        self.assertEqual(3, len(cur))
        self.assertEqual('97', cur[0].message)

        self.assertEqual([(None, True, 7), (100, False, 5)], msg.calls)

    def test_should_get_more_records_if_buffer_is_low_for_new_page_size(self):
        msg = ScreenBufferTest.FakeDriver(100)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=2)

        msg.last_id = 110
        buf.page_size = 3

        self.assertEqual([(None, True, 4), (97, True, 2), (100, False, 2)], msg.calls)

    def test_should_change_message_driver_after_initialize(self):
        msg = ScreenBufferTest.FakeDriver(100)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.message_driver = ScreenBufferTest.FakeDriver(200)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('199', cur[0].message)
