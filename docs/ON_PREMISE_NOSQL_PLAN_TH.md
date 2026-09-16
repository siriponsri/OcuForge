# แผนฐานข้อมูลภาพและ Label ภายในโรงพยาบาล

สถานะ: แบบออกแบบและ adapter สำหรับทดสอบระบบ ยังไม่ผ่านการติดตั้งรับรองบนเครือข่ายโรงพยาบาล
วันที่: 2026-09-09 · รุ่นสถาปัตยกรรม: local-storage.v1

## ข้อสรุปที่ใช้พัฒนา

ใช้ MongoDB Community เก็บเอกสาร metadata, สถานะงาน, label และประวัติการแก้ไข ส่วนภาพต้นฉบับเก็บเป็นไฟล์ immutable บนดิสก์/NAS ภายในโรงพยาบาล เชื่อมกันด้วย `image_id`, `relative_uri` และ SHA-256 ภาพและ label รวมถึง feature, prediction, checkpoint ที่สร้างจากข้อมูลโรงพยาบาล **ห้ามส่งออก cloud** แม้เปลี่ยนชื่อผู้ป่วยแล้วก็ตาม GitHub เก็บโค้ด/config/safe manifest/model metadata/hash/report ที่เหมาะสมและ synthetic fixture เท่านั้น

การไม่เก็บบน cloud หมายถึงทั้งระบบใช้งานจริง การสำรองข้อมูล log และ telemetry ไม่ใช่เพียงฐานข้อมูลหลัก: ไม่ใช้ MongoDB Atlas, Vercel Blob, S3 หรือ hosted analytics สำหรับงานคลินิก แยก Vast.ai/RunPod เป็นสภาพแวดล้อม public/synthetic เท่านั้น ไม่มี hospital volume หรือ hospital credential ในเครื่องเหล่านั้น

## ส่วนประกอบและขอบเขต

| ส่วน | ที่เก็บ/การเชื่อมต่อ | หน้าที่ |
|---|---|---|
| Browser แพทย์ | เครื่องในโรงพยาบาล → HTTPS ภายใน | เปิด CVAT และ portal จัดการงาน |
| CVAT | server ภายใน + PostgreSQL/Redis/volume ของ CVAT | editor ภาพ, geometry และงาน annotation |
| Labeler bridge | server ภายใน | mapping ภาพ, schema validation, provenance, review/export |
| MongoDB | server ภายใน; ไม่ publish port 27017 | metadata, workflow, immutable annotation revisions |
| Image store | local SSD หรือ NAS ที่ mount บน server | ภาพแบบ content-addressed; ไม่เก็บ binary ใน document |
| Export store | local volume แยก | versioned JSONL, geometry/export และ snapshot สำหรับฝึกในโรงพยาบาล |
| Patient linkage | ระบบโรงพยาบาลแยกต่างหาก | mapping HN/ชื่อจริง ↔ pseudonym; ไม่อยู่ใน labeler |
| Backup | NAS สำรองและสื่อเข้ารหัส offline | snapshot ภาพ/ฐานข้อมูล/CVAT/config ที่กู้คืนร่วมกัน |

MongoDB **ไม่แทน PostgreSQL ของ CVAT**; adapter ทำงานร่วมกับ API ของ CVAT และเก็บข้อมูลตามสัญญากลางอีกชุดหนึ่ง จึงไม่แก้ฐานข้อมูล CVAT โดยตรง และไม่ถือว่า MongoDB dump อย่างเดียวกู้ระบบทั้งหมดได้

แผนภาพ trust boundary และ public/local handoff ฉบับปัจจุบันอยู่ที่
[`ocuforge-deployment-boundary.svg`](diagrams/ocuforge-deployment-boundary.svg) ส่วนรายละเอียด storage และ
backup ในเอกสารนี้ยังเป็น supporting design ที่ต้องทดสอบใน local/on-premise gate

## โครงสร้างเอกสาร

รุ่นแรกใช้ `workflow_documents` และ `annotation_revisions` เพื่อลดความซับซ้อน มี field `kind` แยก `image`, `batch`, `protocol` และ `release` เมื่อจำนวนงานโตขึ้นจึง migration เป็น collections แยก โดยรักษา IDs เดิม

| เอกสาร | field สำคัญ | กติกา |
|---|---|---|
| image | image_id, file_sha256, relative_uri, pseudonym, laterality, dimensions, site, camera, split, source_type, binary_assessment | `LOCAL_PRIVATE`, cloud_eligible=false; ห้ามใช้ชื่อ/HN เป็นชื่อไฟล์ |
| batch | batch_id, task_id, frames, protocol ref, version, status, events | compare-and-swap ป้องกันแพทย์/worker เขียนทับงานกัน |
| annotation_revision | annotation_id, image_id, revision_hash, body | append-only ผ่าน application; ทุก revision มี actor เวลา และ parent prediction |
| protocol | protocol_id, version, config_sha256, approved_by, effective_date | ICO 2017 เป็นค่าเริ่มต้น; เปลี่ยนเป็นรุ่นใหม่ ไม่แก้ label เก่าย้อนหลัง |
| release | release_id, image IDs, annotation revision hashes, split manifest, protocol hashes | immutable dataset snapshot; เฉพาะ adjudicated/locked ที่มีสิทธิ์ใช้ |

