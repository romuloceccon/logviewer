import curses

class TextInput(object):
    def __init__(self, max_len):
        self._max_len = max_len
        self._text = ''
        self._cursor = 0

    @property
    def text(self):
        return self._text

    @property
    def visible_text(self):
        return self._text

    @property
    def cursor(self):
        return self._cursor

    def put(self, char):
        if isinstance(char, str) and len(self._text) < self._max_len:
            self._text = self._text[:self._cursor] + char + self._text[self._cursor:]
            self._cursor += 1
        elif char == curses.KEY_LEFT and self._cursor > 0:
            self._cursor -= 1
        elif char == curses.KEY_RIGHT and self._cursor < len(self._text):
            self._cursor += 1
        elif char == curses.KEY_BACKSPACE and self._cursor > 0:
            self._text = self._text[:self._cursor - 1] + self._text[self._cursor:]
            self._cursor -= 1
