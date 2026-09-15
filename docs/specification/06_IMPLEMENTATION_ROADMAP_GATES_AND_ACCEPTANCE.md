# DUAL-TRACK IMPLEMENTATION ROADMAP, GATES & ACCEPTANCE

## 0. Parallel schedule

Indicative:

```text
MONTH    TRACK A — MODEL                  TRACK B — ANNOTATION
────────────────────────────────────────────────────────────────
M1       data registry/audit              label schema + CVAT setup
         tiling/tests                     contracts + guides

M2       public dataset adapters          prediction import/export
         encoder adapter                  geometry workflow
         feature store                    synthetic dry-run

M3       DINOv3 feature bake-off          MA point workflow
         MIL + CORAL                      lesion region workflow
         source baseline                  SAM integration exploration

M4       lesion auxiliary/pre-label       adjudication/provenance
         QC/OOD                           usability dry-run
         local embedding bank             AL batch import

M5       zero-label local analysis        Track A pre-label integration
         adaptation baselines             public-data rehearsal
         AL selector                      doctor pilot readiness

M6       freeze first expert batch        freeze annotation guide
         sentinel protocol                READY FOR DOCTOR
                      │
                      └──────────────┐
                                     ▼
M7                              first clinician batch
                                     ↓
M8       local supervised refinement + active learning
```

Timeline is indicative and should be updated from actual capacity.

---

# 1. Starter generation gate — current GPT Work task

Must deliver:
- repository skeletons;
- working synthetic tests;
- contracts;
- Docker setup;
- no real dataset download;
- no full model training;
- no doctor dependency.

Status:
```text
G0 STARTER FOUNDATION
```

---

# 2. G1 — Data foundation

Pass when:
- dataset registry implemented;
- MMRDR/IDRiD/DDR/etc adapters specified;
- label-scope validation works;
- local manifest schema works;
- leakage checks work;
- synthetic sample passes.

No performance metric required.

---

# 3. G2 — Representation readiness

Pass when:
- DINOv3 adapter verified externally;
- patch pipeline deterministic;
- feature extraction completes on a small authorized sample;
- feature metadata/versioning complete;
- at least one baseline representation benchmark runs.

---

# 4. G3 — Source-model readiness

Pass when:
- Attention MIL trains;
- CORAL trains;
- 5-grade outputs valid;
- metrics reproducible;
- lesion-presence auxiliary does not misuse localization labels;
- baseline comparison complete.

This is public-data performance only.

---

# 5. G4 — Local zero-label readiness

Pass when:
- local unlabeled ingest complete;
- source/local drift report exists;
- OOD scores available;
- prototype/reference baseline exists;
- at least one source-free adaptation baseline run;
- pseudo-label gate audited;
- no local clinical performance claim made.

---

# 6. G5 — Pre-label readiness

Pass when:
- MA candidate output exists from a localized-label source or explicitly test-only model;
- region pre-labels for supported lesion classes can be imported;
- unsupported lesions are manual-first;
- prediction contract roundtrip works;
- clinician corrections preserve parent prediction.

---

# 7. G6 — Annotation-platform readiness

Pass when:
- CVAT workflow stable;
- schema/guide frozen v0.1;
- batch import works;
- export works;
- provenance works;
- adjudication state works;
- MA point workflow tested;
- lesion region workflow tested;
- backup/export tested;
- clinician safety language present.

Only now request doctor time.

---

# 8. G7 — First expert batch

Before annotation:
- freeze batch manifest;
- freeze model version used for pre-label;
- freeze sentinel/train designation;
- freeze clinical annotation guide.

During:
- record time and corrections;
- do not alter definitions mid-batch without amendment.

After:
- QA;
- adjudication;
- lock versioned dataset release.

---

# 9. G8 — Local supervised refinement

Compare:
- source model;
- zero-label adapted model;
- local-labeled refinement.

Do not select on sentinel.

---

# 10. G9 — Active learning

First rounds:
- diversity/representativeness.

Later:
- hybrid diversity;
- uncertainty;
- MC Dropout/disagreement.

Report performance vs:
- random sampling;
- uncertainty-only.

---

# 11. Research/business evaluation gate

Technical:
- QWK;
- AUROC;
- AUPRC;
- sensitivity/specificity;
- calibration;
- OOD.

Operational:
- clinician review time;
- correction yield;
- annotation yield/hour;
- abstention;
- potential referral reduction at fixed sensitivity.

Product value requires both technical and operational evidence.

---

# 12. Production gate — not current scope

Future only:
- locked retrospective validation;
- prospective silent evaluation;
- usability;
- risk management;
- change control;
- cybersecurity;
- intended-use freeze;
- regulatory strategy.

No production model should self-update from live clinician labels.

---

# 13. Acceptance criteria for GPT Work starter ZIP

## Global
- [ ] ZIP opens cleanly.
- [ ] no secrets.
- [ ] no PHI.
- [ ] no >50MB unexpected binaries.
- [ ] docs consistent.
- [ ] validation report accurate.

## Track A
- [ ] Python package imports.
- [ ] patch tiler test passes.
- [ ] CORAL target test passes.
- [ ] Attention MIL synthetic forward/backward passes.
- [ ] prediction export validates.
- [ ] AL selector returns a valid synthetic batch.
- [ ] external encoder unavailable case fails clearly.

## Track B
- [ ] bridge package imports.
- [ ] geometry validator passes.
- [ ] synthetic prediction→annotation roundtrip passes.
- [ ] provenance state preserved.
- [ ] CVAT setup documented.
- [ ] annotation guide exists.

## Contracts
- [ ] schemas validate good fixture.
- [ ] schemas reject bad fixture.
- [ ] sentinel leakage check passes/fails as expected.

## Documentation
- [ ] beginner start guide.
- [ ] architecture Mermaid.
- [ ] external dependency list.
- [ ] implementation-status table.

---

# 14. Final delivery report template

```markdown
# FINAL DELIVERY REPORT

Overall: PASS | PARTIAL | FAIL

## Implemented
...

## Scaffolded
...

## External dependencies
...

## Validation commands
...

## Test results
...

## Safety checks
...

## Known limitations
...

## Next recommended action
...
```
