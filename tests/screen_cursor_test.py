import unittest

from logviewer.screen_cursor import ScreenCursor

class ScreenCursorTest(unittest.TestCase):
    def test_should_create_cursor(self):
        cursor = ScreenCursor(count=5)
        self.assertEqual(5, cursor.visible_count)
        self.assertEqual(0, cursor.offset)
        self.assertEqual(0, cursor.position)

    def test_should_create_cursor_with_smaller_visible_count(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        self.assertEqual(3, cursor.visible_count)

    def test_should_increment_position(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 1
        self.assertEqual(0, cursor.offset)
        self.assertEqual(1, cursor.position)

    def test_should_increment_position_with_smaller_count(self):
        cursor = ScreenCursor(count=2, visible_count=5)
        cursor.position = 1
        self.assertEqual(0, cursor.offset)
        self.assertEqual(1, cursor.position)

    def test_should_increment_position_past_end_of_screen(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 5
        self.assertEqual(3, cursor.offset)

    def test_should_decrement_offset_if_position_was_offscreen(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 5
        cursor.position = 4
        self.assertEqual(2, cursor.offset)

    def test_should_decrement_position_past_beginning_of_screen(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = -1
        self.assertEqual(-1, cursor.offset)

    def test_should_increment_offset_if_position_was_offscreen(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = -1
        cursor.position = 0
        self.assertEqual(0, cursor.offset)

    def test_should_increment_offset_if_position_would_be_offscreen(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 3
        self.assertEqual(1, cursor.offset)

    def test_should_not_decrement_offset_if_going_back_one_position(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 3
        cursor.position = 2
        self.assertEqual(1, cursor.offset)

    def test_should_decrement_offset_if_visible_count_increases(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 4
        cursor.visible_count = 4
        self.assertEqual(1, cursor.offset)

    def test_should_decrement_offset_if_count_and_visible_count_increase(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 4
        cursor.count = 6
        cursor.visible_count = 4
        self.assertEqual(2, cursor.offset)

    def test_should_decrement_offset_if_position_would_be_offscreen(self):
        cursor = ScreenCursor(count=5, visible_count=3)
        cursor.position = 4
        cursor.position = 1
        self.assertEqual(1, cursor.offset)
