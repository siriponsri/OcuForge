# ชุดคำสั่ง model pipeline และ public GPU

คำสั่งทั้งหมดใช้ path ที่ผู้รันกำหนดเอง ไม่มี dataset/model downloader, uploader หรือ provision GPU อัตโนมัติ
Hospital images/labels/features/checkpoints อยู่ on-premises เท่านั้น

สำหรับ R1 public-data GPU ให้ตั้ง storage roots ก่อน:

```bash
export OCUFORGE_DATA_ROOT=/workspace/data
export OCUFORGE_MODEL_ROOT=/workspace/models
export OCUFORGE_CACHE_ROOT=/workspace/cache
export OCUFORGE_ARTIFACT_ROOT=/workspace/artifacts
```

RunPod Network Volume เป็นตัวเลือก persistent storage ที่แนะนำ แต่ไม่ใช่ dependency; root เดียวกันใช้กับ
filesystem อื่นได้ด้วย layout `data/mmrdr`, `data/idrid`, `data/manifests`, `models/dinov3`,
`cache/features`, `artifacts/experiments`. Git เก็บเฉพาะ code, safe manifests, hashes และ metadata.

ติดตั้ง packages ตาม README แล้วใช้ `eyes-pipeline --help` รองรับ audit, extract, train, evaluate, predict; คำสั่ง smoke/active-learning เดิมยังอยู่ใน `eyes-models --help`

```bash
eyes-pipeline audit --manifest /data/images.jsonl --dataset /data/dataset.yaml --data-root /data --out /runs/audit.json
eyes-pipeline extract --manifest /data/images.jsonl --dataset /data/dataset.yaml --data-root /data --config /runs/extract-reviewed.json --out /runs/features
eyes-pipeline train --manifest /data/images.jsonl --dataset /data/dataset.yaml --targets /data/targets.jsonl --features /runs/features --config /runs/train.json --protocol eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json --out /runs/mil
eyes-pipeline evaluate --manifest /data/images.jsonl --dataset /data/dataset.yaml --targets /data/targets.jsonl --features /runs/features --checkpoint /runs/mil/best.pt --split TEST --out /runs/evaluation
eyes-pipeline predict --manifest /data/images.jsonl --dataset /data/dataset.yaml --features /runs/features --checkpoint /runs/mil/best.pt --split ALL --out /runs/predictions
```

`extract-dino.json` ต้องแก้ local checkout/path, hash, license_reviewed หลังตรวจสิทธิ์จริง จึงรันได้ ไม่มี tiny fallback; `extract-tiny.json` รับ synthetic เท่านั้น ตั้ง device=cpu สำหรับ CPU synthetic tests โดยชัดเจน

Target JSONL เป็น schema ของ `pipeline.data.Target`: image_id, source, dr_grade **หรือ** binary_dr, optional lesions ลำดับ `[microaneurysm, intraretinal_hemorrhage, hard_exudate, cotton_wool_spot, vb_irma, nv, laser_scar]` (7 ช่อง; null หมายถึงไม่มี supervision), gradable 0/1/null ต้องกำหนด label semantics ของแหล่งข้อมูลก่อนใช้ ความหมาย 7 ช่องเป็นสัญญาของ pipeline นี้ ห้ามส่งออกเป็น lesion localization

ตัวอย่าง synthetic: `{"image_id":"SYN_01","source":"SYNTHETIC","dr_grade":2}`

Binary hospital experience ใช้ `source=DOCTOR_EXPERIENCE`, binary_dr=0/1, ไม่ใส่ ordinal/lesions; รัน on-premises ด้วย train-binary config เท่านั้น Feature cache ตรวจ image SHA, encoder/weights/preprocess identity ก่อน train/infer checkpoint โหลดแบบ weights_only และควรรับเฉพาะ checkpoint ที่เชื่อถือได้

Train ใช้ TRAIN และเลือก best ด้วย VAL; ไม่ใช้ TEST/SENTINEL เลือกโมเดล Resume ด้วย `--resume /runs/mil/last.pt` ต้อง config/data/protocol เหมือนเดิม เปลี่ยน experiment ให้ใช้ directory ใหม่ Evaluation ต้องเลือก held-out split ชัดเจน; ค่าจาก synthetic ไม่ใช่ผลทางคลินิก ไม่มี calibration/OOD threshold ที่รับรองจาก training pipeline นี้

MIL attention เป็น model evidence; predictions.jsonl ไม่สร้างจุด/กล่อง/mask จาก attention Binary probability อยู่ scores.json แยก เนื่องจาก shared prediction.v0.1 ไม่มี binary field และไม่แปลงเป็น grade 0–4 ส่วน auxiliary heads ที่ยังไม่ยืนยัน supervision ไม่ถูกเผยแพร่เป็น trained probabilities

## Vast / RunPod adapter

1. ตรวจ dataset/model เป็น public จริง พร้อม license ที่อนุญาตงานและ cloud_eligible ทั้ง dataset/image manifests; config ที่เขียนว่า reviewed เป็นการบันทึกผลตรวจ ไม่ใช่ตัวตรวจ license อัตโนมัติ
2. เตรียม GPU instance เองตามงบและสิทธิ์ที่อนุมัติ ไม่มีสคริปต์เช่าเครื่องหรือส่งภาพโรงพยาบาล
3. ถ้าเป็น Docker host ที่มี NVIDIA Container Toolkit: ตั้ง `OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`,
   `OCUFORGE_CACHE_ROOT`, `OCUFORGE_ARTIFACT_ROOT` ให้ชี้เฉพาะ public/synthetic แล้ว
   `docker compose -f deploy/vast/compose.yaml build` และ
   `docker compose -f deploy/vast/compose.yaml run --rm models <subcommand และ args>`
4. Vast instance หลายรูปแบบเป็น container อยู่แล้ว ไม่ถือว่ามี Docker daemon หรือ nested Docker ให้ติดตั้ง packages ใน container ที่เตรียมแล้วและใช้ `bash deploy/vast/run-public.sh <subcommand และ args>` แทน ทั้งสองทางตั้ง PUBLIC_CLOUD ทำให้ data gate ทำงานแม้ไม่ระบุ --cloud
5. ไม่มี network ระหว่าง Compose training; model checkout ต้องไม่ดาวน์โหลดตอน torch.hub local load และต้องตรวจ dependency ที่ official model ต้องการก่อน build image ใช้ nvidia-smi/CUDA probe บน target host; หากไม่มี GPU จะ fail ไม่ fallback
6. บันทึก image digest, commit SHA, license decision และ run config ก่อนใช้จริง Docker build/GPU/DINO/live service ยังเป็น external acceptance gate ของรุ่นนี้

RunPod ใช้ Dockerfile/launcher เดียวกันบน container ที่ผู้ใช้จัดเตรียม ไม่สมมติว่ามี connected plugin และ
ไม่บังคับให้ใช้ RunPod. สำหรับ R1 B1 ใช้คำสั่งใน
`eyes-detected-models/configs/research/r1-global-b1.json`; ต้อง mount manifest/data/model roots เอง,
ตรวจ hash/สิทธิ์ก่อนรัน และยังไม่ provision หรือ download dataset ขนาดใหญ่ใน gate ปัจจุบัน. Vercel ใช้ได้เฉพาะ
เอกสารหรือ synthetic demo; clinical UI/API/database ไม่ deploy ที่นั่น

[Vast SSH connection](https://docs.vast.ai/guides/instances/connect/ssh)
