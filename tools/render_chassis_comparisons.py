#!/usr/bin/env python3
"""Render English-labeled chassis comparisons from locally obtained QTS assets.

Requires Pillow and PyGObject/GdkPixbuf (with SVG support). Does not access a NAS.
Vendor SVG/CSS inputs are supplied locally and are not part of this repository.
"""
from argparse import ArgumentParser
from pathlib import Path
import xml.etree.ElementTree as ET

import gi
from PIL import Image, ImageDraw, ImageFont

gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--original-dir', type=Path, required=True)
    parser.add_argument('--adapted-dir', type=Path, required=True)
    parser.add_argument('--network-css', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--font', default='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    css = args.network_css.read_text()
    font = lambda size: ImageFont.truetype(args.font, size)

    def render(face, custom, dark=False, selected=False):
        name = f'ts_873a_{face}' + ('.candidate.svg' if custom else '.svg')
        root = ET.parse((args.adapted_dir if custom else args.original_dir) / name).getroot()
        for parent in root.iter():
            for child in list(parent):
                if child.tag == f'{{{NS}}}style':
                    parent.remove(child)
        # Dark rules are a fixture, not extracted mobile CSS or a live capture.
        ET.SubElement(root, f'{{{NS}}}style').text = css + (
            '\n.shape,.others,.off,.on{stroke:#aaa}' if dark else '')
        if selected:
            target = 'hd_0' if face == 0 else 'ethernet_3'
            group = next(node for node in root.iter() if node.get('id') == target)
            for node in group.iter():
                if node.get('class') == 'off':
                    node.set('class', 'off on')
        loader = GdkPixbuf.PixbufLoader.new_with_type('svg')
        loader.set_size(270, 161)
        loader.write(ET.tostring(root))
        loader.close()
        pix = loader.get_pixbuf()
        mode = 'RGBA' if pix.get_has_alpha() else 'RGB'
        image = Image.frombytes(mode, (pix.get_width(), pix.get_height()),
                                pix.get_pixels(), 'raw', mode, pix.get_rowstride()).convert('RGBA')
        background = Image.new('RGBA', (270, 162), '#1d1d1d' if dark else 'white')
        background.alpha_composite(image)
        return background.convert('RGB')

    comparison = Image.new('RGB', (620, 450), '#f4f5f7')
    draw = ImageDraw.Draw(comparison)
    draw.text((18, 10), '270 px: original (left), custom (right)', font=font(20), fill='#222')
    draw.text((18, 38), 'Offline render; not a live QTS capture', font=font(15), fill='#444')
    for face, label in enumerate(['Front', 'Rear']):
        y = 85 + face * 185
        draw.text((20, y - 23), label, font=font(15), fill='#222')
        for custom in [False, True]:
            comparison.paste(render(face, custom), (20 + int(custom) * 310, y))
    comparison.save(args.output_dir / 'before-after-270px.png')

    themes = Image.new('RGB', (1160, 510), '#eeeeee')
    draw = ImageDraw.Draw(themes)
    draw.text((15, 10), 'Transparent interiors at 270 px: native light CSS and simulated dark theme',
              font=font(19), fill='#222')
    draw.text((15, 38), 'Offline render. Dark rules and selections are test fixtures, not live mobile data.',
              font=font(16), fill='#444')
    for face, label in enumerate(['Front', 'Rear']):
        for dark in [False, True]:
            for selected in [False, True]:
                x = 15 + int(dark) * 570 + int(selected) * 280
                y = 110 + face * 220
                caption = ('Dark fixture' if dark else 'Native light CSS') + (' / selected' if selected else ' / neutral')
                draw.text((x, y - 24), caption, font=font(15), fill='#222')
                themes.paste(render(face, True, dark, selected), (x, y))
        draw.text((15, 65 + face * 220), label, font=font(15), fill='#444')
    themes.save(args.output_dir / 'transparent-light-dark.png')
    print('Rendered two English-only comparison sheets; no NAS operations.')


if __name__ == '__main__':
    main()
