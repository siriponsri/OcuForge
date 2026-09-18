# R3 IDRiD ROI baseline

R3 is a separate, research-only ROI lesion-classifier track. It does not reuse global DR MIL features or MIL
attention and does not train the global DR model.

The input and target contracts are `r3_roi_input.v0.1` and `r3_roi_target.v0.1` in the contracts package. Each input
row preserves the IDRiD source image identity/hash, ROI image hash, released `TRAIN`/`TEST` split, pixel and normalized
geometry, and one provenance entry for each supported mask class. The only supported classes are:

```text
MICROANEURYSM
INTRARETINAL_HEMORRHAGE
HARD_EXUDATE
SOFT_EXUDATE
```

Missing masks and unannotated/unsupported regions produce `UNKNOWN_OR_UNSUPPORTED_FINDING` target rows and are excluded
from supervision with an explicit report entry. `WEAK_NEGATIVE_FOR_SUPPORTED_CLASS` is limited to an explicit
present-but-empty mask. `NO_SUPPORTED_LESION_IN_ROI` is accepted only for an explicit clean-negative ROI with complete
supported-mask coverage and absence evidence for all four classes. It is ROI-scoped and is not `GLOBAL_NO_DR`.

The executable baseline is `eyes_detected.lesions.roi_classifier`. It extracts deterministic RGB features from the ROI
crop and trains four masked binary heads. A positive row supervises only its declared class; a weak negative supervises
only its explicitly empty class; a clean negative supervises all four classes. This avoids turning unknown classes into
negative labels. Outputs are engineering evidence only and `scientific_result_eligible` remains false.

The command-line entrypoint is available through `eyes-models`:

```powershell
eyes-models r3-train --inputs roi_inputs.jsonl --targets roi_targets.jsonl --data-root C:\data\idrid --out artifacts\r3
eyes-models r3-evaluate --inputs roi_inputs.jsonl --targets roi_targets.jsonl --data-root C:\data\idrid --model artifacts\r3\model.npz --out artifacts\r3-test
```

The equivalent Python API is:

```python
from eyes_detected.lesions.roi_classifier import evaluate_roi_classifier, train_roi_classifier

train_roi_classifier("roi_inputs.jsonl", "roi_targets.jsonl", "/data/idrid", "artifacts/r3")
evaluate_roi_classifier(
    "roi_inputs.jsonl", "roi_targets.jsonl", "/data/idrid", "artifacts/r3/model.npz", "artifacts/r3-test"
)
```

The implementation validates the complete row inventory before selecting `TRAIN` or `TEST`; it does not reshuffle or
silently drop released IDRiD image identities. DDR/OIA-DDR is outside this contract and implementation.
