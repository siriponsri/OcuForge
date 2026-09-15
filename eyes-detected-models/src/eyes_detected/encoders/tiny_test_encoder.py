from torch import nn


class TinyTestEncoder(nn.Module):
    """Explicit synthetic-only encoder. Never used as DINOv3 fallback."""

    encoder_id = "TinyTestEncoder-test-only"

    def __init__(self, dim=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 8, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(8, dim)
        )

    def forward(self, x):
        return self.net(x)
