import struct

from visidata import VisiData, Sheet, ItemColumn, AttrDict


@VisiData.api
def open_res(vd, p):
    return ResSheet(p.name, source=p)


class ResSheet(Sheet):
    columns = [
        ItemColumn('height', 'h', type=int),
        ItemColumn('width', 'w', type=int),
        ItemColumn('image'),
        ItemColumn('filepos', type=int),
    ]
    def iterload(self):
        def asciify(c):
            if c > 31 and c < 128: return chr(c)
            if c == 0: return " "
            return "*"

        contents = self.source.read_bytes()
        i = contents.index(b'D3GR')
        contents = contents[i+4:]

        while contents:
            try:
                i = contents.index(b'D3GR')
            except ValueError:
                i = len(contents)-1
            buf = contents[888:i]
            contents = contents[i+4:]

            i = 0
            while i < len(buf):
                _, _, _, h, w = struct.unpack_from('<IIIHH', buf[i:])
                i += 16
                row = AttrDict(h=h, w=w, image=[])
                for j in range(h):
                    spriterow = ''.join([asciify(c) for c in buf[i:i+w]])
                    row.image.append(spriterow)
                    i += w
                yield row