ตัวอย่าง metadata ที่เป็นข้อมูลสมมติ:

```json
{"_id":"image:SYN_IMG_001","kind":"image","version":0,"body":{"image_id":"SYN_IMG_001","storage":"local-filesystem","relative_uri":"ab/<sha256>.png","cloud_eligible":false,"source_type":"LOCAL_PRIVATE","binary_assessment":{"value":"DR","source":"DOCTOR_EXPERIENCE"},"dr_grade":null,"lesion_annotations_available":false}}
```

ตัวอย่างนี้เป็นภาพแนวคิด ไม่ใช่ JSONL สำหรับ import โดยตรง; schema ใช้งานจริงอยู่ใน `eyes-detected-contracts/schemas/`

ข้อมูล DR/no-DR เดิมเป็น **image-level doctor experience** เท่านั้น: DR ไม่แปลเป็น grade 1–4 และ no-DR ไม่สร้าง label ordinal ที่ adjudicate แล้วโดยอัตโนมัติ ไม่มี lesion mask/point/box จนแพทย์ทำ annotation จริง การไม่พบ annotation ไม่เท่ากับยืนยันว่าไม่พบรอยโรค

DR grade 0–4 ต้องผูก `ProtocolRef` จาก ICO 2017 version/hash ในทุก label; ungradable เป็นสถานะคุณภาพแยกจาก grade, DME เป็นคนละแกน และไม่สรุป OCT-confirmed DME จากภาพ fundus เดี่ยว การปรับ guideline ในอนาคตใช้ protocol ใหม่และงาน re-review ที่ตามรอยได้

## การรับภาพและ lifecycle

1. เจ้าหน้าที่ตรวจการอนุญาตและ de-identification ที่เครื่องภายใน รวมข้อความฝังใน pixel และ EXIF; pseudonymization อย่างเดียวไม่รับประกันว่าปลอด PHI
2. ตรวจ SHA-256, decode ภาพ, RGB/ขนาดและ manifest ก่อน copy เข้า staging ภายใน เก็บต้นฉบับ immutable ไม่เขียนทับ
3. Atomic rename จาก staging ไป `objects/<sha[:2]>/<sha>.<ext>` แล้ว insert image metadata หาก insert ล้มเหลวถือเป็น orphan ที่ตรวจภายหลัง ห้ามลบอัตโนมัติจากการไม่มีเอกสารเพียงครั้งเดียว
4. สร้าง batch และ task ผ่าน bridge; CVAT อ่าน share แบบ read-only ตรวจชื่อ frame/ขนาดก่อน import suggestions
5. แพทย์ confirm/correct/reject/add พร้อม journal; AI_SUGGESTED ไม่ใช่ ground truth
6. ผู้เชี่ยวชาญ adjudicate แล้ว lock; เก็บ revision ใหม่และอ้างถึง revision ที่ release เลือกใช้ ห้ามแก้เอกสาร locked เดิม
7. สร้าง local release พร้อม manifest/hash และ patient-group split; TRAIN/VAL/TEST/SENTINEL ต้องไม่รั่วข้ามผู้ป่วย

## Index และ concurrency

มี `_id` unique, workflow `(kind, updated_at)` และ revision `(annotation_id, revision_hash)` unique ใน adapter รุ่นแรก เพิ่ม `(image_id, annotation_id)` สำหรับค้น revision ตามภาพ งานค้นตาม site/split ควรเพิ่มหลังวัด query จริง

MongoDB มี atomicity ระดับหนึ่ง document จึงใช้ `version` ในเงื่อนไข update; stale write ต้อง conflict และ reload ไม่เขียนทับอัตโนมัติ งานข้าม MongoDB + CVAT + filesystem ไม่เป็น transaction เดียว: เขียน intent ก่อนเรียก CVAT และ reconcile ด้วย task ID เมื่อ timeout ห้าม retry create โดยไม่ตรวจงานเดิม [MongoDB atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/)

