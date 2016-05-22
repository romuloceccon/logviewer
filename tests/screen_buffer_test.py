import unittest
from unittest.mock import Mock, MagicMock

from screen_buffer import ScreenBuffer

class ScreenBufferTest(unittest.TestCase):
    def _get_line_range(self, begin, count):
        return [{ 'id': i, 'message': str(i) } for i in range(begin, begin + count)]

    def test_should_initialize_screen_buffer(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('99', cur[0].message)
        self.assertEqual('100', cur[1].message)

        msg.get_records.assert_called_once_with(None, False, 7)

    def test_should_move_buffer_backward(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg)

        buf.move_backward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('97', cur[0].message)
        self.assertEqual('98', cur[1].message)

        msg.get_records.assert_called_once_with(None, False, 7)

    def test_should_move_buffer_forward(self):
        msg = MagicMock()
        msg.get_records = Mock(return_value=self._get_line_range(94, 7))

        buf = ScreenBuffer(msg)

        buf.move_backward()
        buf.move_forward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('99', cur[0].message)
        self.assertEqual('100', cur[1].message)

        msg.get_records.assert_called()
        self.assertEqual((None, False, 7), msg.get_records.call_args_list[0][0])

    def test_should_get_more_records_when_buffer_is_low_moving_backward(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(94, 7)
        buf = ScreenBuffer(msg)

        buf.move_backward()

        msg.get_records.return_value = self._get_line_range(89, 5)
        buf.move_backward()

        self.assertEqual(2, msg.get_records.call_count)
        self.assertEqual((None, False, 7), msg.get_records.call_args_list[0][0])
        self.assertEqual((94, True, 5), msg.get_records.call_args_list[1][0])
        msg.get_records.reset_mock()

        buf.move_backward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('93', cur[0].message)

        msg.get_records.assert_not_called()

    def test_should_get_more_records_when_buffer_is_low_moving_forward(self):
        msg = MagicMock()
        msg.get_records = Mock()

        msg.get_records.return_value = self._get_line_range(94, 7)
        buf = ScreenBuffer(msg)

        buf.move_backward()

        msg.get_records.return_value = self._get_line_range(101, 5)
        buf.move_forward()

        self.assertEqual(2, msg.get_records.call_count)
        self.assertEqual((None, False, 7), msg.get_records.call_args_list[0][0])
        self.assertEqual((100, False, 5), msg.get_records.call_args_list[1][0])
        msg.get_records.reset_mock()

        buf.move_forward()
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('101', cur[0].message)

        msg.get_records.assert_not_called()
