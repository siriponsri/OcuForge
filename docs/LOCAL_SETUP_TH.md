# Local setup

ใช้ Python 3.11–3.12; ทดสอบรอบนี้บน Python 3.12 และ CPU PyTorch 2.5.1 เริ่มด้วย START_HERE_TH.md บน Windows หรือ `bash scripts/install_cpu.sh` ภายใน virtual environment บน Linux

## Docker Desktop / Docker Engine

ต้องมี Docker Engine และ Compose v2 ที่ทำงานได้ก่อน การติดตั้ง Docker อาจต้องสิทธิ์ผู้ดูแลตามนโยบายเครื่อง; Python CPU path ใช้ได้โดยไม่พึ่ง Docker

รันจาก workspace root:

```bash
docker compose -f eyes-detected-models/compose.yaml config --quiet
docker compose -f eyes-detected-labeler/compose.yaml config --quiet
docker compose -f eyes-detected-models/compose.yaml build cpu-test
docker compose -f eyes-detected-models/compose.yaml run --rm cpu-test
docker compose -f eyes-detected-labeler/compose.yaml --profile offline run --rm bridge-offline
```

Build ดึงเฉพาะ software dependencies; runtime CPU demo ปิด network ไม่ mount raw data ทั้งสองบริการเขียน `artifacts/` จึงควรรันตามลำดับ

## ตรวจเพิ่มเติม

```bash
python -m ruff check .
python scripts/validate_configs.py
python scripts/package_check.py
```

ถ้าเห็น `No module named ...` ให้เรียก install ด้วย interpreter ตัวเดียวกับที่รัน test ถ้า DINOv3 unavailable ให้ทำตาม DINO_SETUP.md ห้ามเปลี่ยน encoder เป็น TinyTestEncoder แล้วเรียกผลว่า DINOv3

## เวิร์กสเปซแยก repository ในอนาคต

Shared contracts เป็น Python dependency version 0.1.0 ทั้งสอง track ไม่มี import ข้ามกัน Docker context ใน monorepo ปัจจุบันอยู่ที่ root เมื่อต้องแยก repository ให้ build wheel ของ contracts และส่งผ่าน package registry ภายในพร้อม pin version แทนการ copy implementation
