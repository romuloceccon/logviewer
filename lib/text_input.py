import curses

class TextInput(object):
    def __init__(self, max_len):
        self._max_len = max_len
        # one more character so we can show the cursor without scrolling the text
        self._width = self._max_len + 1
        self._text = ''
        self._position = 0
        self._offset = 0

    @property
    def cursor(self):
        return self._position - self._offset

    @property
    def text(self):
        return self._text

    @property
    def visible_text(self):
        return self._text[self._offset:self._offset + self._width]

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, val):
        self._width = val
        self._set_position(self._position)

    def _set_position(self, pos):
        self._position = pos

        effective_len = len(self._text)
        if pos >= effective_len:
            effective_len += 1
        visible_w = min(self._width, effective_len)
        max_o = effective_len - visible_w

        self._offset = min(pos, max_o, max(self._offset, pos - visible_w + 1))

    def put(self, char):
        if isinstance(char, str) and len(self._text) < self._max_len and ord(char) >= 0x20:
            self._text = self._text[:self._position] + char + self._text[self._position:]
            self._set_position(self._position + 1)
        elif char == curses.KEY_LEFT and self._position > 0:
            self._set_position(self._position - 1)
        elif char == curses.KEY_RIGHT and self._position < len(self._text):
            self._set_position(self._position + 1)
        elif char == curses.KEY_HOME:
            self._set_position(0)
        elif char == curses.KEY_END:
            self._set_position(len(self._text))
        elif char == curses.KEY_BACKSPACE and self._position > 0:
            self._text = self._text[:self._position - 1] + self._text[self._position:]
            self._set_position(self._position - 1)
        elif char == curses.KEY_DC:
            self._text = self._text[:self._position] + self._text[self._position + 1:]
