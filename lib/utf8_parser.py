import struct

class UTF8Parser(object):
    def __init__(self, receive):
        self._receive = receive
        self._buffer = []
        self._seq_size = 0

    def _reset_buffer(self, size):
        self._buffer.clear()
        self._seq_size = size

    def put_key(self, key):
        if key & 0x80 == 0:
            self._reset_buffer(1)
        elif key & 0xe0 == 0xc0:
            self._reset_buffer(2)
        elif key & 0xf0 == 0xe0:
            self._reset_buffer(3)
        elif key & 0xf8 == 0xf0:
            self._reset_buffer(4)
        elif key & 0xc0 != 0x80 or self._seq_size == 0:
            return

        self._buffer.append(key)
        if len(self._buffer) >= self._seq_size:
            enc = struct.pack('B' * self._seq_size, *(self._buffer))
            self._reset_buffer(0)
            self._receive(enc.decode('utf-8'))
