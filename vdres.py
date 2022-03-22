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
        AttrColumn('offset', type=int, fmtstr='{:x}'),
        AttrColumn('size'),
        AttrColumn('block_type'),
        AttrColumn('block_subtype'),
        AttrColumn('type_id_str'),
        AttrColumn('subtype_id_str'),
        AttrColumn('header_str')
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


def make_palette():
    palette = []
    with open('ANVIL0.PAL', 'rb')  as f:
        palette = list(f.read())
    return [4*b for b in palette]

def make_img(palette, frame):
    im = Image.new("L", (frame.w, frame.h))
    im.putpalette(palette, rawmode="RGB")
    im.putdata(b''.join(frame.byte_rows))
    return im

@VisiData.api
def save_frames(vd, p, rows):
    palette = make_palette()
    frames = []
    for row in rows:
        frames.append(make_img(palette, row))
    frames[0].save(str(p), append_images=frames[1:], optimize=False, save_all=True, duration=100, loop=0)

@VisiData.api
def make_gallery(vd, dirname, blocks):
    palette = make_palette()

    head = "<!DOCTYPE html> <head> <link rel='stylesheet' href='gallery.css'> </head> "
    toc = f"<h1>{vd.sheet.source} Blocks </h1> <div class='toc'> "
    body = "<body> "

    res_dir = dirname.joinpath(f"{vd.sheet.source}_resources")
    if not res_dir.exists():
        res_dir.mkdir()

    for block in blocks:
        body += f"<h1 id={str(block.index)}> {str(block.index)} </h1> <div class='block'> "
        toc += f"<div class='tocitem'> <a href=#{str(block.index)}> {str(block.index)} </a> </div>"

        # list non-graphic blocks in the gallery but don't attempt to parse content
        if block.block_type != "graphic":
            body += "</div> "
            continue

        for frame in block.iter_frames():
            # display a broken img link for unparseable frames
            img_path = str(res_dir.joinpath(f"{str(block.index)}_{str(frame.index)}.png"))
            if frame.byte_rows:
                im = make_img(palette, frame)
                im.save(img_path)
            body += f"<div class='frame'> <a target='_blank' href={img_path}> <img src={img_path}> </a> </div> "
        body += "</div> "

    toc += "</div> "
    html = head + toc + body + "</body> </html>"
    with dirname.joinpath(f'{vd.sheet.source}_gallery.html').open('w') as f:
        f.write(html)

ResSheet.addCommand('g'+ENTER, "dive-selected", "vd.push(sheet.openRows(selectedRows))")

# just create the gallery in the current dir for now
# TODO: make the path an argument
ResSheet.addCommand("X", "make-gallery", "vd.make_gallery(Path(''), selectedRows)")

FramesSheet.addCommand("X", "save-frame", "vd.save_frames(Path('foo.png'), rows)")
