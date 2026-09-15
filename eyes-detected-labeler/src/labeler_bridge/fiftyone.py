def to_fiftyone(samples):
    """Optional local curation adapter; never launches a server or sends data."""
    try:
        import fiftyone as fo
    except ImportError:
        raise RuntimeError("Optional FiftyOne is not installed; see fiftyone_adapter/README.md") from None
    return [fo.Sample(filepath=s["local_path"], image_id=s["image_id"]) for s in samples]
