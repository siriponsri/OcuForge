import argparse
from .validators import read_records, check_splits
from .models import ImageManifest


def main():
    p = argparse.ArgumentParser(description="Eye Detected contracts v0.1: schema + semantic validation")
    p.add_argument("command", choices=["validate"])
    p.add_argument("path")
    a = p.parse_args()
    try:
        records = read_records(a.path)
        if all(isinstance(x, ImageManifest) for x in records):
            check_splits(records)
    except (ValueError, OSError) as e:
        p.exit(2, f"Validation failed: {e}\n")
    print(f"VALID: {len(records)} record(s)")


if __name__ == "__main__":
    main()
