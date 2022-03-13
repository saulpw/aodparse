import struct
import parse95

from PIL import Image
from visidata import VisiData, Sheet, AttrColumn, AttrDict, vd, ENTER


@VisiData.api
def open_res(vd, p):
    return ResSheet(p.name, source=p)


class ResSheet(Sheet):
    rowtype = 'blocks'  # rowdef: parse95.DataBlock
    columns = [
        AttrColumn('index', type=int),
        AttrColumn('offset', type=int),
        AttrColumn('size'),
        AttrColumn('magic'),
    ]
    def iterload(self):
        yield from parse95.Res(str(self.source)).iter_blocks()

    def openRow(self, row):
        return FramesSheet(row.index, source=row)

    def openRows(self, rows):
        frame_rows = []
        for row in rows:
            frame_rows.extend(row.iter_frames())
        return FramesSheet("many rows", rows=frame_rows)

class FramesSheet(Sheet):
    rowtype = 'frames'  # rowdef: parse95.Frame
    columns = [
        AttrColumn('index', type=int),
        AttrColumn('offset', type=int),
        AttrColumn('h', type=int),
        AttrColumn('w', type=int),
        AttrColumn('rows'),
        AttrColumn('hex_rows'),
    ]
    def iterload(self):
        yield from self.source.iter_frames()

@VisiData.api
def save_frames(vd, p, rows):
    frames = []
    for row in rows:
        im = Image.new("L", (row.w, row.h))
        im.putdata(b''.join(row.byte_rows))
        frames.append(im)
    frames[0].save(str(p), append_images=frames[1:], optimize=False, save_all=True, duration=100, loop=0)

ResSheet.addCommand('g'+ENTER, "dive-selected", "vd.push(sheet.openRows(selectedRows))")
FramesSheet.addCommand("X", "save-frame", "vd.save_frames(Path('foo.png'), rows)")
