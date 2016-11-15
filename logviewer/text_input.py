import curses

from .screen_cursor import ScreenCursor

class TextInput(object):
    def __init__(self, max_len, text=''):
        self._max_len = max_len
        # one more character so we can show the cursor without scrolling the text
        self._width = self._max_len + 1
        self._text = text[:max_len]

        self._cursor = ScreenCursor(count=0, visible_count=self._width)
        self._cursor.position = len(self._text)

    @property
    def cursor(self):
        return self._cursor.position - self._cursor.offset

    @property
    def text(self):
        return self._text

    @property
    def visible_text(self):
        offset = self._cursor.offset
        return self._text[offset:offset + self._width]

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, val):
        self._width = val
        self._cursor.visible_count = val

    def put(self, char):
        pos = self._cursor.position
        cnt = len(self._text)

        if isinstance(char, str) and cnt < self._max_len and ord(char) >= 0x20:
            self._text = self._text[:pos] + char + self._text[pos:]
            self._cursor.count = len(self._text)
            self._cursor.position = pos + 1
        elif char == curses.KEY_LEFT and pos > 0:
            self._cursor.position = pos - 1
        elif char == curses.KEY_RIGHT and pos < cnt:
            self._cursor.position = pos + 1
        elif char == curses.KEY_HOME:
            self._cursor.position = 0
        elif char == curses.KEY_END:
            self._cursor.position = cnt
        elif char == curses.KEY_BACKSPACE and pos > 0:
            self._text = self._text[:pos - 1] + self._text[pos:]
            self._cursor.count = len(self._text)
            self._cursor.position = pos - 1
        elif char == curses.KEY_DC:
            self._text = self._text[:pos] + self._text[pos + 1:]
            self._cursor.count = len(self._text)
