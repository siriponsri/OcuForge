# ตั้งค่า CVAT local

สถานะ live integration: REQUIRES_EXTERNAL_SERVICE. ใช้ official CVAT deployment ไม่ fork core และไม่สร้าง CVAT server ปลอมใน compose ของ starter

## 1. เริ่ม upstream CVAT

ตรวจ [คู่มือติดตั้ง CVAT](https://docs.cvat.ai/docs/administration/community/basics/installation/) และเลือก release ที่ทีมจะตรึง version. ตัวอย่างคำสั่งหลังมี Git และ Docker:

```bash
git clone https://github.com/cvat-ai/cvat.git cvat-local
cd cvat-local
# เลือก release tag/commit ที่ตรวจแล้วก่อน deploy; บันทึก commit
 git rev-parse HEAD
docker compose config --quiet
docker compose up -d
docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'
```

Topology และ service names ให้ยึด release นั้นของ upstream. ยังไม่ได้ทดสอบ CVAT server ในสภาพแวดล้อมส่งมอบนี้ เปิด browser ที่ localhost:8080 ตาม upstream setup. การเข้าใช้ผ่าน LAN ต้องจัด TLS/accounts โดยทีม local ก่อน

## 2. ตรวจ bridge

กลับมายัง OcuForge root ตั้ง CVAT_URL=http://localhost:8080 และ CVAT_TOKEN ใน environment ภายในเครื่อง ห้ามใส่ค่าลง Git. สำหรับ Docker bridge ใช้ host.docker.internal

```bash
python -m labeler_bridge.cli health
python -m labeler_bridge.cli bootstrap-project eyes-detected-labeler/configs/projects/ED_LESION_POINT_MA_V1.json
```

สร้าง project ซ้ำจะสร้างรายการใหม่ จด project ID ที่ได้ แยก DR grade, MA point, lesion region และ adjudication ตามไฟล์ config ที่ให้มา

## 3. Synthetic task ก่อนข้อมูลจริง

รัน synthetic_roundtrip.py แล้วสร้าง task ใน CVAT UI อัปโหลด **เฉพาะ** `artifacts/smoke/images/SYNTH_000.png` ลง task เพื่อให้ frame=0 ตรวจ dimensions=80×48 และระบุ image mapping อย่างชัดเจน การอัปโหลดนี้เป็นขั้นตอนที่ผู้ปฏิบัติเลือกเอง starter ไม่มี image upload API

อ่าน label IDs และ attribute spec IDs จาก API ของ project/task แล้วส่ง mapping จริงให้ `import_prediction`. ID 1 ใน demo เป็น test mapping ห้ามสมมติว่า server จะให้ ID นี้

```python
from eyes_contracts.validators import read_records
from labeler_bridge.import_predictions.bridge import import_prediction
image = read_records('artifacts/smoke/images.jsonl')[0]
prediction = read_records('artifacts/smoke/predictions.jsonl')[0]
# label_ids และ attribute_ids ต้องได้จาก CVAT server จริง
payload, sidecar = import_prediction(prediction, image, frame=0,
    label_ids=label_ids, attribute_ids=attribute_ids)
```

บันทึก payload/sidecar พร้อม task ID และ image mapping ก่อน import จากนั้นใช้ `python -m labeler_bridge.cli import-payload TASK_ID payload.json` ซึ่งใช้ PATCH action=create ไม่ overwrite annotation เดิม ห้ามเรียกซ้ำโดยไม่ตรวจ duplicate เพราะ upstream อาจสร้าง shapes เพิ่ม

## 4. Export และ review

ใช้ `fetch-annotations TASK_ID --out cvat_export.json` เพื่อเก็บ payload. ส่งให้ export_annotations พร้อม sidecar, frame→image, label/attribute mappings และ decision journal. คู่มือ API อยู่ BRIDGE_USAGE.md. Label/attribute mapping ไม่รู้จักหรือ provenance หายต้องแก้ก่อน ไม่ทิ้งข้อมูลเงียบ ๆ

ใน DR project ให้แพทย์ตั้ง dr_grade attribute และส่ง frozen ICO ProtocolRef เข้า exporter. รูปแบบ geometry='image_presence'. Grade revision ต้องสร้าง amendment ไม่แก้ annotation เก่าทับ

SAM2/SAM3 ขึ้นกับ upstream deployment และ model access; ไม่ได้ติดตั้งหรือรับรองใน starter. FiftyOne เป็น optional เท่านั้น
