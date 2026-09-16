"""Small model-side heads shared by candidate-specific adapters."""

from torch import nn


class MulticlassImageClassifier(nn.Module):
    """Wrap an image encoder with the initial V3 five-class CE head."""

    def __init__(self, encoder, feature_dim, num_classes=5):
        super().__init__()
        if num_classes != 5:
            raise ValueError("Global V3 CE comparison requires five DR grades")
        self.encoder = encoder
        self.classifier = nn.Linear(feature_dim, num_classes)

    def forward(self, images):
        features = self.encoder(images)
        if features.ndim != 2 or features.shape[-1] != self.classifier.in_features:
            raise ValueError("Image encoder must return [batch, feature] tensors")
        return self.classifier(features)
