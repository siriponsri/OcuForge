# OcuForge V3 - จุดเริ่มต้น

OcuForge เป็นโครงงานวิจัยและระบบช่วย review ภาพจอตา ไม่ใช่ผลิตภัณฑ์วินิจฉัยโรค แผนที่ใช้งานอยู่มีเพียง
[`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md) โดย R0 ผ่านแล้ว แต่ R1-P0 และ R1 ยังไม่รัน

## สถานะปัจจุบัน

```text
R0_V3 = PASS
R1_P0_ACQUISITION_PREFLIGHT = READY_NOT_EXECUTED
R1 C0/C1/C2 = READY_NOT_EXECUTED
CURRENT_R1_CHAMPION = NONE
```

การตรวจเอกสารรอบนี้ไม่ download dataset, ไม่ train model และไม่ provision cloud GPU; ขั้นถัดไปคือ R1-P0

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

Synthetic smoke ใช้ตรวจ engineering path เท่านั้น ไม่ใช่ผลวิจัยหรือผลทางคลินิก ก่อนรัน R1 ต้องให้ R1-P0 ตรวจ
archive/hash, schema/split, preprocessing, asset loading และ runtime ให้ครบ

## กฎข้อมูล

ห้าม commit ภาพโรงพยาบาล, PHI, credentials, weights หรือ derived private artifacts ภาพและข้อมูล private ต้องอยู่
local/on-premise เท่านั้น Public GPU ใช้กับ public หรือ synthetic data ที่ตรวจสอบแล้วเท่านั้น
