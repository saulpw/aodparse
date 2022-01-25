import struct
import sys

class Res():
    def __init__(self, filename):
        self.buf = open(filename, mode='rb').read()
        self.magic = self.buf[:4]
        self.get_block_offsets()
        self.get_blocks()
        self.get_header()

    def __len__(self):
        return len(self.buf)

    def get_block_offsets(self):
        self.block_offsets = []
        for i in range(len(self.buf) - 4):            
            if self.buf[i:i+4] == bytes.fromhex("44 33 47 52"):
                self.block_offsets.append(i)

    def get_blocks(self):
        if len(self.block_offsets) == 0:
            print("No D3GR blocks!")
            return
        self.blocks = {}
        for i in range(len(self.block_offsets) - 1):
            self.blocks[self.block_offsets[i]] = self.buf[self.block_offsets[i]:self.block_offsets[i+1]]
        self.blocks[self.block_offsets[-1]] = self.buf[self.block_offsets[-1]:]

    def summarize_blocks(self):
        print("offset  size\n------------")
        for offset, block in self.blocks.items():
            print("%x:   %d" % (offset, len(block)))

    def get_data_block(self, i):
        offset = self.block_offsets[i]
        return DataBlock(offset, self.blocks[offset])

    def get_header(self):
        if len(self.block_offsets) == 0:
            print("No D3GR blocks!")
            return
        self.header = self.buf[:self.block_offsets[0]]
        self.header_ptrs = []
        # assume that the first 4 bytes are magic and skip them
        for i in range(4, len(self.header) - 4, 4):
            ptr, = struct.unpack_from('<L', self.header[i:i+4])
            self.header_ptrs.append(ptr)
        # check that the last 4 bytes are the file size and skip them
        last, = struct.unpack_from('<L', self.header[-4:])
        if last != len(self.buf):
            print("End of header %x is not equal to file size %x!" % (last, len(self.buf)))

    def summarize_header(self):
        print("addr   ptr\n------------")
        for i, ptr in enumerate(self.header_ptrs):
            print("%x:   %x" % (4*(i+1), ptr))

    # check whether the first chunk of the file consists of pointers
    # to the data blocks
    def check_header(self):
        if len(self.block_offsets) == 0:
            print("No data blocks to check against!")
            return False
        else:
            is_ok = True
            i = 0
            while i < len(self.header_ptrs) and i < len(self.block_offsets):
                if self.header_ptrs[i] != self.block_offsets[i]:
                    print("Header ptr %x at address %x doesn't match next block offset %x" % (self.header_ptrs[i], 4*(i+1), self.block_offsets[i]))
                    is_ok = False
                i += 1
            if len(self.header_ptrs) > len(self.block_offsets):
                is_ok = False
                print("Header ptr list is %d items longer; remaining items:" % (len(self.header_ptrs) - len(self.block_offsets)))
                for j in self.header_ptrs[i:]:
                    print("%x" % j)
            if len(self.block_offsets) > len(self.header_ptrs):
                is_ok = False
                print("Block offset list is %d items longer; remaining items:" % (len(self.block_offsets) - len(self.header_ptrs)))
                for j in self.block_offsets[i:]:
                    print("%x" % j)                
            return is_ok
        

class DataBlock():
    def __init__(self, offset, buf):
        self.offset = offset
        print("Block offset: %x" % self.offset)
        self.buf = buf
        self.header = buf[:28]        
        self.num_stanzas = buf[9]
        self.num_ptrs_per_stanza = buf[24]
        self.parse_header()

    def __len__(self):
        return len(self.buf)

    def parse_header(self):
        self.magic = self.header[:4]
        self.h1, = struct.unpack_from('<L', self.header[4:8])
        self.chunk2_offset, = struct.unpack_from('<L', self.header[8:12])
        self.h3, = struct.unpack_from('<L', self.header[12:16])
        self.h4, = struct.unpack_from('<L', self.header[16:20])
        self.h5, = struct.unpack_from('<L', self.header[20:24])
        self.h6, = struct.unpack_from('<L', self.header[24:28])
