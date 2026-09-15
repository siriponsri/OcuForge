# GPU execution ภายหลัง

Vast.ai และ RunPod เป็น provider choices ไม่มี plugin ที่เชื่อมต่อและไม่มีการจองเครื่องหรือใช้เงินในรอบนี้

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

ก่อนใช้ public dataset ให้ตรวจ dataset access/license, hashes และ split freeze. ภาพ local hospital ให้อยู่ on-prem ตามค่าเริ่มต้น; การอนุมัติการใช้ข้อมูลจริงเป็นคนละเรื่องกับการมี adapter ที่ทำงานได้ ไม่ใส่ raw data ลง image และไม่ใช้ Google Drive/HF เป็นช่องทาง upload จาก starter
