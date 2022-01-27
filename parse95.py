import struct
import sys

class Res():
    def __init__(self, filename):
        self.buf = open(filename, mode='rb').read()

    def __len__(self):
        return len(self.buf)

    def __iter__(self):
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
        return DataBlock(self.buf[i:j], i)
            

class DataBlock():
    def __init__(self, buf, offset):
        self.offset = offset
        self.buf = buf
        self.magic = ' '.join(hex(x)[2:] for x in self.buf[:4])
        if len(self.buf) < 24:
            return        
        self.header = struct.unpack_from('<LLLLLL', self.buf)
        i = self.header[2] # offset of chunk 3
        if i > len(self.buf):
            self.chunk3_size = 0
        else:
            self.chunk3_size, = struct.unpack_from('<L', self.buf[i:i+4])

    def __str__(self):
        return f"Block offset: {self.offset:x} Block length: {len(self):d} {self.magic}" 

    def __len__(self):
        return len(self.buf)

    def __iter__(self):
        i = self.header[2]+self.chunk3_size
        while i < len(self.buf):
            frame_size, = struct.unpack_from('<L', self.buf[i:i+4])
            yield Frame(self.buf[i:i+frame_size], i)
            i += frame_size

class Frame():
    def __init__(self, buf, offset):
        self.offset = offset
        self.header = buf[:16]
        self.body = buf[16:]
        self.h, self.w, = struct.unpack_from('<HH', self.header[-4:])
        self.rows = []
        i = 0
        while i < self.h*self.w:
            self.rows.append(self.body[i:i+self.w])
            i += self.w            

    def __repr__(self):
        def asciify(c):
            if c > 31 and c < 128: return chr(c)
            if c == 0: return " "
            return "*"

        
        image = f'w={self.w:3d} h={self.h:3d} offset={self.offset}\n'
        for i in range(self.h):
            image += (''.join([asciify(c) for c in self.rows[i]]) + '\n')
        return image
            
        
res = Res(sys.argv[1])
for i, block in enumerate(res):
    print("Block %d: %s" % (i, block))
#    for j, frame in enumerate(block):
#        print("  Frame %d: %s" % (j, frame))
