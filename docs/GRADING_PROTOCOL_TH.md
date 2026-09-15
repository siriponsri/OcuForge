# เกณฑ์ระดับ DR และการเปลี่ยนเวอร์ชัน

แหล่งหลักตามผู้ใช้: **International Council of Ophthalmology, ICO Guidelines for Diabetic Eye Care, Updated 2017**, Table 1 หน้าเอกสาร 2 (PDF หน้า 7) ตรวจจากไฟล์แนบโดยตรง และบันทึก SHA-256 ของไฟล์ต้นฉบับไว้ใน protocol config

| ค่า | ระดับ | สรุปเกณฑ์จาก ICO ฉบับแนบ |
|---|---|---|
| 0 | No apparent DR | ไม่พบความผิดปกติของ DR |
| 1 | Mild NPDR | Microaneurysms เท่านั้น |
| 2 | Moderate NPDR | Microaneurysms และอาการแสดงอื่น แต่ยังไม่ถึง severe |
| 3 | Severe NPDR | Moderate และเข้าอย่างน้อยหนึ่งเกณฑ์ 4-2-1 ด้านล่าง โดยไม่มี proliferative signs |
| 4 | PDR | ตาราง ICO อธิบาย severe NPDR ร่วมกับ neovascularization หรือ vitreous/preretinal hemorrhage |

เกณฑ์ severe ในฉบับนี้: intraretinal hemorrhages **≥20 ในแต่ละ quadrant ทั้ง 4 quadrants**, definite venous beading ใน **2 quadrants**, หรือ IRMA ใน **1 quadrant** ไม่เปลี่ยนเครื่องหมาย ≥ เป็น > ตามเอกสารอื่น

เป็นเกณฑ์อ้างอิงสำหรับแพทย์ ไม่ใช่ตัวตัดสินระดับจากจำนวน candidate lesions ของ AI หากข้อมูลภาพไม่พอหรือมีประวัติรักษา/laser scar/อาการแสดงขัดแย้ง ให้ใช้ uncertain/review แล้วให้แพทย์ตัดสิน ไม่ให้โปรแกรมลดเกรด PDR เพราะนับรอยโรคไม่ครบ

Ungradable และ uncertain แยกจากระดับ 0–4 ไม่สร้าง grade 5. ไม่มี autonomous referral rule

## เปลี่ยนเกณฑ์ในอนาคต

1. คัดลอก `eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json` เป็นไฟล์ใหม่
2. เปลี่ยน protocol_id/version และ source reference; ให้แพทย์ทบทวนการปรับใช้
3. รัน `load_protocol(path)` เพื่อ validate และสร้าง canonical config hash
4. ผูก ProtocolRef ใหม่กับ annotation batch ถัดไป; ห้ามแก้ hash ใน annotation เก่า
5. เก็บ migration note ระบุว่าระดับเดิมเทียบกับใหม่ได้หรือไม่ได้อย่างไร การเปลี่ยนจำนวนเกรดต้องเปลี่ยน CORAL/schema อย่างชัดเจน

`check_protocol` ปฏิเสธ record ที่ใช้ protocol/hash คนละฉบับ ห้ามรวมผลเพื่อรายงานโดยไม่มี compatibility review

## ข้อมูลเดิม

DR/no-DR จากประสบการณ์แพทย์เก็บเป็น binary assessment ไม่ทราบย้อนหลังว่าแต่ละภาพใช้ protocol version ใด ให้ protocol_id เป็น null ได้ ห้ามเติม ICO ให้ historical label โดยอัตโนมัติ

## DME

ประเมินเป็นแกนแยกจาก DR ตาม ICO ซึ่งกล่าวถึง retinal thickening และการประเมินสามมิติ ไม่ใช่ดู hard exudates แล้วสรุป DME โดยตรง starter ไม่สร้าง OCT-confirmed DME จากภาพ fundus/UWF เดี่ยว และยังไม่มี OCT workflow

คำอธิบายนี้ดัดแปลงเพื่อการวิจัยภายในที่ไม่ใช่เชิงพาณิชย์ โดยให้เครดิต ICO, January 2017 ไม่ได้คัดลอกภาพตัวอย่างหรือแจกจ่าย PDF ต้นฉบับ
