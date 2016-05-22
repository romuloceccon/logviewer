import unittest
from unittest.mock import Mock, MagicMock

from screen_buffer import ScreenBuffer

class ScreenBufferTest(unittest.TestCase):
    def _get_line_range(self, begin, count, desc=True):
        result = [{ 'id': i, 'message': str(i) } for i in range(begin, begin + count)]
        if desc:
            result.reverse()
        return result

    def test_should_initialize_screen_buffer(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg, step_size=2, buffer_size=5, low_buffer_threshold=2)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('99', cur[0].message)
        self.assertEqual('100', cur[1].message)

        msg.get_records.assert_called_once_with(None, True, 7)

    def test_should_initialize_screen_buffer_with_less_lines_than_buffer_size(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(1, 3))

        buf = ScreenBuffer(msg, step_size=2, buffer_size=10)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_initialize_screen_buffer_with_defaults(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(91, 10))

        buf = ScreenBuffer(msg, step_size=10)

        self.assertEqual(50, buf._buffer_size)
        self.assertEqual(10, buf._low_buffer_threshold)

    def test_should_move_buffer_backward(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg, step_size=2, buffer_size=5, low_buffer_threshold=2)

        buf.move_backward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('97', cur[0].message)
        self.assertEqual('98', cur[1].message)

        msg.get_records.assert_called_once_with(None, True, 7)

    def test_should_move_backward_after_initializing_with_less_lines_than_step_size(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(2, 1)
        buf = ScreenBuffer(msg, step_size=2, buffer_size=5, low_buffer_threshold=2)

        msg.get_records.return_value = self._get_line_range(1, 1)
        buf.move_backward()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)

    def test_should_move_buffer_forward(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg, step_size=2, buffer_size=5, low_buffer_threshold=0)

        buf.move_backward()
        buf.move_backward()
        buf.move_forward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('97', cur[0].message)
        self.assertEqual('98', cur[1].message)

        msg.get_records.assert_called_once_with(None, True, 7)

    def test_should_move_forward_without_new_records(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(95, 6)
        buf = ScreenBuffer(msg, step_size=2)

        msg.get_records.return_value = []
        buf.move_forward()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('99', cur[0].message)

    def test_should_get_more_records_when_buffer_is_low_moving_backward(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(93, 8)
        buf = ScreenBuffer(msg, step_size=2, buffer_size=6, low_buffer_threshold=2)

        buf.move_backward()

        msg.get_records.return_value = self._get_line_range(87, 6)
        buf.move_backward()

        self.assertEqual(2, msg.get_records.call_count)
        self.assertEqual((None, True, 8), msg.get_records.call_args_list[0][0])
        self.assertEqual((93, True, 6), msg.get_records.call_args_list[1][0])
        msg.get_records.reset_mock()

        buf.move_backward()
        buf.move_backward()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('91', cur[0].message)

        msg.get_records.assert_not_called()

    def test_should_get_more_records_when_buffer_is_low_moving_forward(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(91, 10)
        buf = ScreenBuffer(msg, step_size=2, buffer_size=8, low_buffer_threshold=2)

        buf.move_backward()
        buf.move_backward()

        msg.get_records.return_value = self._get_line_range(101, 8, False)
        # After the next call position would be at 97. More records need to be
        # fetched because there would be only two lines past the current window
        # (99 and 100).
        buf.move_forward()

        self.assertEqual(2, msg.get_records.call_count)
        self.assertEqual((None, True, 10), msg.get_records.call_args_list[0][0])
        self.assertEqual((100, False, 8), msg.get_records.call_args_list[1][0])
        msg.get_records.reset_mock()

        buf.move_forward()
        buf.move_forward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('101', cur[0].message)

        msg.get_records.assert_not_called()
