# เริ่มใช้ Shared contracts

เปิด terminal ที่โฟลเดอร์ root ของ ZIP ไม่ใช่โฟลเดอร์ src และติดตั้งทั้งสาม package ตาม [START_HERE_TH.md](../docs/START_HERE_TH.md)

```bash
python -m eyes_contracts.cli validate eyes-detected-contracts/examples/image_manifest.json
```

สำหรับ Track B ให้รัน Track A smoke ก่อนเพื่อสร้างไฟล์ input. ทุกตัวอย่างเป็นข้อมูลสังเคราะห์ ไม่ใช่ผลตรวจโรค คำสั่งนี้ไม่เชื่อมต่อ CVAT จริง

ตรวจระบบทั้งหมดด้วย `python -m pytest` และ `python scripts/synthetic_roundtrip.py` จาก root

ดูคำสั่ง Docker และข้อจำกัดใน [LOCAL_SETUP_TH.md](../docs/LOCAL_SETUP_TH.md)
