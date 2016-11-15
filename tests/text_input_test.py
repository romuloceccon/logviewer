import unittest
import curses

from logviewer.text_input import TextInput

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

    def test_should_swallow_control_chars(self):
        input = TextInput(max_len=10)
        input.put('\t')
        self.assertEqual('', input.text)
        self.assertEqual(0, input.cursor)

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

    def test_should_delete_char_at_cursor(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put('b')
        input.put(curses.KEY_LEFT)
        input.put(curses.KEY_LEFT)
        input.put(curses.KEY_DC)
        self.assertEqual('b', input.text)
        self.assertEqual(0, input.cursor)

    def test_should_go_to_beginning(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put('b')
        input.put(curses.KEY_HOME)
        self.assertEqual(0, input.cursor)

    def test_should_go_to_end(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put('b')
        input.put(curses.KEY_HOME)
        input.put(curses.KEY_END)
        self.assertEqual(2, input.cursor)

    def test_should_honor_max_len(self):
        input = TextInput(max_len=10)
        for c in range(11):
            input.put(chr(ord('a') + c))
        self.assertEqual('abcdefghij', input.text)
        self.assertEqual(10, input.cursor)

    def test_should_scroll_narrow_input(self):
        input = TextInput(max_len=10)
        input.width = 3
        input.put('a')
        input.put('b')
        input.put('c')
        self.assertEqual('abc', input.text)
        self.assertEqual('bc', input.visible_text)
        self.assertEqual(2, input.cursor)

    def test_should_squeeze_text_input_after_input(self):
        input = TextInput(max_len=10)
        input.put('a')
        input.put('b')
        input.put('c')
        input.put('d')
        input.width = 3
        self.assertEqual('cd', input.visible_text)
        self.assertEqual(2, input.cursor)

    def test_should_initialize_text_input_with_text(self):
        input = TextInput(max_len=10, text='test')
        self.assertEqual('test', input.visible_text)
        self.assertEqual(4, input.cursor)

    def test_should_initialize_text_input_with_long_text(self):
        input = TextInput(max_len=10, text='an excessively long test')
        self.assertEqual('an excessi', input.visible_text)
        self.assertEqual(10, input.cursor)
