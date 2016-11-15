class ScreenCursor(object):
    def __init__(self, count, visible_count=None):
        self._count = count
        self._visible_count = visible_count or count

        self._offset = 0
        self._position = 0

    def _update_offset(self):
        pos = self._position
        effective_count = min(self._count, self._visible_count)
        max_offset = max(self._count, pos + 1) - effective_count
        min_offset = 0
        self._offset = min(pos, max_offset, max(pos - self._visible_count + 1,
            min_offset, self._offset))

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, val):
        self._count = val

    @property
    def offset(self):
        return self._offset

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, val):
        self._position = val
        self._update_offset()

    @property
    def visible_count(self):
        return self._visible_count

    @visible_count.setter
    def visible_count(self, val):
        self._visible_count = val
        self._update_offset()
