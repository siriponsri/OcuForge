# Workflow สำหรับแพทย์ (ฉบับเตรียม pilot)

1. เปิด synthetic/public rehearsal case ก่อน ตรวจ laterality และคุณภาพภาพ
2. งาน image grading: ใช้คู่มือ ICO ที่ตรึง version; เลือก 0–4 หรือ ungradable/uncertain
3. งาน MA: confirm/reject จุด AI, ย้ายจุดที่คลาดเคลื่อน, เพิ่มจุดที่ขาด
4. งาน region: ปรับ polygon/mask ตามชนิดรอยโรค ไม่ถือ evidence map เป็นขอบเขตรอยโรค
5. กรณีไม่แน่ใจ โดยเฉพาะ NVD/NVE ส่ง NEEDS_REVIEW ให้ specialist
6. ผู้จัดการข้อมูลจัด decision journal จากการ review และตรวจ native export; specialist adjudicate ก่อน lock

ยังไม่วัดความเร็ว UX หรือ pilot readiness บน CVAT จริง ไม่ควรขอเวลาหมอจนกว่าทีมวิศวกรรมจะ dry run import/edit/export/backup ผ่านแล้ว
