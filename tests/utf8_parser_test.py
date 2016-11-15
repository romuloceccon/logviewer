import unittest
import curses

from utf8_parser import UTF8Parser

class UTF8ParserTest(unittest.TestCase):
    def setUp(self):
        self.text = ''
        self.parser = UTF8Parser(self._put_char)

    def _put_char(self, c):
        self.text += c

    def test_should_accept_ascii_char(self):
        self.parser.put_key(ord('a'))
        self.assertEqual('a', self.text)

    def test_should_not_accept_invalid_utf8_char(self):
        self.parser.put_key(0x8f)
        self.assertEqual('', self.text)

    def test_should_accept_two_byte_utf8_char(self):
        self.parser.put_key(0xc3)
        self.parser.put_key(0xa1)
        self.assertEqual('á', self.text)

    def test_should_accept_sequence_of_utf8_chars(self):
        self.parser.put_key(0xc3)
        self.parser.put_key(0xa1)
        self.parser.put_key(0xc2)
        self.parser.put_key(0xb6)
        self.assertEqual('á¶', self.text)

    def test_should_accept_three_byte_utf8_char(self):
        self.parser.put_key(0xE2)
        self.parser.put_key(0x80)
        self.parser.put_key(0x9C)
        self.assertEqual('“', self.text)

    def test_should_resync_at_ascii_char_following_unterminated_sequence(self):
        self.parser.put_key(0xc3)
        self.parser.put_key(ord('a'))
        self.parser.put_key(ord('b'))
        self.assertEqual('ab', self.text)

    def test_should_discard_invalid_continuation_byte_after_resync(self):
        self.parser.put_key(0xc3)
        self.parser.put_key(ord('a'))
        self.parser.put_key(0xa1)
        self.assertEqual('a', self.text)

    def test_should_accept_ascii_char_after_utf8_char(self):
        self.parser.put_key(0xE2)
        self.parser.put_key(0x80)
        self.parser.put_key(0x9C)
        self.parser.put_key(ord('a'))
        self.assertEqual('“a', self.text)

    def test_should_resync_at_leading_byte_following_unterminated_sequence(self):
        self.parser.put_key(0xc3)
        self.parser.put_key(0xc3)
        self.parser.put_key(0xa1)
        self.assertEqual('á', self.text)

    def test_should_accept_four_byte_sequence(self):
        self.parser.put_key(0xf0)
        self.parser.put_key(0x90)
        self.parser.put_key(0x8d)
        self.parser.put_key(0x88)
        self.assertEqual('𐍈', self.text)
