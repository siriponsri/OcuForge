import hashlib
from eyes_contracts.models import ImageManifest
from eyes_contracts.validators import check_splits


def assign_splits(images, seed=42, train=0.7, val=0.15):
    if not images or not 0 < train < 1 or not 0 <= val < 1 or train + val >= 1:
        raise ValueError("Invalid split proportions")
    if any(i.split != "UNASSIGNED" for i in images):
        raise ValueError("Existing split is frozen; refusing reassignment")
    # Union every available grouping key AND exact hash. Mixed metadata never breaks groups.
    parent = list(range(len(images)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen = {}
    for i, im in enumerate(images):
        for field in ["patient_pseudo_id", "eye_id", "visit_id", "file_sha256"]:
            value = getattr(im, field)
            if not value:
                continue
            key = (field, value)
            if key in seen:
                parent[root(i)] = root(seen[key])
            else:
                seen[key] = i
    groups = {}
    for i, im in enumerate(images):
        groups.setdefault(root(i), []).append(im.image_id)
    out = []
    for i, im in enumerate(images):
        key = min(groups[root(i)])
        v = int(hashlib.sha256(f"{seed}:{key}".encode()).hexdigest()[:12], 16) / 16**12
        data = im.model_dump()
        data["split"] = "TRAIN" if v < train else "VAL" if v < train + val else "SENTINEL"
        out.append(ImageManifest.model_validate(data))
    check_splits(out)
    unit = next(
        (f for f in ["patient_pseudo_id", "eye_id", "visit_id"] if all(getattr(i, f) for i in images)),
        "image_id",
    )
    return out, {
        "grouping": unit,
        "leakage_risk": unit != "patient_pseudo_id",
        "seed": seed,
        "policy": "union_all_identifiers_and_exact_hash",
    }
