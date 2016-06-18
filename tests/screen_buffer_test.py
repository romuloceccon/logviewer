import unittest
import threading
import random
from unittest.mock import Mock, MagicMock

from screen_buffer import ScreenBuffer

class ScreenBufferTest(unittest.TestCase):
    class Queue(object):
        def __init__(self):
            self._sem = threading.Semaphore(0)
            self._lock = threading.Lock()
            self._cv = threading.Condition(self._lock)
            self._list = list()

        def push(self, x):
            with self._lock:
                self._list.insert(0, x)
            self._sem.release()

        def pop(self):
            self._sem.acquire()
            with self._lock:
                result = self._list.pop()
            with self._cv:
                self._cv.notify()
            return result

        def push_backward_records(self, start, count):
            for x in range(start, start - count, -1):
                self.push(x)
            self.push(None)

        def push_forward_records(self, start, count):
            for x in range(start, start + count):
                self.push(x)
            self.push(None)

        def is_empty(self):
            with self._lock:
                return len(self._list) == 0

        def push_none_and_wait(self):
            self.push(None)
            self.wait()

        def wait(self):
            with self._cv:
                while len(self._list) != 0:
                    self._cv.wait()

    class Observer(object):
        def __init__(self):
            self._count = 0

        @property
        def count(self):
            return self._count

        def notify(self):
            self._count += 1

    class FakeDriver(ScreenBuffer.Driver):
        def __init__(self, queue):
            self.started = threading.Event()
            self.stopped = False
            self.queue = queue
            self.magic = random.randint(1, 1000)
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
            i = self.queue.pop()
            if i is None:
                return None
            result = { 'id': i, 'datetime': '2016-05-22 23:00:00',
                'host': 'test', 'program': 'test', 'facility_num': 1,
                'level_num': 6, 'message': str(i) }
            return result

    def _get_line(self, i, message=None):
        return { 'id': i, 'datetime': '2016-05-22 23:00:00', 'host': 'test',
            'program': 'test', 'facility_num': 1, 'level_num': 6,
            'message': message is None and str(i) or message }

    def setUp(self):
        self.observer = ScreenBufferTest.Observer()
        self.queue = ScreenBufferTest.Queue()

    def tearDown(self):
        self.assertTrue(self.queue.is_empty())

    def test_should_translate_integers_to_description(self):
        line = ScreenBuffer.Line({ 'id': 1, 'datetime': '', 'host': '',
            'program': '', 'message': '', 'facility_num': 1, 'level_num': 6 }, False)
        self.assertEqual('user', line.facility)
        self.assertEqual('info', line.level)

    def test_should_translate_strings_to_description(self):
        line = ScreenBuffer.Line({ 'id': 1, 'datetime': '', 'host': '',
            'program': '', 'message': '', 'facility_num': '1', 'level_num': '6' }, False)
        self.assertEqual('user', line.facility)
        self.assertEqual('info', line.level)

    def test_should_translate_out_of_range_values_to_blank(self):
        line = ScreenBuffer.Line({ 'id': 1, 'datetime': '', 'host': '',
            'program': '', 'message': '', 'facility_num': 24, 'level_num': 8 }, False)
        self.assertEqual('', line.facility)
        self.assertEqual('', line.level)

    def test_should_translate_invalid_integers_to_blank(self):
        line = ScreenBuffer.Line({ 'id': 1, 'datetime': '', 'host': '',
            'program': '', 'message': '', 'facility_num': 'a', 'level_num': 'b' }, False)
        self.assertEqual('', line.facility)
        self.assertEqual('', line.level)

    def test_should_initialize_screen_buffer_with_defaults(self):
        buf = ScreenBuffer(page_size=10)

        self.assertEqual(50, buf._buffer_size)
        self.assertEqual(10, buf._low_buffer_threshold)

    def test_should_prepend_record_on_empty_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)
        buf.add_observer(self.observer.notify)

        buf.prepend_record(self._get_line(2))
        self.assertEqual(1, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('2', cur[0].message)

    def test_should_prepend_record_on_non_empty_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)
        buf.add_observer(self.observer.notify)

        buf.prepend_record(self._get_line(2))
        buf.prepend_record(self._get_line(1))
        self.assertEqual(2, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('2', cur[1].message)

    def test_should_prepend_record_on_off_screen_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

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
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.add_observer(self.observer.notify)
        buf.append_record(self._get_line(2))
        self.assertEqual(1, self.observer.count)

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('2', cur[0].message)

    def test_should_append_record_on_non_empty_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.append_record(self._get_line(2))
        buf.append_record(self._get_line(3))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_append_record_past_end_of_screen(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.append_record(self._get_line(2))
        buf.append_record(self._get_line(3))

        buf.add_observer(self.observer.notify)
        buf.append_record(self._get_line(4))
        self.assertEqual(0, self.observer.count)

    def test_should_prepend_record_on_buffer_not_at_end_of_screen(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.append_record(self._get_line(2))
        buf.append_record(self._get_line(3))
        buf.append_record(self._get_line(4))
        buf.prepend_record(self._get_line(1))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_prepend_multi_line_record_on_empty_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(1, 'a\nb'))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('a', cur[0].message)
        self.assertEqual(False, cur[0].is_continuation)
        self.assertEqual('b', cur[1].message)
        self.assertEqual(True, cur[1].is_continuation)

    def test_should_prepend_multi_line_record_on_non_empty_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(3))
        buf.prepend_record(self._get_line(2))
        buf.prepend_record(self._get_line(1, 'a\nb'))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)
        self.assertEqual('3', cur[1].message)

    def test_should_append_multi_line_record(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.append_record(self._get_line(1))
        buf.append_record(self._get_line(2, 'a\nb'))
        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('a', cur[1].message)

    def test_should_stop_observing(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.add_observer(self.observer.notify)
        buf.prepend_record(self._get_line(2))
        buf.remove_observer(self.observer.notify)
        buf.prepend_record(self._get_line(1))
        self.assertEqual(1, self.observer.count)

    def test_should_go_to_previous_line(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.go_to_previous_line()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('8', cur[0].message)

    def test_should_go_to_next_line(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10):
            buf.append_record(self._get_line(i + 1))

        buf.go_to_next_line()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('2', cur[0].message)

    def test_should_go_to_previous_page(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.go_to_previous_page()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('7', cur[0].message)
        self.assertEqual('8', cur[1].message)

    def test_should_go_to_previous_page_with_less_lines_than_page_size(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.prepend_record(self._get_line(1))

        buf.go_to_previous_page()

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('1', cur[0].message)

    def test_should_go_to_next_page(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10):
            buf.append_record(self._get_line(i + 1))

        buf.go_to_next_page()

        cur = buf.get_current_lines()
        self.assertEqual(2, len(cur))
        self.assertEqual('3', cur[0].message)

    def test_should_go_to_next_page_with_less_lines_than_page_size(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.append_record(self._get_line(1))

        buf.go_to_next_page()

        cur = buf.get_current_lines()
        self.assertEqual(1, len(cur))
        self.assertEqual('1', cur[0].message)

    def test_should_change_page_size_at_end_of_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.page_size = 3
        cur = buf.get_current_lines()
        self.assertEqual(3, len(cur))
        self.assertEqual('8', cur[0].message)

    def test_should_change_page_size_before_end_of_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        buf.go_to_previous_page()
        buf.page_size = 3

        cur = buf.get_current_lines()
        self.assertEqual(3, len(cur))
        self.assertEqual('7', cur[0].message)

    def test_should_get_buffer_instructions_for_empty_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        self.assertEqual(((None, True, 7),), buf.get_buffer_instructions())

    def test_should_get_buffer_instructions_for_forward_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))

        self.assertEqual(((10, False, 5),), buf.get_buffer_instructions())

    def test_should_not_get_buffer_instructions_for_forward_buffer_if_below_threshold(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 0, -1):
            buf.prepend_record(self._get_line(i))
        buf.go_to_previous_line()
        buf.go_to_previous_line()
        buf.go_to_previous_line()

        self.assertEqual(tuple(), buf.get_buffer_instructions())

    def test_should_get_buffer_instructions_for_backward_buffer(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 20):
            buf.append_record(self._get_line(i + 1))

        self.assertEqual(((11, True, 5),), buf.get_buffer_instructions())

    def test_should_not_get_buffer_instructions_for_backward_buffer_if_below_threshold(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        for i in range(10, 20):
            buf.append_record(self._get_line(i + 1))
        buf.go_to_next_line()
        buf.go_to_next_line()
        buf.go_to_next_line()

        self.assertEqual(tuple(), buf.get_buffer_instructions())

    def test_should_get_buffer_instructions_if_both_buffers_are_below_threshold(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.append_record(self._get_line(11))
        buf.append_record(self._get_line(12))

        self.assertEqual(((12, False, 5), (11, True, 5)), buf.get_buffer_instructions())

    def test_should_start_and_stop_driver(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf.start(drv)
        drv.started.wait()
        self.queue.push_none_and_wait()

        buf.stop()
        self.assertTrue(drv.stopped)

    def test_should_not_start_already_started_driver(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf.start(drv)
        self.queue.push(None)
        try:
            self.assertRaises(ValueError, buf.start, drv)
        finally:
            buf.stop()

    def test_should_restart_driver(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf.start(drv)
        self.queue.push(None)

        queue2 = ScreenBufferTest.Queue()
        drv2 = ScreenBufferTest.FakeDriver(queue2)
        buf.restart(drv2)
        queue2.push(None)

        buf.stop()

    def test_should_stop_unstarted_driver(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.stop()

    def test_should_clear_existing_records_on_restart(self):
        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.start(drv)
        self.queue.push_backward_records(2, 2)
        self.queue.wait()

        queue2 = ScreenBufferTest.Queue()
        drv2 = ScreenBufferTest.FakeDriver(queue2)
        buf.restart(drv2)
        queue2.push_none_and_wait()

        try:
            self.assertEqual(0, len(buf.get_current_lines()))
        finally:
            buf.stop()

    def test_should_fetch_records_from_thread(self):
        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        buf.start(drv)
        self.queue.push_backward_records(2, 2)
        self.queue.wait()

        cur = buf.get_current_lines()
        buf.stop()
        self.assertTrue(drv.stopped)
        self.assertFalse(drv.error)
        self.assertEqual((None, True, 7), drv.instruction)

        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('2', cur[1].message)

    def test_should_fetch_records_in_descending_order(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        self.queue.push_backward_records(2, 2)

        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf.get_records(drv)
        cur = buf.get_current_lines()

        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('2', cur[1].message)

    def test_should_fetch_records_in_ascending_order(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        self.queue.push_backward_records(5, 5)

        drv = ScreenBufferTest.FakeDriver(self.queue)
        buf.get_records(drv)

        self.queue.push_forward_records(6, 5)

        buf.get_records(drv)

        buf.go_to_next_page()
        cur = buf.get_current_lines()

        self.assertEqual(2, len(cur))
        self.assertEqual('6', cur[0].message)
        self.assertEqual('7', cur[1].message)

    def test_should_stop_fetching_if_fetch_returns_less_records_than_asked(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        drv = ScreenBufferTest.FakeDriver(self.queue)

        self.queue.push_backward_records(6, 6)

        buf.get_records(drv)

        buf.go_to_previous_page()
        buf.go_to_previous_page()

        buf.get_records(drv)

        cur = buf.get_current_lines()

        self.assertEqual(2, len(cur))
        self.assertEqual('1', cur[0].message)
        self.assertEqual('2', cur[1].message)

    def test_should_not_stop_fetching_if_fetch_returns_correct_number_of_records(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        drv = ScreenBufferTest.FakeDriver(self.queue)

        self.queue.push_backward_records(14, 7)
        buf.get_records(drv)

        buf.go_to_previous_page()
        buf.go_to_previous_page()

        self.queue.push_backward_records(7, 7)
        buf.get_records(drv)

        buf.go_to_previous_page()
        cur = buf.get_current_lines()

        self.assertEqual(2, len(cur))
        self.assertEqual('7', cur[0].message)
        self.assertEqual('8', cur[1].message)

    def test_should_not_stop_fetching_if_forward_fetch_returns_fewer_records(self):
        buf = ScreenBuffer(page_size=2, buffer_size=5)

        drv = ScreenBufferTest.FakeDriver(self.queue)

        self.queue.push_backward_records(14, 7)
        buf.get_records(drv)

        buf.go_to_previous_line()
        self.queue.push(None)
        buf.get_records(drv)

        buf.go_to_previous_page()
        buf.go_to_previous_page()

        self.queue.push_backward_records(7, 7)
        buf.get_records(drv)

        buf.go_to_previous_page()
        cur = buf.get_current_lines()

        self.assertEqual(2, len(cur))
        self.assertEqual('6', cur[0].message)
        self.assertEqual('7', cur[1].message)
