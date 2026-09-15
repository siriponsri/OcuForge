# GPU execution ภายหลัง

## Current model-first gate

GPU work follows the completed R0 / MDL dataset and lesion-taxonomy freeze. The selected global dataset is
MMRDR UWF; IDRiD is the selected ROI source but remains local-audit-only. R1 B1 is ready but not executed:
frozen DINOv3 ViT-B/16 features, global-average pooling, and an ordinal CORAL head. Vast.ai and RunPod remain
limited to reviewed public or synthetic
data and public model assets;
hospital images, labels, embeddings, predictions and checkpoints remain local/on-premises.

Vast.ai และ RunPod เป็น provider choices ไม่มี plugin ที่เชื่อมต่อและไม่มีการจองเครื่องหรือใช้เงินในรอบนี้
RunPod Network Volume เป็น persistent storage ที่แนะนำสำหรับ public research แต่ไม่ใช่ hard dependency.
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

ก่อนใช้ public dataset ให้ตรวจ dataset access/license, hashes และ split freeze. สำหรับ R1 ให้ดูคำสั่งใน
`eyes-detected-models/configs/research/r1-global-b1.json` และ mount volume เอง. ภาพ local hospital ให้อยู่
on-prem ตามค่าเริ่มต้น; การอนุมัติการใช้ข้อมูลจริงเป็นคนละเรื่องกับการมี adapter ที่ทำงานได้ ไม่ใส่ raw data
ลง image และไม่ใช้ Google Drive/HF เป็นช่องทาง upload จาก starter. รอบ R0/R1-ready นี้ไม่ provision
RunPod และไม่ download dataset ขนาดใหญ่.
