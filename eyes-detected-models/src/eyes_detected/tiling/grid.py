from dataclasses import dataclass, asdict
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class PatchConfig:
    canvas: int = 1024
    grid: int = 5
    patch: int = 224
    resize_policy: str = "letterbox"
    mean: tuple = (0.485, 0.456, 0.406)
    std: tuple = (0.229, 0.224, 0.225)

    def __post_init__(self):
        if self.grid < 2 or not 0 < self.patch <= self.canvas or self.resize_policy != "letterbox":
            raise ValueError("Invalid patch configuration; letterbox required")
        if (self.canvas - self.patch) / (self.grid - 1) > self.patch:
            raise ValueError("Grid leaves uncovered gaps")
        if len(self.mean) != 3 or len(self.std) != 3 or any(x <= 0 for x in self.std):
            raise ValueError("Invalid normalization")


def tile(image, config=PatchConfig()):
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image)
    image = image.convert("RGB")
    sw, sh = image.size
    scale = min(config.canvas / sw, config.canvas / sh)
    rw, rh = max(1, round(sw * scale)), max(1, round(sh * scale))
    ox, oy = (config.canvas - rw) // 2, (config.canvas - rh) // 2
    canvas = Image.new("RGB", (config.canvas, config.canvas))
    canvas.paste(image.resize((rw, rh), Image.Resampling.BILINEAR), (ox, oy))
    starts = np.rint(np.linspace(0, config.canvas - config.patch, config.grid)).astype(int)
    patches = []
    coords = []
    for y in starts:
        for x in starts:
            box = (int(x), int(y), int(x + config.patch), int(y + config.patch))
            patches.append(np.asarray(canvas.crop(box)).copy())
            coords.append(
                {
                    "index": len(coords),
                    "canvas_xyxy": list(box),
                    "source_xyxy": [
                        (box[0] - ox) * sw / rw,
                        (box[1] - oy) * sh / rh,
                        (box[2] - ox) * sw / rw,
                        (box[3] - oy) * sh / rh,
                    ],
                }
            )
    return np.stack(patches), {
        "config": asdict(config),
        "source_size": [sw, sh],
        "resized_size": [rw, rh],
        "offset": [ox, oy],
        "patches": coords,
    }


def normalize(patches, config=PatchConfig()):
    return (
        (
            (patches.astype(np.float32) / 255 - np.array(config.mean, dtype=np.float32))
            / np.array(config.std, dtype=np.float32)
        )
        .transpose(0, 3, 1, 2)
        .copy()
    )


def source_to_canvas(x, y, metadata):
    sw, sh = metadata["source_size"]
    rw, rh = metadata["resized_size"]
    ox, oy = metadata["offset"]
    return x * rw / sw + ox, y * rh / sh + oy


def canvas_to_source(x, y, metadata):
    sw, sh = metadata["source_size"]
    rw, rh = metadata["resized_size"]
    ox, oy = metadata["offset"]
    return (x - ox) * sw / rw, (y - oy) * sh / rh
