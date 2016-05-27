import unittest
import threading
import random
from unittest.mock import Mock, MagicMock

from screen_buffer import ScreenBuffer

class ScreenBufferTest(unittest.TestCase):
    class Observer(object):
        def __init__(self):
            self._count = 0

        @property
        def count(self):
            return self._count

        def notify(self):
            self._count += 1

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

            return [{ 'id': i, 'datetime': '2016-05-22 23:00:00', 'host': 'test',
                'program': 'test', 'facility': 'user', 'level': 'info',
                'message': str(i) } for i in r]

    class FakeDriver2(ScreenBuffer.Driver):
        def __init__(self, recs):
            self.started = threading.Event()
            self.stopped = False
            self.recs = recs
            self.magic = random.randint(1, 1000)
            self.count = threading.Semaphore(0)
            self.error = False
            self.instruction = None

        def start_connection(self):
            self.started.set()

        def stop_connection(self):
            self.stopped = True

        def prepare_query(self, start, desc, count):
            self.instruction = (start, desc, count)
            return self.magic

        def fetch_record(self, query):
            if query != self.magic:
                self.error = True
            self.count.release()
            if len(self.recs) > 0:
                i = self.recs[0]
                del self.recs[0]
                result = { 'id': i, 'datetime': '2016-05-22 23:00:00',
                    'host': 'test', 'program': 'test', 'facility': 'user',
                    'level': 'info', 'message': str(i) }
                return result

    def _get_line(self, i, message=None):
        return { 'id': i, 'datetime': '2016-05-22 23:00:00', 'host': 'test',
            'program': 'test', 'facility': 'user', 'level': 'info',
            'message': message is None and str(i) or message }

    def _get_line_range(self, begin, count, desc=True):
        result = [self._get_line(i) for i in range(begin, begin + count)]
        if desc:
            result.reverse()
        return result

    def setUp(self):
        self.observer = ScreenBufferTest.Observer()

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

    def test_should_get_multi_line_records(self):
        lines = self._get_line_range(91, 10)
        lines[0]['message'] = '100/1\n100/2\n100/3'

        msg = MagicMock()
        msg.get_records = Mock(return_value=lines)

        buf = ScreenBuffer(msg, page_size=4, buffer_size=10)

        cur = buf.get_current_lines()
        self.assertEqual(4, len(cur))
        self.assertEqual('99', cur[0].message)
        self.assertEqual(False, cur[0].is_continuation)
        self.assertEqual('100/1', cur[1].message)
        self.assertEqual(False, cur[1].is_continuation)
        self.assertEqual('100/2', cur[2].message)
        self.assertEqual(True, cur[2].is_continuation)
        self.assertEqual('100/3', cur[3].message)
        self.assertEqual(True, cur[3].is_continuation)

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

    def test_should_prepend_record_on_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)
        buf.add_observer(self.observer.notify)

        buf.prepend_record(self._get_line(2))
        self.assertEqual(1, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('2', cur[0].message)

    def test_should_prepend_record_on_non_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)
        buf.add_observer(self.observer.notify)

        buf.prepend_record(self._get_line(2))
        buf.prepend_record(self._get_line(1))
        self.assertEqual(2, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('2', cur[1].message)

    def test_should_prepend_record_on_off_screen_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(3))
        buf.prepend_record(self._get_line(2))

        buf.add_observer(self.observer.notify)
        buf.prepend_record(self._get_line(1))
        self.assertEqual(0, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_append_record_on_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.add_observer(self.observer.notify)
        buf.append_record(self._get_line(2))
        self.assertEqual(1, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('2', cur[0].message)

    def test_should_append_record_on_non_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.append_record(self._get_line(2))
        buf.append_record(self._get_line(3))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_append_record_past_end_of_screen(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.append_record(self._get_line(2))
        buf.append_record(self._get_line(3))

        buf.add_observer(self.observer.notify)
        buf.append_record(self._get_line(4))
        self.assertEqual(0, self.observer.count)

    def test_should_prepend_record_on_buffer_not_at_end_of_screen(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.append_record(self._get_line(2))
        buf.append_record(self._get_line(3))
        buf.append_record(self._get_line(4))
        buf.prepend_record(self._get_line(1))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_prepend_multi_line_record_on_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(1, 'a\nb'))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('a', cur[0].message)
        self.assertEqual(False, cur[0].is_continuation)
        self.assertEqual('b', cur[1].message)
        self.assertEqual(True, cur[1].is_continuation)

    def test_should_prepend_multi_line_record_on_non_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(3))
        buf.prepend_record(self._get_line(2))
        buf.prepend_record(self._get_line(1, 'a\nb'))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_append_multi_line_record(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.append_record(self._get_line(1))
        buf.append_record(self._get_line(2, 'a\nb'))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('a', cur[1].message)

    def test_should_stop_observing(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.add_observer(self.observer.notify)
        buf.prepend_record(self._get_line(2))
        buf.remove_observer(self.observer.notify)
        buf.prepend_record(self._get_line(1))
        self.assertEqual(1, self.observer.count)

    def test_should_go_to_previous_line(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.go_to_previous_line2()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('8', cur[0].message)

    def test_should_go_to_next_line(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10):
            buf.append_record(self._get_line(i + 1))

        buf.go_to_next_line2()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)

    def test_should_go_to_previous_page(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.go_to_previous_page2()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('7', cur[0].message)
        self.assertEqual('8', cur[1].message)

    def test_should_go_to_previous_page_with_less_lines_than_page_size(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(1))

        buf.go_to_previous_page2()

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('1', cur[0].message)

    def test_should_go_to_next_page(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10):
            buf.append_record(self._get_line(i + 1))

        buf.go_to_next_page2()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('3', cur[0].message)

    def test_should_go_to_next_page_with_less_lines_than_page_size(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.append_record(self._get_line(1))

        buf.go_to_next_page2()

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('1', cur[0].message)

    def test_should_change_page_size_at_end_of_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.page_size = 3
        cur = buf.get_current_lines()
        self.assertEqual(3, len(cur))
        self.assertEqual('8', cur[0].message)

    def test_should_change_page_size_before_end_of_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.go_to_previous_page2()
        buf.page_size = 3

        cur = buf.get_current_lines()
        self.assertEqual(3, len(cur))
        self.assertEqual('7', cur[0].message)

    def test_should_get_buffer_instructions_for_empty_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        self.assertEqual(((None, True, 7),), buf.get_buffer_instructions())

    def test_should_get_buffer_instructions_for_forward_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        self.assertEqual(((10, False, 5),), buf.get_buffer_instructions())

    def test_should_not_get_buffer_instructions_for_forward_buffer_if_below_threshold(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))
        buf.go_to_previous_line2()
        buf.go_to_previous_line2()
        buf.go_to_previous_line2()

        self.assertEqual(tuple(), buf.get_buffer_instructions())

    def test_should_get_buffer_instructions_for_backward_buffer(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 20):
            buf.append_record(self._get_line(i + 1))

        self.assertEqual(((11, True, 5),), buf.get_buffer_instructions())

    def test_should_not_get_buffer_instructions_for_backward_buffer_if_below_threshold(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        for i in range(10, 20):
            buf.append_record(self._get_line(i + 1))
        buf.go_to_next_line2()
        buf.go_to_next_line2()
        buf.go_to_next_line2()

        self.assertEqual(tuple(), buf.get_buffer_instructions())

    def test_should_get_buffer_instructions_if_both_buffers_are_below_threshold(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5)

        buf.append_record(self._get_line(11))
        buf.append_record(self._get_line(12))

        self.assertEqual(((12, False, 5), (11, True, 5)), buf.get_buffer_instructions())

    def test_should_start_and_stop_driver(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        drv = ScreenBufferTest.FakeDriver2([])
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, message_driver2=drv)

        drv.started.wait()
        buf.stop()
        self.assertTrue(drv.stopped)

    def test_should_fetch_records_in_descending_order(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        drv = ScreenBufferTest.FakeDriver2([2, 1])
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, message_driver2=drv)

        # wait for the two recs *and* the last call to fetch_record, which will
        # return None
        for x in range(3):
            drv.count.acquire()

        cur = buf.get_current_lines()
        buf.stop()
        self.assertTrue(drv.stopped)
        self.assertFalse(drv.error)
        self.assertEqual((None, True, 7), drv.instruction)

        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('2', cur[1].message)

    def test_should_fetch_records_in_ascending_order(self):
        msg = ScreenBufferTest.FakeDriver(-1)
        drv = ScreenBufferTest.FakeDriver2([6, 5, 4, 3, 2, 1])
        buf = ScreenBuffer(msg, page_size=2, buffer_size=5, message_driver2=drv)

        for x in range(7):
            drv.count.acquire()

        drv.recs = [7, 8, 9, 10, 11]
        buf.go_to_previous_line2()

        for x in range(6):
            drv.count.acquire()

        buf.go_to_next_page2()
        cur = buf.get_current_lines()

        buf.stop()
        self.assertTrue(drv.stopped)
        self.assertFalse(drv.error)
        self.assertEqual((6, False, 5), drv.instruction)

        self.assertEqual(2, len(cur))
        self.assertEqual('6', cur[0].message)
        self.assertEqual('7', cur[1].message)
