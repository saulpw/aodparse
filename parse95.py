import struct
import sys

# mainly based on RES001
block_types = {
    b'\x01\x00\x00\x00': "text(?)", # one help text block, one short 18-byte block
    b'\x03\x00\x00\x00': "text", # misc help text
    b'\x05\x00\x00\x00': "text", # help text for left button
    b'\x06\x00\x00\x00': "text", # help text for left button
    b'\x07\x00\x00\x00': "text", # help text for left button
    b'\x0a\x00\x00\x00': "text", # help text for left button
    b'\x0b\x00\x00\x00': "text", # help text for left button
    b'\x0c\x00\x00\x00': "text", # misc help text
    b'\x0f\x00\xf7\x00': "text", # misc help text
    b'\x10\x00\x14\x01': "text", # help text for left button
    b'\x13\x00\xf7\x00': "text", # misc help text
    b'\x44\x33\x47\x52': "graphic",
}

# mainly based on RES001
block_subtypes = {
    b'\x00\x00\x00\x00': "palette",
    b'\x20\x00\x00\x00': "image", # single-frame, mostly characters
    b'\x22\x00\x00\x00': "selector", # player-controlled icons i think, all single-frame
    b'\x24\x00\x00\x00': "2-frame image", # both frames are same-sized, meant to be layered/animated, or just different views?

    # might be groups of animations and/or an animation with frames of different sizes that
    # should be layered at particular relative positions
    b'\x28\x00\x00\x00': "animation",
    b'\x2c\x00\x00\x00': "animation",

    b'\x2e\x00\x00\x00': "selectors/icons", # not sure what exactly these things are, multi-frame
    b'\x4c\x00\x00\x00': "animated icon(s)", # usually all frames are same-sized/same icon but one block contains several icons
    b'\x1c\x02\x00\x00': "font",
    b'\x24\x03\x00\x00': "background", # single-frame 320x200 image
}

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
        self.type_id = self.buf[:4]
        self.type_id_str = ' '.join(f'{x:02x}' for x in self.type_id)
        self.subtype_id = self.buf[8:12]
        self.subtype_id_str = ' '.join(f'{x:02x}' for x in self.subtype_id)
        self.block_type = block_types.get(self.type_id, "")
        self.block_subtype = block_subtypes.get(self.subtype_id, "")
        if len(self.buf) < 24:
            return
        self.header = struct.unpack_from('<LLLLLL', self.buf)
        self.header_str = ' '.join(f'{x:02x}' for x in self.buf[:24])
        self.chunk3_offset = self.header[2] # offset of chunk 3
        self.chunk3_size = 0
#        if self.chunk3_offset > len(self.buf):
#            self.chunk3_size = 0
#        else:
#            self.chunk3_size, = struct.unpack_from('<L', self.buf[self.chunk3_offset:self.chunk3_offset+4])

    def __str__(self):
        return f"Block offset: {self.offset:x} Block length: {self.size:d}"

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
        i = 0
        while i < self.h*self.w:
            row = self.body[i:i+self.w]
            self.byte_rows.append(row)
            self.rows.append(self.asciify(row))
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
