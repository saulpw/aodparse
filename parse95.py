import struct
import sys

from PIL import Image, ImageDraw

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
    b'\x2c\x03\x00\x00': "animation",
    b'\x3c\x03\x00\x00': "animation",
    b'\x44\x03\x00\x00': "animation",
    b'\x50\x03\x00\x00': "animation",

    b'\x2e\x00\x00\x00': "selectors/icons", # not sure what exactly these things are, multi-frame
    b'\x30\x00\x00\x00': "animated icon(s)",
    b'\x3c\x01\x00\x00': "animated icon(s)",
    b'\x44\x00\x00\x00': "animated icon(s)",
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
        # guesses: self.c = delay, self.e = frame to composite onto
        self.size, self.b, self.c, self.d, self.x, self.y, self.h, self.w = struct.unpack_from('<HHHHHHHH', self.header)
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

def make_palette():
    palette = []
    with open('ANVIL0.PAL', 'rb')  as f:
        palette = list(f.read())
    return [4*b for b in palette]

def make_img(palette, w, h, data):
    if w*h != len(data):
#        print(w, h, len(data))
        return
    if all(x == b'\xfe' for x in data):
        return
    im = Image.new("L", (w, h))
    im.putpalette(palette, rawmode="RGB")
    im.putdata(data)
    return im

def make_mask(w, h, data):
    if w*h != len(data):
        return
    im = Image.new("L", (w, h))
    im.putdata(data)
    return im

def frames_to_imgs(frames, block_type):
    palette = make_palette()
    imgs = []
#    if frames:
#        h, w = frames[0].h, frames[0].w
    h, w = 0, 0
    for frame in frames:
        if frame.h > h:
            h = frame.h
        if frame.w > w:
            w = frame.w
    for frame in frames:
        img = make_img_frame(palette, imgs, frame, w, h, block_type)
        if img:
            imgs.append(img)
    return imgs

def make_img_frame(palette, imgs, frame, w, h, block_type):
    pad = (frame.h != h or frame.w != w)
    if not block_type.startswith('animat') or not pad:
        return make_img(palette, frame.w, frame.h, b''.join(frame.byte_rows))
    left = b'\x00' * frame.x
    right = b'\x00' * (w - frame.w - frame.x)
    top = [b'\x00' * w] * frame.y
    bottom = [b'\x00' * w] * (h - frame.h - frame.y)

    padded = [b'\x00' * w] * frame.y
    mask = [b'\x00' * w] * frame.y
    for row in frame.byte_rows:
        padded.append(b''.join([left,row,right]))
        mask.append(b''.join([b'\xff' if p else b'\x00' for p in padded[-1]]))
    if bottom:
        padded = padded + bottom
        mask = mask + bottom

    img = make_img(palette, w, h, b''.join(padded))
    mask = make_mask(w, h, b''.join(mask))
    if img and mask and imgs:
        return Image.composite(img, imgs[-1], mask)
    return img

def make_sprite_sheet(spec, filename, outfile, w=1500, h=3000):
    # each element of rows is a list of block indices
    rows = []
    with open(spec, 'r') as f:
        rows = [list(map(int, x.split())) for x in f.readlines() if x and not x.startswith('#')]

    res = Res(filename)
    palette = make_palette()
    maxw = 0 # computed
    minw = 20
    bkgds = [make_img(palette, w, h, b'\x6a'*w*h) for i in range(12)]
    draws = [ImageDraw.Draw(bkgd) for bkgd in bkgds]
    imgs = []
    x, y = 0, 0
    maxrowh = 0

    for draw in draws:
        draw.text((x+5, y), "ANVIL OF DAWN (1995)")
        draw.text((x+5, y+12), f"numbers refer to data blocks in {filename}")
        draw.text((x+5, y+24), "extracted by saul.pw & peskin (2022)")

    y += 50

    blocks = list(res.iter_blocks())
    for row in rows:
        y += maxrowh + 20
        maxrowh = 0
        x = 0
        for blocknum in row:
            x += 5
            block = blocks[blocknum]
            if block.block_type != "graphic":
                print("block type is not 'graphic' for block", blocknum)
                continue

            imgs = frames_to_imgs(list(block.iter_frames()), block.block_subtype)
            if imgs:
                print(f"{blocknum}") #  {len(imgs)} imgs for block {blocknum)
            else:
                continue

            for draw in draws:
                draw.text((x, y-12), str(blocknum))

            oldx = x
            for i, bkgd in enumerate(bkgds):
                img = imgs[i] if i < len(imgs) else imgs[0]
                x = oldx
                if x + img.width > w:
                    print("running off the right edge for block", blocknum)
                    break
                if block.block_subtype.startswith('animat'):
                    bkgd.paste(img, (x, y))
                else:
                    for img in imgs:
                        bkgd.paste(img, (x, y))
                        x += max(img.width + 5, minw)
                        maxrowh = max(maxrowh, img.height)
            if block.block_subtype.startswith('animat'):
                x += max(img.width + 5, minw)
                maxrowh = max(maxrowh, img.height)
                print(f"{len(imgs)} frames in animation block {blocknum}", file=sys.stderr)
            maxw = max(maxw, x)
    bkgds[0].save(outfile, append_images=bkgds[1:], optimize=False, save_all=True, duration=150, loop=0)
    return maxw, y + maxrowh + 20

if __name__ == '__main__':
#    res = Res(sys.argv[1])
#    for i, block in enumerate(res):
#        print("Block %d: %s" % (i, block))
    w, h = make_sprite_sheet(*sys.argv[1:])
    make_sprite_sheet(*sys.argv[1:], w, h)