Document จำกัดก่อนถึงเพดาน 16 MiB ของ BSON; ภาพ/mask ขนาดใหญ่ใช้ไฟล์ภายนอก อาจเพิ่ม GridFS เมื่อมีเหตุผลด้าน operation แต่ GridFS ไม่รองรับ multi-document transactions จึงไม่ทำให้ภาพกับ metadata กลายเป็น atomic โดยอัตโนมัติ [MongoDB GridFS](https://www.mongodb.com/docs/manual/core/gridfs/)

## ความปลอดภัยที่ต้องติดตั้งจริง

- Reverse proxy HTTPS ด้วย certificate ภายใน; firewall allowlist subnet โรงพยาบาล; service database ไม่มี public port
- บัญชีแยก admin/annotator/expert; token file อยู่ใน secret mount ภายใน ไม่ commit; เปลี่ยนค่าเริ่มต้นและกำหนดรอบ rotate
- MongoDB เปิด authentication; account ของ application มีเฉพาะฐานข้อมูล OcuForge ไม่ใช้ root ในแอป การทำ append-only ใน adapter ไม่ใช่หลักประกันป้องกันผู้ดูแล DB แก้ข้อมูล ต้องกำหนด custom role/immutable backup ตามความเข้มงวดที่โรงพยาบาลต้องการ
- ใช้ full-disk encryption เช่น LUKS/BitLocker หรือ NAS encryption รวมสื่อสำรอง; เก็บ recovery key แยกเครื่อง ห้ามอ้างว่า MongoDB Community มี native encrypted storage engine แบบ Enterprise [MongoDB encryption at rest](https://www.mongodb.com/docs/manual/core/security-encryption-at-rest/)
- ปิด internet egress ของ clinical service หลังติดตั้ง dependencies และ disable analytics/crash upload ไม่ใส่ภาพ/path/PHI ใน log
- Browser shared computer ต้อง logout, lock screen, ไม่ sync download folder ขึ้น cloud; audit log ใช้รหัสผู้ใช้ ไม่ใส่ชื่อผู้ป่วย
- Retention/การลบต้องผ่านนโยบายโรงพยาบาล รวมสำเนา backup และ CVAT copy ไม่กำหนดจำนวนปีขึ้นเอง

## Capacity และ backup

ประมาณจากภาพจริงแบบสุ่มภายในเท่านั้น ไม่ดาวน์โหลดตัวอย่างไปบริการภายนอก สูตรพื้นที่ = ภาพต้นฉบับ + CVAT copies/cache + exports/revisions + features/checkpoints ที่เก็บภายใน + headroom 30% แล้วคิดสำเนา backup แยก

ตัวอย่างสมมติ 100,000 ภาพ × 5 MB ≈ 500 GB เฉพาะต้นฉบับ; ถ้า CVAT copy อีกชุดรวม ~1 TB ก่อน feature/cache/backup จึงไม่ใช้ตัวเลขนี้เป็นสเปกจัดซื้อโดยไม่มีการวัด

เป้าหมายเสนอเพื่อให้โรงพยาบาลรับรอง: RPO ≤24 ชั่วโมง และ RTO ≤8 ชั่วโมง ไม่ใช่ SLA ที่ทดสอบแล้ว

1. แจ้ง maintenance แล้วหยุดการเขียนจาก portal/bridge และ CVAT workers รอ queue จบ
2. backup MongoDB, PostgreSQL และ CVAT volumes พร้อม image/export store และ config/secret ที่เข้ารหัส ใช้ snapshot ID เดียวกัน ระบุ software versions และ hashes
3. สำรองรายวันไปเครื่อง/NAS คนละ failure domain และสำเนา encrypted offline ที่เก็บอีกพื้นที่ภายในองค์กร ไม่ใช้ cloud sync
4. ตรวจความครบถ้วนกับ manifest และ hash; ทุกเดือนทดลอง restore ในเครือข่ายแยก ตรวจภาพเปิดได้ mapping CVAT ถูก ประวัติ/release ครบ และวัดเวลากู้คืน
5. `eyes-local backup/restore` สำรองเฉพาะ MongoDB application documents สำหรับพัฒนา/ตรวจสอบ **ไม่ใช่ full disaster recovery**; ต้องหยุด writer และ restore ลง DB ว่าง ถ้าขัดข้องกลางทางให้ทิ้ง DB เป้าหมายแล้วเริ่มใหม่ ไม่ merge

## ระยะติดตั้งและเกณฑ์รับมอบ

- ระยะ 1: เครื่องทดลองภายใน synthetic only ทดสอบ auth, ingest/hash, stale-write conflict, review/provenance, backup/restore และการปิด egress
- ระยะ 2: pilot ข้อมูลที่โรงพยาบาลอนุมัติบนเครื่องจริง ตรวจ de-identification, permissions, CVAT version/API และคู่มือแพทย์
- ระยะ 3: expert sign-off protocol, restore drill และ access review ก่อนใช้งานจริง; ระบบนี้ยังเป็น research workflow ไม่ใช่เครื่องมือวินิจฉัยที่ผ่าน clinical validation

สิ่งที่ต้องตัดสินกับ IT ในขั้นติดตั้ง: server/NAS ที่มีอยู่, จำนวนแพทย์พร้อมกัน, ขนาด/อัตรารับภาพ, subnet/DNS/TLS, ผู้ดูแล backup และ recovery key, retention และ RPO/RTO ที่รับรอง ไม่จำเป็นต้องรอคำตอบเหล่านี้เพื่อพัฒนา adapter และ synthetic tests
