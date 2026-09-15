# ข้อมูลเพิ่มเติมที่มีผลเหนือสมมติฐานในสเปกเดิม

บันทึก 2026-09-09

1. ข้อมูล local ไม่ใช่ไม่มี label ทุกชนิด: ผู้ใช้ยืนยันว่ามี DR / no-DR ตามประสบการณ์แพทย์ แต่ไม่มีเกรด 0–4 และไม่มี lesion annotation/segmentation จึงใช้ `binary_assessment` แยกต่างหาก พร้อม DOCTOR_EXPERIENCE และ USER_REPORTED_NOT_ADJUDICATED ไม่ยกระดับเป็น expert-adjudicated label และไม่แปลง DR เป็น grade 1 หรือ no-DR เป็น ordinal grade 0 อัตโนมัติ
2. ไม่ทราบจำนวนภาพ การแยกผู้ป่วย ความสม่ำเสมอของเกณฑ์ หรือคุณภาพ label; ไม่ได้อ่านหรือดาวน์โหลด raw hospital image ในรอบนี้ ข้อมูลเดิมยังไม่เป็น locked benchmark
3. นิยาม DR หลักใช้ ICO Guidelines for Diabetic Eye Care, Updated 2017 ตามไฟล์แนบ: Table 1 หน้าเอกสาร 2 / PDF หน้า 7 มี config hash และ protocol version สำหรับ prediction/annotation ระดับโรค
4. เกณฑ์เป็นคู่มือให้แพทย์กำหนดระดับ ไม่ใช่ automatic diagnosis engine การเปลี่ยน config ต้องเปลี่ยน version และออก migration note; เก็บ label เก่าพร้อม protocol เดิม
5. เอกสารสเปกต้นฉบับใน `docs/specification/` เก็บเพื่อ provenance ข้อความ local labels=0 ในเอกสารเดิมหมายถึงไม่มี ordinal/localized labels ภายใต้ amendment นี้
6. ตรวจเอกสารเก่า EYE_DETECTED_POC_V2_3_RUNBOOK.md และ LICENSE_NOTES.md ผ่าน Drive แล้ว: งานเดิมแยก CEO_POC/FULL_RESEARCH และมี longitudinal กับ SAM3 แต่ starter ใหม่นี้ไม่สืบทอดโมเดล/ผลทดสอบ/สิทธิ์ใช้งานโดยอัตโนมัติ ไม่เพิ่ม HF deployment lane และไม่คัดลอก token, notebook output, checkpoint หรือ data

## DME

ICO อธิบาย DME แยกจาก DR และนิยามจาก retinal thickening ซึ่งอาศัยการประเมินสามมิติได้ ไม่ได้กำหนดว่า DME ทุกกรณีต้องมี OCT เท่านั้น แต่ starter ห้ามใช้ภาพ fundus/UWF เดี่ยวหรือ hard exudates เป็น OCT-confirmed DME; ยังไม่สร้าง OCT workflow ใน v0.1