#        self.chunk3_offset = self.chunk2_offset + 0x200
        self.chunk3_offset = self.chunk2_offset
        self.chunk3_size = 0

        self.parse_chunk1()
        self.parse_chunk2()
 #       self.parse_chunk3()
        self.parse_body()

    def parse_chunk1(self):
        self.chunk1_buf = self.buf[28:self.chunk2_offset]
        self.chunk1_ptrs = []
        for i in range(0, len(self.chunk1_buf), 4):
            ptr, = struct.unpack_from('<L', self.chunk1_buf[i:i+4])
            self.chunk1_ptrs.append(ptr)
#        print("Chunk 1 (%d ptrs):" % len(self.chunk1_ptrs))
#        for i, p in enumerate(self.chunk1_ptrs):
#            if i == 0:
#                print("%x" % p)
#            else:
#                print("%x (+%d)" % (p, self.chunk1_ptrs[i] - self.chunk1_ptrs[i - 1]))

    def parse_chunk2(self):
        self.chunk2_buf = self.buf[self.chunk2_offset:self.chunk3_offset]
#        self.chunk2_ptrs = []
#        for i in range(0, len(self.chunk2_buf), 4):
#            ptr, = struct.unpack_from('<L', self.chunk2_buf[i:i+4])
#            self.chunk2_ptrs.append(ptr)        
#        print("Chunk 2 (offset %x, %d ints):" % (self.chunk2_offset, len(self.chunk2_ptrs)))
#        for p in self.chunk2_ptrs:
#            print("%x" % p)

    def parse_chunk3(self):
        self.chunk3_size, = struct.unpack_from('<L', self.buf[self.chunk3_offset:self.chunk3_offset+4])
 #       print("Chunk 3 (offset %x, size %d):" % (self.chunk3_offset, self.chunk3_size))
        self.chunk3_buf = self.buf[self.chunk3_offset:self.chunk3_offset+self.chunk3_size]
#        self.chunk3_ptrs = []
#        for i in range(0, len(self.chunk3_buf), 4):            
#            ptr, = struct.unpack_from('<L', self.chunk3_buf[i:i+4])
#            self.chunk3_ptrs.append(ptr)        
#        print("Chunk 3 (%d ptrs/ints):" % len(self.chunk3_ptrs))
#        for p in self.chunk3_ptrs:        
#            print("%x" % p)

    def parse_body(self):
        self.body_offset = self.chunk3_offset+self.chunk3_size
        self.frame_offsets = []
        self.frames = {}
        i = self.body_offset
        while i < len(self.buf):
            self.frame_offsets.append(i)
            frame_size, = struct.unpack_from('<L', self.buf[i:i+4])
            self.frames[i] = Frame(i, self.buf[i:i+frame_size])
            i += frame_size

class Frame():
    def __init__(self, offset, buf):
        self.offset = offset
        self.header = buf[:16]
        self.body = buf[16:]
        self.h, self.w, = struct.unpack_from('<HH', self.header[-4:])
        self.rows = []
        i = 0
        while i < self.h*self.w:
            self.rows.append(self.body[i:i+self.w])
            i += self.w            
        print("Offset: %x H: %d W: %d" % (self.offset, self.h, self.w))
        print(self)

    def __repr__(self):
        def asciify(c):
            if c > 31 and c < 128: return chr(c)
            if c == 0: return " "
            return "*"

        image = ''
        for i in range(self.h):
            image += (''.join([asciify(c) for c in self.rows[i]]) + '\n')
        return image
            
        
res = Res(sys.argv[1])
#print("File size: %d bytes" % len(res))
#print("Magic bytes:", "".join([hex(c)[2:] for c in res.magic]))
#print("Header size: %d bytes, %d ptrs" % (len(res.header), len(res.header_ptrs)))
#res.summarize_header()
print("Number of data blocks:", len(res.block_offsets))
#res.summarize_blocks()
#print("Data block offsets:", [hex(a) for a in res.block_offsets])
#print("Begins with pointers to data blocks?:", res.check_header())
for i in range(27, 214):
    block = res.get_data_block(i)
    print("\nBlock %d: %d bytes, %d frames" % (i, len(block), len(block.frame_offsets)))
#    print("number of stanzas?:", block.num_stanzas)
#    print("number of ptrs per stanza?:", block.num_ptrs_per_stanza)
#    print("h1: ", block.h1)
#    print("chunk2_offset: ", block.chunk2_offset)
#    print("h3: ", block.h3)
#    print("h4: ", block.h4)
#    print("h5: ", block.h5)
