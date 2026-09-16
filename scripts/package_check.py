"""Review every releasable file, enforce the safe starter allowlist, and inspect ZIP structure."""

import argparse, ast, hashlib, json, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "artifacts"}
REQUIRED = [
    "README.md",
    "eyes-detected-models/pyproject.toml",
    "eyes-detected-labeler/pyproject.toml",
    "eyes-detected-contracts/pyproject.toml",
    "validation/FINAL_DELIVERY_REPORT.md",
]
ALLOWED = {
    ".py",
    ".md",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".svg",
    ".txt",
    ".sh",
    ".ps1",
    ".js",
    ".example",
    ".cmd",
    ".html",
    ".css",
    ".xml",
}
BINARY_ALLOWLIST = {
    "templates/assets/fundus-retinopathy-eda03.jpg",
    "templates/assets/fonts/ibm-plex-mono-latin-400-normal.woff2",
    "templates/assets/fonts/public-sans-latin-wght-normal.woff2",
}
PATTERNS = [
    r"gh[pousr]_[A-Za-z0-9]{30,}",
    r"hf_[A-Za-z0-9]{25,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"sk-[A-Za-z0-9]{32,}",
]


def files(root=ROOT):
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and not any(x in EXCLUDE or x.endswith(".egg-info") for x in p.relative_to(root).parts)
    )


def inspect(root=ROOT, require_report=True):
    records = []
    for p in files(root):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            raise ValueError(f"Symlink excluded: {rel}")
        if p.stat().st_size > 50 * 1024 * 1024:
            raise ValueError(f"Large file: {rel}")
        if p.suffix not in ALLOWED and rel not in BINARY_ALLOWLIST and p.name not in [
            "Dockerfile",
            "Makefile",
            ".gitignore",
            ".dockerignore",
        ]:
            raise ValueError(f"Unexpected binary/data file: {rel}")
        raw = p.read_bytes()
        if rel in BINARY_ALLOWLIST:
            if not raw:
                raise ValueError(f"Empty file: {rel}")
            records.append({"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            continue
        text = raw.decode("utf-8")
        if not text.strip():
            raise ValueError(f"Empty file: {rel}")
        if any(re.search(pattern, text) for pattern in PATTERNS):
            raise ValueError(f"Potential secret: {rel}")
        if p.suffix == ".py":
            ast.parse(text)
        if p.suffix in [".json", ".jsonl"]:
            for value in text.splitlines() if p.suffix == ".jsonl" else [text]:
                json.loads(value)
        records.append({"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    if require_report:
        for name in REQUIRED:
            if not (root / name).is_file():
                raise ValueError(f"Missing release file: {name}")
    return records


def check_zip(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP path")
        prefix = "eyes-detected-dual-track-starter-v0.2/"
        for n in names:
            if not n.startswith(prefix) or ".." in Path(n).parts or n.startswith("/"):
                raise ValueError("ZIP path violation")
        for name in REQUIRED:
            if prefix + name not in names:
                raise ValueError("ZIP required file missing")
        expected = {prefix + r["path"]: r["sha256"] for r in inspect()}
        if set(names) != set(expected):
            raise ValueError("ZIP/source file set mismatch")
        for name in names:
            if hashlib.sha256(z.read(name)).hexdigest() != expected[name]:
                raise ValueError("ZIP/source hash mismatch")
    return len(names)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--zip")
    p.add_argument("--pre-report", action="store_true")
    a = p.parse_args()
    if a.zip:
        print(f"PASS ZIP: {check_zip(a.zip)} files")
    else:
        print(
            f"PASS file gate: {len(inspect(require_report=not a.pre_report))} reviewed files; only allowlisted GUI assets are binary, common secret scan clear"
        )
