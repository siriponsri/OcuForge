# Local labeler workflow

CVAT เป็น UI ที่แพทย์ใช้ annotation ระบบนี้เพิ่ม local operator CLI สำหรับเชื่อมสถานะงานและประวัติใน MongoDB ไม่มี editor ใหม่หรือเว็บรับภาพบน cloud ใช้ Python module ได้แม้ยังไม่ได้ติดตั้ง console entrypoint: `python -m labeler_bridge.local_cli --help`

เตรียม CVAT และ Mongo ตาม deploy/onprem/README.md ก่อน คำสั่งต่อไปนี้เป็นตัวอย่าง path ภายในเครื่อง ตั้ง MONGO_URI/CVAT_URL/CVAT_TOKEN ผ่าน environment/secret ภายใน ไม่ใส่ token ใน command line

```bash
eyes-local ingest --images /local/images.jsonl --source-root /local/incoming --object-root /local/objects --out /local/images.objects.jsonl
eyes-labeler bootstrap-project eyes-detected-labeler/configs/projects/ED_LESION_POINT_MA_V1.json
```

เลือกไฟล์ project spec ที่มีจริงจาก `eyes-detected-labeler/configs/projects/` ให้ตรงงาน ไม่ใช้ project ID สมมติในการเรียกจริง จากนั้นบันทึก ID ที่ CVAT คืนกลับ และเตรียม batch JSON ตาม contracts

```bash
eyes-local --exports /local/exports register --batch /local/batch.json --images /local/images.objects.jsonl --protocol eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json --actor USER_01
eyes-local create-task BATCH_001 --project-id 1 --actor USER_01
eyes-local attach-share BATCH_001 --share-root /local/objects --actor USER_01
eyes-local sync BATCH_001 --actor USER_01
eyes-local import-predictions BATCH_001 --predictions /local/predictions.jsonl --actor USER_01
```

`project-id 1` เป็นตัวอย่างต้องแทนด้วยค่าจริง Share root ใน bridge และ CVAT ต้อง mount ไฟล์เดียวกัน ภาพตรวจ hash ก่อน attach; sync ตรวจ frame name/ขนาด/label IDs ก่อน import สำหรับ classification-only predictions ที่ไม่มี localized objects ให้แพทย์ทำ manual grading/annotation ไม่สร้าง geometry จาก attention

แพทย์ทำงานใน CVAT จากนั้นบันทึก decision journal ตามคู่มือ BRIDGE_USAGE.md: annotation ID → CONFIRM/CORRECT/REJECT/ESCALATE และ new:<CVAT shape ID> → ADD; export จะตรวจว่าการเปลี่ยน geometry ตรงกับ action จริง คำสั่ง operator ไม่แทนการยืนยันโดยแพทย์

```bash
eyes-local --exports /local/exports export BATCH_001 --decisions /local/decisions.json --active-seconds 120 --actor DOCTOR_01
eyes-local --exports /local/exports finalize BATCH_001 --expert-attestation --actor EXPERT_01
eyes-local list-batches
```

Finalization คือคำสั่งยืนยันผลตรวจของ expert จริง รวมการ resolve uncertain ก่อน lock อย่ารันเพื่อทำให้สถานะผ่านโดยไม่มี review คลินิก โปรแกรมไม่ตรวจคุณวุฒิผู้ใช้; โรงพยาบาลต้องกำหนด operator permission และ CVAT role

Timeout ตอนสร้าง task ทิ้งสถานะ CREATING_TASK; ตรวจงาน CVAT ก่อน `attach-task` เพื่อ reconcile ห้าม retry สร้างซ้ำอัตโนมัติ Import retry ไม่เพิ่ม suggestion ID ซ้ำและปฏิเสธ prediction contents ที่เปลี่ยนไป ต้องสร้าง batch ใหม่เมื่อแก้ model output งาน finalized เป็น immutable snapshot หากต้องแก้ให้เปิดงาน amendment ใหม่ที่อ้างงานเดิม; ยังไม่มี automatic amendment UI

Backup CLI เป็น application document export เท่านั้น ดูแผน full backup ใน ON_PREMISE_NOSQL_PLAN_TH.md ต้องหยุด writers ก่อน backup และ restore ลง DB ว่าง
