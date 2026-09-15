import numpy as np
from eyes_contracts.models import Geometry


def rle_encode(mask):
    flat = np.asarray(mask).ravel(order="C")
    if not np.isin(flat, [0, 1]).all():
        raise ValueError("Binary mask required")
    counts = []
    value = 0
    run = 0
    for x in flat:
        if x == value:
            run += 1
        else:
            counts.append(run)
            run = 1
            value = int(x)
    counts.append(run)
    return counts


def rle_decode(counts, size):
    if sum(counts) != size[0] * size[1] or any(int(x) != x or x < 0 for x in counts):
        raise ValueError("Invalid RLE")
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(np.uint8).reshape(size)


def to_cvat(geometry, width, height):
    g = Geometry.model_validate(geometry.model_dump())
    if width < 2 or height < 2:
        raise ValueError("Image dimensions must exceed 1")
    if g.type == "mask":
        if tuple(g.mask_size) != (height, width):
            raise ValueError("Mask/image size mismatch")
        return {"type": "mask", "points": g.mask_rle + [0, 0, width - 1, height - 1]}
    if g.type == "image_presence":
        return {"type": "tag", "points": []}
    xy = [v * ((width - 1) if i % 2 == 0 else (height - 1)) for i, v in enumerate(g.coordinates_norm)]
    if g.type == "ellipse":
        x0, y0, x1, y1 = xy
        xy = [(x0 + x1) / 2, (y0 + y1) / 2, x1, y0]
    return {"type": {"point": "points", "box": "rectangle"}.get(g.type, g.type), "points": xy}


def from_cvat(shape, width, height):
    typ = shape["type"]
    pts = shape.get("points", [])
    if typ == "mask":
        if len(pts) < 5 or any(int(v) != v for v in pts):
            raise ValueError("Invalid CVAT mask coordinates")
        x0, y0, x1, y1 = map(int, pts[-4:])
        counts = list(map(int, pts[:-4]))
        if not 0 <= x0 <= x1 < width or not 0 <= y0 <= y1 < height:
            raise ValueError("Mask outside image")
        crop = rle_decode(counts, (y1 - y0 + 1, x1 - x0 + 1))
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[y0 : y1 + 1, x0 : x1 + 1] = crop
        return Geometry(type="mask", mask_size=(height, width), mask_rle=rle_encode(mask))
    if typ == "ellipse":
        if shape.get("rotation", 0) != 0:
            raise ValueError("Rotated ellipse unsupported; use mask")
        cx, cy, rx, ty = pts
        dx = abs(rx - cx)
        dy = abs(ty - cy)
        pts = [cx - dx, cy - dy, cx + dx, cy + dy]
    coords = [v / ((width - 1) if i % 2 == 0 else (height - 1)) for i, v in enumerate(pts)]
    return Geometry(
        type={"points": "point", "rectangle": "box", "tag": "image_presence"}.get(typ, typ),
        coordinates_norm=coords,
    )
