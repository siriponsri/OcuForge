import json, random
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from eyes_detected.pipeline.data import load_images, load_targets
from eyes_detected.features.store import NPZFeatureStore, digest
from eyes_detected.mil.attention import AttentionMIL
from eyes_detected.mil.global_average import GlobalAveragePooling
from eyes_detected.ordinal.coral import loss as coral_loss
from eyes_detected.ordinal.corn import CORNHead, loss as corn_loss
from eyes_contracts.protocol import load_protocol


class ResearchMIL(nn.Module):
    def __init__(self, dim, task, pooling="attention_mil", head=None):
        super().__init__()
        if pooling == "attention_mil":
            self.core = AttentionMIL(dim)
        elif pooling == "global_average":
            self.core = GlobalAveragePooling(dim)
        else:
            raise ValueError("Unknown pooling strategy")
        self.binary = nn.Linear(dim, 1)
        self.task = task
        self.pooling = pooling
        self.head = head or ("CORAL" if task == "ordinal" else "BINARY")
        if task == "ordinal" and self.head == "CE":
            self.ordinal_head = nn.Linear(dim, 5)
        elif task == "ordinal" and self.head == "CORN":
            self.ordinal_head = CORNHead(dim)
        elif task == "ordinal" and self.head != "CORAL":
            raise ValueError("Ordinal head must be CE, CORAL, or CORN")

    def forward(self, x, mask):
        r = self.core(x, mask)
        r["binary_logits"] = self.binary(r["embedding"]).squeeze(-1)
        if self.task == "ordinal" and self.head in ["CE", "CORN"]:
            r["dr_logits"] = self.ordinal_head(r["embedding"])
        return r


