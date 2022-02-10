import struct
import sys

class Res():
    def __init__(self, filename):
        self.buf = open(filename, mode='rb').read()

    def __len__(self):
        return len(self.buf)

    def iter_blocks(self):
        i = 0
        while True:
            block = self.get_block(i)
            if block is None:
                break
            yield block
            i += 1
                
    def get_block_offset(self, blocknum):
        offset, = struct.unpack_from('<L', self.buf, (blocknum+1)*4)
        return offset

    def get_block(self, blocknum):
        i = self.get_block_offset(blocknum)
        if i >= len(self.buf):
            return None
        j = self.get_block_offset(blocknum+1)
        return DataBlock(blocknum, self.buf[i:j], i)


class DataBlock():
    def __init__(self, index, buf, offset):
        self.index = index
        self.offset = offset
        self.buf = buf
        self.magic = ' '.join(hex(x)[2:].zfill(2) for x in self.buf[:4])
        if len(self.buf) < 24:
            return
        self.header = struct.unpack_from('<LLLLLL', self.buf)
        i = self.header[2] # offset of chunk 3
        if i > len(self.buf):
            self.chunk3_size = 0
        else:
            self.chunk3_size, = struct.unpack_from('<L', self.buf[i:i+4])

    def __str__(self):
        return f"Block offset: {self.offset:x} Block length: {self.size:d} {self.magic}"

    @property
    def size(self):
        return len(self.buf)

    def iter_frames(self):
        i = self.header[2]+self.chunk3_size
        framenum = 0
        while i < len(self.buf):
            frame_size, = struct.unpack_from('<L', self.buf[i:i+4])
            yield Frame(framenum, self.buf[i:i+frame_size], i)
            i += frame_size
            framenum += 1

class Frame():
    def __init__(self, index, buf, offset):
        self.index = index
        self.offset = offset
        self.header = buf[:16]
        self.body = buf[16:]
        self.h, self.w, = struct.unpack_from('<HH', self.header[-4:])
        self.byte_rows = []
        self.rows = []
        self.hex_rows = []
        i = 0
        while i < self.h*self.w:
            row = self.body[i:i+self.w]
            self.byte_rows.append(row)
            self.rows.append(self.asciify(row))
#            self.hex_rows.append(' '.join(f'{c:02x}' for c in row))
            i += self.w

    def asciify(self, row):
        def asciify_c(c):
            if c > 31 and c < 128: return chr(c)
            if c == 0: return " "
            return "*"
        return ''.join([asciify_c(c) for c in row])

    def __repr__(self):
        image = f'w={self.w:3d} h={self.h:3d} offset={self.offset}\n'
        for i in range(self.h):
            image += self.rows[i] + '\n'
        return image


if __name__ == '__main__':
    res = Res(sys.argv[1])
    for i, block in enumerate(res):
        print("Block %d: %s" % (i, block))
#        for j, frame in enumerate(block):
#            print("  Frame %d: %s" % (j, frame))
