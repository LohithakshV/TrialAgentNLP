"""Vectorize the generated artwork silhouettes; never invent logo paths."""
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
import vtracer

ROOT = Path(__file__).resolve().parents[1]
for name, color in [('trialagent-mark', '#BCECD5'), ('warning', '#F29A9A'), ('privacy', '#EDEDE6'), ('questions', '#BCECD5'), ('learning', '#BCECD5')]:
    image = Image.open(ROOT / 'public' / 'brand' / f'{name}.png').convert('RGBA')
    image.thumbnail((512, 512))
    # Discard transparent RGB noise before tracing; preserve the visible silhouette.
    mask = Image.new('RGB', image.size, 'white')
    mask.putdata([(0, 0, 0) if a > 180 else (255, 255, 255) for r, g, b, a in image.getdata()])
    temporary = ROOT / '.artifacts' / f'{name}-trace.png'
    mask.save(temporary)
    output = ROOT / 'public' / 'brand' / f'{name}.svg'
    vtracer.convert_image_to_svg_py(str(temporary), str(output), colormode='binary', mode='spline', filter_speckle=24, path_precision=2)
    tree = ET.parse(output)
    root = tree.getroot()
    root.set('viewBox', f'0 0 {image.width} {image.height}')
    for node in root:
        if node.tag.endswith('path'):
            node.set('fill', color)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    tree.write(output, encoding='utf-8', xml_declaration=True)
    print(name, output.stat().st_size)
