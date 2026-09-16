# ข้อกำหนดเจ้าของโครงการสำหรับ OcuForge V3

เอกสารนี้เป็น supporting note ของ [`POC_MASTER_PLAN.md`](POC_MASTER_PLAN.md) ไม่ใช่แผนงานแยก

## ความหมายของข้อมูล

1. ข้อมูล local อาจมี DR / no-DR จากประสบการณ์แพทย์ แต่ไม่มีเกรด ordinal 0-4 และไม่มี lesion annotation โดยอัตโนมัติ
   เก็บเป็น `binary_assessment` พร้อม provenance เช่น `DOCTOR_EXPERIENCE` และ `USER_REPORTED_NOT_ADJUDICATED`
2. ห้ามแปลง DR เป็น grade 1 หรือ no-DR เป็น ordinal grade 0 โดยอัตโนมัติ และข้อมูล local ที่ยังไม่ audit ไม่ใช่ locked benchmark
3. การเปลี่ยน grading guidance ต้องสร้าง protocol version และ migration note ใหม่ โดยคง label และ protocol เดิมไว้
4. DME เป็นคนละแกนกับ DR ห้ามสรุป OCT-confirmed DME จากภาพ fundus หรือ UWF เดี่ยว และยังไม่มี OCT workflow ใน gate นี้

## ทิศทาง V3

- R0 ต้องตรวจ source/version/access, license, identity split, supervision, leakage, taxonomy และ foundation-model pretraining overlap
- R1 เปรียบเทียบ C0 ConvNeXt V2-Tiny, C1 FLAIR และ C2 DINOv3 patch Attention MIL ด้วย CE ก่อน
- Global DR และ ROI lesion เป็นคนละ model track; MMRDR image-level lesion presence ไม่ใช่ ROI geometry
- `templates/` ยังคงเป็น customer-facing DR Review Workspace; Label Studio Community เป็น internal ROI QA/HITL
- ภาพโรงพยาบาล, PHI, credentials, weights และ private derived artifacts อยู่ local/on-premise เท่านั้น

การตรวจเอกสารรอบนี้ไม่ download ภาพโรงพยาบาล ไม่ train model และไม่ provision cloud provider
