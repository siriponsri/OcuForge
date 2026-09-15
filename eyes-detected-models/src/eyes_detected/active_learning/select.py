import numpy as np
from eyes_contracts.models import AnnotationBatch
from eyes_contracts.validators import check_splits, validate_batch


def select_batch(images, features, n, model_id="TINY_TEST_001", batch_id="SYNTHETIC_R0", disagreement=None):
    check_splits(images)
    x = np.asarray(features, dtype=float)
    if x.ndim != 2 or len(x) != len(images) or not np.isfinite(x).all():
        raise ValueError("Features must align with image manifest")
    eligible = sorted(
        [i for i, m in enumerate(images) if m.split in ["TRAIN", "UNASSIGNED"]],
        key=lambda i: images[i].image_id,
    )
    if not 0 < n <= len(eligible):
        raise ValueError("Insufficient eligible non-evaluation images")
    if len({images[i].dataset_id for i in eligible}) != 1:
        raise ValueError("One dataset per batch")
    d = np.zeros(len(images)) if disagreement is None else np.asarray(disagreement, float)
    if d.shape != (len(images),) or not np.isfinite(d).all() or np.any((d < 0) | (d > 1)):
        raise ValueError("Invalid disagreement scores")
    selected = []
    covered = set()
    reasons = {}
    while len(selected) < n:
        remaining = [i for i in eligible if i not in selected]

        def score(i):
            domain = (images[i].site_id, images[i].camera_model)
            distance = (
                min(np.linalg.norm(x[i] - x[j]) for j in selected)
                if selected
                else -np.linalg.norm(x[i] - x[eligible].mean(0))
            )
            return (domain not in covered, float(distance), float(d[i]))

        i = max(remaining, key=score)
        domain = (images[i].site_id, images[i].camera_model)
        reasons[i] = (
            ["DIVERSITY"]
            + (["SITE_CAMERA_COVERAGE"] if domain not in covered else [])
            + (["MODEL_DISAGREEMENT"] if d[i] > 0.5 else [])
        )
        selected.append(i)
        covered.add(domain)
    batch = AnnotationBatch.model_validate(
        {
            "batch_id": batch_id,
            "dataset_id": images[selected[0]].dataset_id,
            "selection": {"strategy": "coverage_farthest_first_v1", "model_manifest_id": model_id},
            "requested_n": n,
            "items": [
                {
                    "image_id": images[i].image_id,
                    "priority": 1 - rank / max(n, 1),
                    "reasons": reasons[i],
                    "split": images[i].split,
                    "locked_sentinel": False,
                }
                for rank, i in enumerate(selected)
            ],
        }
    )
    return validate_batch(batch, images)
