import unittest
import curses

from text_input import TextInput

class TextInputTest(unittest.TestCase):
    def test_should_initialize_text_input(self):
        input = TextInput(max_len=10)
        self.assertEqual('', input.text)
        self.assertEqual('', input.visible_text)
        self.assertEqual(0, input.cursor)

    def test_should_put_single_char(self):
        input = TextInput(max_len=10)
        input.put('a')
        self.assertEqual('a', input.text)
        self.assertEqual('a', input.visible_text)
        self.assertEqual(1, input.cursor)

    def test_should_move_cursor_left(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put(curses.KEY_LEFT)
        self.assertEqual(0, input.cursor)

    def test_should_move_cursor_right(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put(curses.KEY_LEFT)
        input.put(curses.KEY_RIGHT)
        self.assertEqual(1, input.cursor)

    def test_should_not_move_cursor_before_left_boundary(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put(curses.KEY_LEFT)
        input.put(curses.KEY_LEFT)
        self.assertEqual(0, input.cursor)

    def test_should_not_move_cursor_after_right_boundary(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put(curses.KEY_RIGHT)
        self.assertEqual(1, input.cursor)

    def test_should_put_backspace(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put('b')
        input.put(curses.KEY_BACKSPACE)
        self.assertEqual('a', input.text)
        self.assertEqual(1, input.cursor)

    def test_should_put_char_at_beginning(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put(curses.KEY_LEFT)
        input.put('b')
        self.assertEqual('ba', input.text)
        self.assertEqual(1, input.cursor)

    def test_should_put_backspace_before_end(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put('b')
        input.put(curses.KEY_LEFT)
        input.put(curses.KEY_BACKSPACE)
        self.assertEqual('b', input.text)
        self.assertEqual(0, input.cursor)

    def test_should_not_put_backspace_at_beginning(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put(curses.KEY_LEFT)
        input.put(curses.KEY_BACKSPACE)
        self.assertEqual('a', input.text)
        self.assertEqual(0, input.cursor)

    def test_should_honor_max_len(self):
        input = TextInput(max_len=10)
        for c in range(11):
            input.put(chr(ord('a') + c))
        self.assertEqual('abcdefghij', input.text)
        self.assertEqual(10, input.cursor)
