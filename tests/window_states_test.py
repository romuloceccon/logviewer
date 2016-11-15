import unittest

import datetime

import window_states

class FilterTest(unittest.TestCase):
    def test_should_create_filter_state(self):
        filter = window_states.Filter()
        self.assertEqual(7, filter.level)
        self.assertIsNone(filter.facility)
        self.assertIsNone(filter.host)
        self.assertIsNone(filter.program)

    def test_should_set_facility(self):
        filter = window_states.Filter()
        filter.facility = 10
        self.assertEqual(10, filter.facility)

    def test_should_set_host(self):
        filter = window_states.Filter()
        filter.host = 'example'
        self.assertEqual('example', filter.host)

    def test_should_clear_host(self):
        filter = window_states.Filter()
        filter.host = ''
        self.assertIsNone(filter.host)

    def test_should_set_level(self):
        filter = window_states.Filter()
        filter.level = 4
        self.assertEqual(4, filter.level)

    def test_should_clear_level(self):
        filter = window_states.Filter()
        filter.level = 4
        filter.level = None
        self.assertEqual(7, filter.level)

    def test_should_set_program(self):
        filter = window_states.Filter()
        filter.program = 'su'
        self.assertEqual('su', filter.program)

    def test_should_clear_program(self):
        filter = window_states.Filter()
        filter.program = ''
        self.assertIsNone(filter.program)

    def test_should_get_empty_filter_summary(self):
        filter = window_states.Filter()
        self.assertEqual((('[l]evel', 'debug'), ('[f]acility', 'ALL'),
            ('[p]rogram', '*'), ('[h]ost', '*')), filter.get_summary())

    def test_should_get_non_empty_filter_summary(self):
        filter = window_states.Filter()
        filter.level = 6
        filter.facility = 0
        filter.host = 'example'
        filter.program = 'test'
        self.assertEqual((('[l]evel', 'info'), ('[f]acility', 'kern'),
            ('[p]rogram', 'test'), ('[h]ost', 'example')), filter.get_summary())

class DatetimeTest(unittest.TestCase):
    def test_should_initialize_datetime_state(self):
        dt = datetime.datetime(2016, 6, 27, 18, 56, 30)
        state = window_states.Datetime(dt)
        self.assertEqual('2016-06-27 18:56:30', state.text)
        self.assertEqual(datetime.datetime(2016, 6, 27, 18, 56, 30),
            state.value)

    def test_should_get_year_position(self):
        state = window_states.Datetime(datetime.datetime.utcnow())
        self.assertEqual((0, 4), state.position)

    def test_should_go_to_month_position(self):
        state = window_states.Datetime(datetime.datetime.utcnow())
        state.move_right()
        self.assertEqual((5, 2), state.position)

    def test_should_go_back_to_year_position(self):
        state = window_states.Datetime(datetime.datetime.utcnow())
        state.move_right()
        state.move_left()
        self.assertEqual((0, 4), state.position)

    def test_should_honor_left_boundary(self):
        state = window_states.Datetime(datetime.datetime.utcnow())
        state.move_right()
        state.move_left()
        state.move_left()
        self.assertEqual((0, 4), state.position)

    def test_should_honor_right_boundary(self):
        state = window_states.Datetime(datetime.datetime.utcnow())
        for i in range(6):
            state.move_right()
        self.assertEqual((17, 2), state.position)

    def test_should_increment_year(self):
        dt = datetime.datetime(2016, 6, 27, 19, 10, 3)
        state = window_states.Datetime(dt)
        state.increment()
        self.assertEqual('2017-06-27 19:10:03', state.text)

    def test_should_increment_from_leap_year(self):
        dt = datetime.datetime(2016, 2, 29, 0, 0, 0)
        state = window_states.Datetime(dt)
        state.increment()
        self.assertEqual('2017-02-28 00:00:00', state.text)

    def test_should_decrement_year(self):
        dt = datetime.datetime(2016, 6, 27, 19, 20, 4)
        state = window_states.Datetime(dt)
        state.decrement()
        self.assertEqual('2015-06-27 19:20:04', state.text)

    def test_should_increment_month(self):
        dt = datetime.datetime(2016, 6, 27, 19, 28, 52)
        state = window_states.Datetime(dt)
        state.move_right()
        state.increment()
        self.assertEqual('2016-07-27 19:28:52', state.text)

    def test_should_increment_from_long_month(self):
        dt = datetime.datetime(2016, 1, 31, 0, 0, 0)
        state = window_states.Datetime(dt)
        state.move_right()
        state.increment()
        self.assertEqual('2016-02-29 00:00:00', state.text)

    def test_should_increment_month_at_end_of_year(self):
        dt = datetime.datetime(2015, 12, 1, 0, 0, 0)
        state = window_states.Datetime(dt)
        state.move_right()
        state.increment()
        self.assertEqual('2016-01-01 00:00:00', state.text)

    def test_should_decrement_month(self):
        dt = datetime.datetime(2016, 6, 27, 19, 38, 43)
        state = window_states.Datetime(dt)
        state.move_right()
        state.decrement()
        self.assertEqual('2016-05-27 19:38:43', state.text)

    def test_should_increment_day(self):
        dt = datetime.datetime(2016, 6, 27, 19, 54, 14)
        state = window_states.Datetime(dt)
        state.move_right()
        state.move_right()
        state.increment()
        self.assertEqual('2016-06-28 19:54:14', state.text)

    def test_should_decrement_day(self):
        dt = datetime.datetime(2016, 6, 27, 19, 56, 14)
        state = window_states.Datetime(dt)
        state.move_right()
        state.move_right()
        state.decrement()
        self.assertEqual('2016-06-26 19:56:14', state.text)

    def test_should_increment_hour(self):
        dt = datetime.datetime(2016, 6, 27, 19, 57, 35)
        state = window_states.Datetime(dt)
        for i in range(3):
            state.move_right()
        state.increment()
        self.assertEqual('2016-06-27 20:57:35', state.text)

    def test_should_increment_minute(self):
        dt = datetime.datetime(2016, 6, 27, 20, 1, 45)
        state = window_states.Datetime(dt)
        for i in range(4):
            state.move_right()
        state.increment()
        self.assertEqual('2016-06-27 20:02:45', state.text)

    def test_should_increment_second(self):
        dt = datetime.datetime(2016, 6, 27, 20, 2, 36)
        state = window_states.Datetime(dt)
        for i in range(5):
            state.move_right()
        state.increment()
        self.assertEqual('2016-06-27 20:02:37', state.text)
