# Optional FiftyOne adapter

Status: SCAFFOLDED / REQUIRES_EXTERNAL_SERVICE. `labeler_bridge.fiftyone.to_fiftyone` converts explicitly supplied local sample descriptors into FiftyOne Sample objects. It does not launch a server, upload images or send tasks to CVAT.

Install a version compatible with your chosen CVAT deployment only when needed. Follow the [official CVAT walkthrough](https://docs.voxel51.com/tutorials/cvat_annotation.html). This optional integration has not been installed or executed in the starter validation. Core tests and labeler conversion do not depend on it.
