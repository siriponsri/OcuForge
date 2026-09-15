from pathlib import Path
import yaml
from eyes_contracts.models import DatasetManifest


class DatasetRegistry:
    def __init__(self):
        self.datasets = {}

    def register(self, record):
        d = DatasetManifest.model_validate(record)
        if d.dataset_id in self.datasets:
            raise ValueError("Duplicate dataset ID")
        self.datasets[d.dataset_id] = d
        return d

    def load(self, path):
        return self.register(yaml.safe_load(Path(path).read_text()))
