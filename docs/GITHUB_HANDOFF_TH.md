# GitHub handoff — OcuForge v0.2

เป้าหมายและ source of truth ปัจจุบันคือ https://github.com/siriponsri/OcuForge repository นี้ live บน GitHub แล้ว การส่งงานใช้ commit ที่ตรวจสอบแล้วและสิทธิ์ Git ของผู้ดูแลตามปกติ ไม่เปลี่ยนสิทธิ์หรือใช้ช่องทางข้ามข้อจำกัด

มี local commit ของโค้ดที่ตรวจแล้วใน workspace; ZIP ไม่บรรจุ .git หลังแตก ZIP ใช้บัญชีที่มี write permission ของคุณ:

```bash
git init -b main
git add .
git commit -m "Add OcuForge v0.2 on-premises label storage and research pipelines"
git remote add origin https://github.com/siriponsri/OcuForge.git
git push -u origin main
```

ถ้า remote มี commit ใหม่ ให้ clone remote แล้วนำชุดไฟล์ที่ตรวจแล้วไป branch ใหม่ ไม่ force push ก่อน push ตรวจว่าไม่มี local data/exports/secrets/weights แม้ .gitignore จะเตรียมไว้แล้ว

GitHub เป็น source of truth; ZIP เป็น handoff artifact ไม่ใช้ Google Drive เป็น source repository ข้อมูลโรงพยาบาลรวม label/backup ไม่ส่ง GitHub/Vercel/HF/Vast
