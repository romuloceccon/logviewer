import struct

class Utf8Parser(object):
    def __init__(self, receive):
        self._receive = receive
        self._buffer = []
        self._seq_size = 0

    def put_key(self, key):
        if key & 0x80 == 0:
            self._buffer.clear()
            self._receive(chr(key))
            self._seq_size = 0
        elif key & 0xe0 == 0xc0:
            self._buffer.clear()
            self._buffer.append(key)
            self._seq_size = 2
        elif key & 0xf0 == 0xe0:
            self._buffer.clear()
            self._buffer.append(key)
            self._seq_size = 3
        elif key & 0xf8 == 0xf0:
            self._buffer.clear()
            self._buffer.append(key)
            self._seq_size = 4
        elif key & 0xc0 == 0x80 and self._seq_size > 0:
            self._buffer.append(key)
            if len(self._buffer) >= self._seq_size:
                enc = struct.pack('B' * self._seq_size, *(self._buffer))
                self._receive(enc.decode('utf-8'))
                self._buffer.clear()
                self._seq_size = 0
        else:
            self._buffer.clear()
            self._seq_size = 0
