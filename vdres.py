import struct
import parse95

from visidata import VisiData, Sheet, AttrColumn, AttrDict, vd


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
