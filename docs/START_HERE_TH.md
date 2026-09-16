# เริ่มใช้งาน Eye Detected v0.1

แพ็กเกจนี้เป็นโครงระบบวิจัยที่รันด้วยข้อมูลสังเคราะห์ได้ ไม่ต้องใช้ GPU หรือให้แพทย์ทำ label ก่อน

## 5 คำสั่งแรกบน Windows

แตก ZIP แล้วเปิด PowerShell ในโฟลเดอร์ `eyes-detected-dual-track-starter-v0.1` ติดตั้ง Python 3.12 ให้เรียก `python` ได้ก่อน

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -e ./eyes-detected-contracts -e ./eyes-detected-models -e ./eyes-detected-labeler -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts/synthetic_roundtrip.py
```

การเรียก Python ใน `.venv` โดยตรงไม่ต้องเปลี่ยน PowerShell execution policy การติดตั้งครั้งแรกต้องมีอินเทอร์เน็ต หลังติดตั้งแล้ว test/demo ใช้งาน offline ได้

## ผลที่ควรเห็น

- pytest แสดงว่าผ่านทุก test; จำนวนจริงอยู่ใน FINAL_DELIVERY_REPORT
- demo แสดง `weights_updated: true`, `scientific_result_eligible: false`
- `artifacts/smoke/images.jsonl` มี 10 synthetic images
- `artifacts/smoke/predictions.jsonl` เป็นผลโมเดลทดลองพร้อม synthetic candidate point ที่ระบุชัด
- `artifacts/roundtrip/annotations.jsonl` เก็บประวัติ PROPOSE → CORRECT → ADJUDICATE → LOCK
- `artifacts/smoke/annotation_batch.json` เป็น 3 cases ที่เลือกได้

คะแนน loss ใช้ตรวจกลไก training เท่านั้น ไม่ใช่ความแม่นยำตรวจโรค

## อ่านอะไรต่อ

1. LOCAL_SETUP_TH.md เพื่อใช้ Docker
2. GRADING_PROTOCOL_TH.md เพื่อเข้าใจเกณฑ์ ICO และข้อมูล DR/no-DR เดิม
3. ../eyes-detected-labeler/docs/CVAT_SETUP_TH.md เพื่อทดลอง CVAT local
4. IMPLEMENTATION_STATUS.md เพื่อแยกสิ่งที่ทำแล้วกับงานถัดไป

แผน POC ปัจจุบันอยู่ที่ `docs/POC_MASTER_PLAN_V2.md` ของ workspace; ก่อนรันงานวิจัยให้อ่าน
`R0_DATASET_SUPERVISION_FREEZE.md` และ `R1_GLOBAL_MODEL_SELECTION.md` ด้วย R0 V2 ยังเป็น READY_TO_EXECUTE
ไม่ใช่ PASS และ R1 G0-G5 ยังไม่ได้รัน

อย่าใส่ภาพโรงพยาบาลใน GitHub, starter folder, Space หรือ cloud GPU ผู้ใช้ต้องกำหนด local secure data root ภายใต้การดูแลของหน่วยงานในขั้นถัดไป
