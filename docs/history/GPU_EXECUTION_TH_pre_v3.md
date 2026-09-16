# GPU execution ภายหลัง

## Current model-first gate

The current gate is **R0_V2=READY_TO_EXECUTE**. Supervision semantics, spatial taxonomy, negative policy and
identity split rules must be re-audited before R0 can pass. R1 is **READY_NOT_EXECUTED** and uses the controlled
G0-G5 ladder; DINOv3 plus Attention MIL is a leading candidate, not a predetermined champion, and CE versus
CORAL is an ablation for genuine ordinal labels only. MMRDR UWF is a candidate global source; IDRiD is a
candidate spatial ROI source and remains local-audit-only. Vast.ai and RunPod remain
limited to reviewed public or synthetic
data and public model assets for model training, temporary feature extraction, and experiments;
hospital images, labels, embeddings, predictions and private checkpoints remain local/on-premises.

The cloud providers are temporary research compute, not authoritative deployment or production storage. A persistent
RunPod/Vast volume is optional training workspace/cache only. The authoritative inference environment is
local/on-premise, where champion weights are archived and the Model API, DR Review Workspace, Label Studio, DICOM,
model diff/drift, and HL7/FHIR are hosted. Vercel is the preferred public/synthetic demo frontend; it may host
adapters or measured CPU inference, but never hospital data/PHI or authoritative clinical inference.

Vast.ai และ RunPod เป็น provider choices ไม่มี plugin ที่เชื่อมต่อและไม่มีการจองเครื่องหรือใช้เงินในรอบนี้
RunPod Network Volume เป็น optional workspace/cache สำหรับ public research ไม่ใช่ hard dependency, authoritative
deployment หรือ production storage.
ใช้ `OCUFORGE_DATA_ROOT`, `OCUFORGE_MODEL_ROOT`, `OCUFORGE_CACHE_ROOT` และ `OCUFORGE_ARTIFACT_ROOT`
เพื่อให้ย้าย filesystem ได้โดยไม่แก้ model/data logic.

หลังรัน synthetic demo สามารถสร้างแผนคำสั่งได้:

```bash
python eyes-detected-models/jobs/gpu/job_plan.py --provider vast --images artifacts/smoke/images.jsonl
python eyes-detected-models/jobs/gpu/job_plan.py --provider runpod --images artifacts/smoke/images.jsonl
python eyes-detected-models/jobs/gpu/job_plan.py --provider onprem --images artifacts/smoke/images.jsonl
```

Output เป็น JSON แผน Docker argv เท่านั้น ยังไม่ execute, upload หรือ provision. Smoke job ยังคงฝึกบน CPU เพื่อทดสอบ integration; GPU training จริงและ performance validation ยังเป็นงานถัดไป

Docker GPU target ใช้ PyTorch 2.5.1 กับ CUDA 12.4 wheel ต้องตรวจ NVIDIA driver/runtime บนเครื่องจริงก่อน ถือเป็น compatibility candidate ไม่ใช่ผลทดสอบ GPU ที่ผ่านแล้ว

```bash
docker build -f eyes-detected-models/Dockerfile --target gpu-research -t ocuforge-gpu-research:0.1.0 .
docker run --rm --gpus all --network none ocuforge-gpu-research:0.1.0 python -c "import torch; print(torch.cuda.is_available())"
```

ก่อนใช้ public dataset ให้ตรวจ dataset access/license, hashes และ split freeze. สำหรับ R1 ให้ดู benchmark record ใน
`eyes-detected-models/configs/research/r1-global-benchmark.json` และ mount volume เอง. ภาพ local hospital ให้อยู่
on-prem ตามค่าเริ่มต้น; การอนุมัติการใช้ข้อมูลจริงเป็นคนละเรื่องกับการมี adapter ที่ทำงานได้ ไม่ใส่ raw data
ลง image และไม่ใช้ Google Drive/HF เป็นช่องทาง upload จาก starter. รอบ R0 V2 reconciliation นี้ไม่ provision
RunPod และไม่ download dataset ขนาดใหญ่. ก่อนเลือก model ให้บันทึก CPU inference latency, peak RAM, model size,
preprocessing latency และ GPU train cost เพิ่มจาก scientific metrics; metric สูงสุดเพียงอย่างเดียวไม่ทำให้เป็น
deployment champion หากรัน local/on-prem ไม่เหมาะสม.