def load_features(directory, images):
    directory = Path(directory)
    rows = json.loads((directory / "index.json").read_text(encoding="utf-8"))
    index = {r["image_id"]: r for r in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate feature image ID")
    store = NPZFeatureStore(directory / "shards")
    out = {}
    identities = set()
    for im in images:
        if im.image_id not in index:
            raise ValueError("Image missing from feature index")
        r = index[im.image_id]
        meta = r["metadata"]
        if (
            meta["image_id"] != im.image_id
            or meta["dataset_id"] != im.dataset_id
            or meta.get("image_sha256") != im.file_sha256
        ):
            raise ValueError("Feature/image provenance mismatch")
        identities.add(
            (
                meta["encoder_id"],
                meta["encoder_weight_hash"],
                meta["preprocessing_config_hash"],
                meta["tensor_shape"][-1],
            )
        )
        out[im.image_id] = torch.from_numpy(store.get(r["key"], meta)).float()
    if len(identities) != 1:
        raise ValueError("Mixed encoder/preprocessing identities")
    return out, next(iter(identities))


def collate(ids, features, device):
    tensors = [features[i] for i in ids]
    maxn = max(len(x) for x in tensors)
    dim = tensors[0].shape[1]
    x = torch.zeros(len(ids), maxn, dim)
    mask = torch.zeros(len(ids), maxn, dtype=torch.bool)
    for i, t in enumerate(tensors):
        x[i, : len(t)] = t
        mask[i, : len(t)] = True
    return x.to(device), mask.to(device)


def objective(r, ids, targets, task, weights, head="CORAL"):
    primary = "dr_grade" if task == "ordinal" else "binary_dr"
    y = torch.tensor([getattr(targets[i], primary) for i in ids], device=r["dr_logits"].device)
    if task == "ordinal" and head == "CORAL":
        total = coral_loss(r["dr_logits"], y.long())
    elif task == "ordinal" and head == "CORN":
        total = corn_loss(r["dr_logits"], y.long())
    elif task == "ordinal" and head == "CE":
        total = F.cross_entropy(r["dr_logits"], y.long())
    else:
        total = F.binary_cross_entropy_with_logits(r["binary_logits"], y.float())
    total = weights.get("primary", 1.0) * total
    for field, key, factor in [("lesions", "lesion_logits", "lesions"), ("gradable", "qc_logits", "qc")]:
        vals = []
        valid = []
        for i in ids:
            v = getattr(targets[i], field)
            if field == "lesions":
                v = v if v is not None else [None] * 7
            else:
                v = [v]
            vals.append([0 if x is None else x for x in v])
            valid.append([x is not None for x in v])
        logits = r[key] if field == "lesions" else r[key][:, None]
        mask = torch.tensor(valid, dtype=torch.bool, device=logits.device)
        if mask.any():
            target = torch.tensor(vals, dtype=torch.float, device=logits.device)
            total = total + weights.get(factor, 0) * F.binary_cross_entropy_with_logits(
                logits[mask], target[mask]
            )
    return total


def train(
    manifest,
    targets_path,
    features_dir,
    out,
    config_path,
    protocol_path,
    resume=None,
    dataset_path=None,
    cloud=False,
):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    task = config.get("task", "ordinal")
    if task not in ["ordinal", "binary"]:
        raise ValueError("task must be ordinal or binary")
    pooling = config.get("pooling", "attention_mil")
    if pooling not in ["attention_mil", "global_average"]:
        raise ValueError("pooling must be attention_mil or global_average")
    head = config.get("head", "CORAL" if task == "ordinal" else "BINARY")
    if task == "ordinal" and head not in ["CE", "CORAL", "CORN"]:
        raise ValueError("Ordinal head must be CE, CORAL, or CORN")
    images, dataset = load_images(manifest, dataset_path, cloud)
    targets = load_targets(targets_path, images)
    features, identity = load_features(features_dir, images)
    primary = "dr_grade" if task == "ordinal" else "binary_dr"
    train_ids = [
        i.image_id
        for i in images
        if i.split == "TRAIN" and i.image_id in targets and getattr(targets[i.image_id], primary) is not None
    ]
    val_ids = [
        i.image_id
        for i in images
        if i.split == "VAL" and i.image_id in targets and getattr(targets[i.image_id], primary) is not None
    ]
    if not train_ids or not val_ids:
        raise ValueError("Explicit TRAIN and VAL labels required; TEST/SENTINEL never used for selection")
    if task == "ordinal" and any(targets[i].source == "DOCTOR_EXPERIENCE" for i in train_ids + val_ids):
        raise ValueError("Binary experience labels cannot train CORAL")
    device = config.get("device", "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    seed = config.get("seed", 42)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(config.get("cpu_threads", 1))
    epochs = config.get("epochs", 20)
    batch_size = config.get("batch_size", 8)
    if not isinstance(epochs, int) or not isinstance(batch_size, int) or epochs < 1 or batch_size < 1:
        raise ValueError("Positive epochs/batch_size required")
    weights = config.get("loss_weights", {"primary": 1, "lesions": 0.2, "qc": 0.1})
    if any(not np.isfinite(v) or v < 0 for v in weights.values()) or weights.get("primary", 1) <= 0:
        raise ValueError("Invalid loss weights")
    _, protocol = load_protocol(protocol_path)
    fingerprint = digest(
        {
            "config": config,
            "protocol": protocol.model_dump(),
            "images": [i.model_dump() for i in images],
            "targets": [targets[k].model_dump() for k in sorted(targets)],
            "feature_identity": identity,
        }
    )
    model = ResearchMIL(identity[-1], task, pooling, head).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.get("learning_rate", 0.001),
        weight_decay=config.get("weight_decay", 0.01),
    )
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    start = 0
    best = float("inf")
    history = []
    if resume:
        checkpoint = torch.load(resume, map_location=device, weights_only=True)
        if checkpoint["fingerprint"] != fingerprint:
            raise ValueError("Resume configuration/data/protocol mismatch")
        model.load_state_dict(checkpoint["state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        start = checkpoint["epoch"] + 1
        best = checkpoint["best"]
        history = checkpoint["history"]
    elif (out / "last.pt").exists():
        raise ValueError("Run output already exists; use explicit --resume or a fresh directory")
    run = {
        "status": "RUNNING",
        "task": task,
        "pooling": pooling,
        "head": head,
        "fingerprint": fingerprint,
        "feature_identity": list(identity),
        "protocol": protocol.model_dump(),
        "seed": seed,
        "device": device,
        "torch": str(torch.__version__),
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "train_ids": train_ids,
        "val_ids": val_ids,
        "scientific_result_eligible": False,
    }
    (out / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    try:
        for epoch in range(start, epochs):
            order = random.Random(seed + epoch).sample(train_ids, len(train_ids))
            model.train()
            losses = []
            for offset in range(0, len(order), batch_size):
                ids = order[offset : offset + batch_size]
                x, mask = collate(ids, features, device)
                optimizer.zero_grad()
                value = objective(model(x, mask), ids, targets, task, weights, head)
                if not torch.isfinite(value):
                    raise RuntimeError("Nonfinite training loss")
                value.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.get("clip_grad_norm", 5.0))
                optimizer.step()
                losses.append(float(value.detach()))
            model.eval()
            vsum = 0
            with torch.no_grad():
                for offset in range(0, len(val_ids), batch_size):
                    ids = val_ids[offset : offset + batch_size]
                    x, mask = collate(ids, features, device)
                    vsum += float(objective(model(x, mask), ids, targets, task, weights, head)) * len(ids)
            vloss = vsum / len(val_ids)
            history.append({"epoch": epoch, "train_loss": sum(losses) / len(losses), "val_loss": vloss})
            improved = vloss < best
            best = min(best, vloss)
            ckpt = {
                "state_dict": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "best": best,
                "history": history,
                "fingerprint": fingerprint,
                "task": task,
                "pooling": pooling,
                "head": head,
                "dim": identity[-1],
                "feature_identity": list(identity),
                "protocol": protocol.model_dump(),
                "seed": seed,
                "training_dataset_ids": sorted({i.dataset_id for i in images if i.image_id in train_ids}),
                "created_at": run["timestamp"],
            }
            tmp = out / "last.tmp"
            torch.save(ckpt, tmp)
            tmp.replace(out / "last.pt")
            if improved:
                torch.save(ckpt, out / "best.pt")
            (out / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        run["status"] = "COMPLETED"
        run["epochs_completed"] = len(history)
        run["best_val_loss"] = best
    except Exception:
        run["status"] = "FAILED"
        (out / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
        raise
    (out / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    return run
