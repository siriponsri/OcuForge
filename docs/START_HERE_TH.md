# OcuForge V3 - จุดเริ่มต้น

OcuForge เป็นโครงงานวิจัยและระบบช่วย review ภาพจอตา ไม่ใช่ผลิตภัณฑ์วินิจฉัยโรค แผนที่ใช้งานอยู่มีเพียง
[`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md) โดย R0 ผ่านแล้ว แต่ R1-P0 และ R1 ยังไม่รัน

## สถานะปัจจุบัน

```text
R0_V3 = PASS
CAMPAIGN_START_READY = YES
R1_P0_EXECUTION_READY = YES
R1_P0_ACQUISITION_PREFLIGHT = BLOCKED
R1_TRAINING_READY = NO
R1 C0/C1/C2 = READY_NOT_EXECUTED
CURRENT_R1_CHAMPION = NONE
```

R1-P0 acquisition/runtime checks completed but remain `BLOCKED` by two exact MMRDR duplicate-content groups crossing the
released `tr`/train and `ts`/test split. Do not train R1, reshuffle the released split, or silently exclude rows until
the owner resolves the protocol. The authorized P0 runtime used public data only; IDRiD remains an independent R2/R3
lane and does not resolve this R1 blocker.

## ลำดับการอ่าน

1. [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md) - ทิศทาง V3 และ execution gate
2. [`R0_DATASET_SUPERVISION_FREEZE.md`](R0_DATASET_SUPERVISION_FREEZE.md) - แหล่งข้อมูล supervision และ leakage
3. [`R1_GLOBAL_MODEL_SELECTION.md`](R1_GLOBAL_MODEL_SELECTION.md) - C0/C1/C2 และ CE-first benchmark
4. [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) - สิ่งที่พร้อมและ gate ที่ยังเปิด
5. [`CTR_MODULE_CONTRACT.md`](CTR_MODULE_CONTRACT.md) - boundary ระหว่าง contracts, models และ labeler

## ตรวจแบบ offline

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\validate_configs.py
.\.venv\Scripts\python.exe scripts\package_check.py
```

Synthetic smoke ใช้ตรวจ engineering path เท่านั้น ไม่ใช่ผลวิจัยหรือผลทางคลินิก ก่อนรัน R1 ต้องให้ R1-P0 Global ตรวจ
MMRDR archive/hash, schema/split, preprocessing, C0/C1/C2 asset loading และ runtime ให้ครบ โดยยอมรับ
`PASS_WITH_WARNINGS` ได้เมื่อไม่มี blocking finding และต้องส่งต่อ warnings ไปยัง R1 artifacts

## กฎข้อมูล

ห้าม commit ภาพโรงพยาบาล, PHI, credentials, weights หรือ derived private artifacts ภาพและข้อมูล private ต้องอยู่
local/on-premise เท่านั้น Public GPU ใช้กับ public หรือ synthetic data ที่ตรวจสอบแล้วเท่านั้น
