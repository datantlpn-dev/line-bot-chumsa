# คู่มือติดตั้ง LINE Bot บน Vercel + Google Sheets

---

## ภาพรวม

```
ผู้ใช้ส่ง Location
    ↓
LINE → Vercel Function
    ↓
อ่านข้อมูลจาก Google Sheets (มี cache 5 นาที)
    ↓
คำนวณหาชุมสาย
    ↓
ตอบกลับ LINE
```

---

## ขั้นตอนที่ 1: เตรียม Google Sheets

### 1.1 สร้าง Google Sheets
1. ไปที่ https://sheets.google.com
2. สร้าง Spreadsheet ใหม่ ชื่อ **"LINE Bot ชุมสาย"**

### 1.2 สร้าง Sheet "pins"
1. เปลี่ยนชื่อ Sheet แรกเป็น **pins**
2. ใส่ Header ในแถวที่ 1:
   ```
   A1: chumsa
   B1: lat
   C1: lng
   ```

### 1.3 Import ข้อมูล
1. ดาวน์โหลดไฟล์ `pins_import.csv` ที่แนบมา
2. ใน Google Sheets กด **File → Import**
3. เลือกไฟล์ `pins_import.csv`
4. Import location: **Replace current sheet**
5. กด **Import data**
6. ตรวจสอบ: ควรมี **6,800 แถว** (+ 1 header)

### 1.4 คัดลอก Sheet ID
- ดูจาก URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
- เก็บ **YOUR_SHEET_ID** ไว้ใช้ในขั้นตอนถัดไป

---

## ขั้นตอนที่ 2: สร้าง Google Service Account

### 2.1 เปิด Google Cloud Console
1. ไปที่ https://console.cloud.google.com
2. สร้าง Project ใหม่ (ถ้ายังไม่มี) เช่น "line-bot-chumsa"

### 2.2 เปิด Google Sheets API
1. ไปที่ **APIs & Services → Library**
2. ค้นหา **Google Sheets API**
3. กด **Enable**

### 2.3 สร้าง Service Account
1. ไปที่ **APIs & Services → Credentials**
2. กด **Create Credentials → Service Account**
3. ตั้งชื่อ: `line-bot-sheets`
4. Role: **Editor** (หรือ Viewer ถ้าไม่ต้องการให้แก้ไข)
5. กด **Done**

### 2.4 สร้าง JSON Key
1. คลิกที่ Service Account ที่สร้าง
2. ไปที่แท็บ **Keys**
3. กด **Add Key → Create new key**
4. เลือก **JSON**
5. กด **Create** → ดาวน์โหลดไฟล์ JSON

### 2.5 แชร์ Google Sheets ให้ Service Account
1. เปิดไฟล์ JSON ที่ดาวน์โหลด
2. คัดลอก **client_email** (จะหน้าตาแบบนี้: `xxx@xxx.iam.gserviceaccount.com`)
3. กลับไปที่ Google Sheets
4. กด **Share** (มุมขวาบน)
5. วาง email ของ Service Account
6. สิทธิ์: **Viewer** (อ่านได้อย่างเดียว)
7. กด **Send**

---

## ขั้นตอนที่ 3: Deploy บน Vercel

### 3.1 Push โค้ดขึ้น GitHub
1. สร้าง GitHub repo ใหม่ เช่น `line-bot-chumsa`
2. Upload ไฟล์ทั้งหมด:
   ```
   line-bot-chumsa/
   ├── api/
   │   └── webhook.py
   ├── requirements.txt
   └── vercel.json
   ```

### 3.2 เชื่อมต่อ Vercel กับ GitHub
1. ไปที่ https://vercel.com
2. Sign up ด้วย GitHub
3. กด **Add New → Project**
4. เลือก repo `line-bot-chumsa`
5. กด **Import**

### 3.3 ตั้งค่า Environment Variables
ก่อน Deploy ให้เพิ่ม Environment Variables ทั้งหมดนี้:

1. **LINE_CHANNEL_ACCESS_TOKEN**
   - Value: ค่าจาก LINE Developers Console

2. **LINE_CHANNEL_SECRET**
   - Value: ค่าจาก LINE Developers Console

3. **GOOGLE_SHEET_ID**
   - Value: Sheet ID จากขั้นตอน 1.4

4. **GOOGLE_CREDENTIALS_JSON**
   - Value: เปิดไฟล์ Service Account JSON → คัดลอกทั้งหมด (ทั้งไฟล์)
   - ⚠️ **สำคัญ**: ต้องวางทั้งไฟล์ JSON ตั้งแต่ `{` ถึง `}` รวมทุกอย่าง

### 3.4 Deploy
1. กด **Deploy**
2. รอ 2-3 นาที
3. เมื่อเสร็จจะได้ URL เช่น `https://line-bot-chumsa.vercel.app`

---

## ขั้นตอนที่ 4: ตั้งค่า LINE Webhook

1. ไปที่ https://developers.line.biz/console
2. เลือก Channel ของคุณ
3. ไปที่ **Messaging API**
4. ตั้ง **Webhook URL**:
   ```
   https://line-bot-chumsa.vercel.app/api/webhook
   ```
5. เปิด **Use webhook**: ON
6. ปิด **Auto-reply messages**: OFF
7. กด **Verify** → ควรขึ้น Success

---

## ขั้นตอนที่ 5: ทดสอบ

### 5.1 ทดสอบ Health Check
เปิด Browser ไปที่:
```
https://line-bot-chumsa.vercel.app/api/health
```

ควรได้:
```json
{
  "status": "ok",
  "pins_count": 6800,
  "cache_age_seconds": 0
}
```

### 5.2 ทดสอบกับ LINE
1. เปิด LINE → Add Friend Bot
2. ส่ง Location ให้ Bot
3. Bot ควรตอบภายใน 2-4 วินาที (ครั้งแรก)
4. ครั้งต่อไปจะเร็วขึ้น (~1 วินาที) เพราะมี cache

---

## การอัปเดตข้อมูล

### วิธีที่ 1: แก้ไขใน Google Sheets โดยตรง
1. เปิด Google Sheets
2. แก้ไข/เพิ่ม/ลบ แถวตามต้องการ
3. **รอ 5 นาที** (cache จะหมดอายุ)
4. หรือ Deploy ใหม่ทันที (Clear cache ทันที)

### วิธีที่ 2: Import CSV ใหม่
1. แก้ไขไฟล์ `pins_import.csv`
2. ใน Google Sheets: **File → Import**
3. เลือก **Replace current sheet**
4. รอ 5 นาที หรือ Deploy ใหม่

---

## Troubleshooting

### ปัญหา 1: Bot ไม่ตอบ
✅ เช็ค Vercel Logs: https://vercel.com/dashboard
✅ เช็ค Webhook URL ใน LINE Developers
✅ ตรวจสอบ Environment Variables ครบไหม

### ปัญหา 2: Error: "Insufficient Permission"
✅ ตรวจสอบว่า Share Google Sheets ให้ Service Account แล้วหรือยัง
✅ เช็ค client_email ใน JSON ตรงกับที่ Share ไหม

### ปัญหา 3: ช้ามาก (> 6 วินาที)
✅ ปกติครั้งแรกจะช้า (Cold start + โหลดข้อมูล)
✅ ครั้งต่อไปควรเร็วขึ้น (มี cache)
✅ ถ้ายังช้า ลอง Deploy ใหม่

### ปัญหา 4: Cache ไม่ทำงาน
✅ เช็ค `/api/health` ดู cache_age_seconds
✅ ถ้าเป็น null หรือ 0 ตลอด = cache ไม่ทำงาน
✅ อาจเป็นเพราะ Vercel cold start บ่อย (ใช้งานน้อย)

---

## ข้อมูลเพิ่มเติม

### Cache Strategy
- ข้อมูลจาก Google Sheets จะถูก cache ใน Memory นาน **5 นาที**
- ลด API calls จาก 300/วินาที → ~12/ชั่วโมง (ประหยัด quota)
- ถ้าต้องการข้อมูล real-time ลด `CACHE_DURATION` ในโค้ด

### Google API Quota
- **ฟรี**: 300 requests/นาที/โปรเจค
- **ด้วย cache 5 นาที**: Bot รับได้ ~1,500 users/นาที
- ถ้า quota เกิน → Bot จะใช้ cache เก่าต่อ (ไม่พัง)

### ค่าใช้จ่าย
- Vercel: **ฟรี** 100 GB Bandwidth/เดือน
- Google Sheets API: **ฟรี** 100%
- รวม: **ฟรีทั้งหมด** ✅

---

## คำสั่งที่มีประโยชน์

```bash
# ติดตั้ง Vercel CLI
npm install -g vercel

# Deploy จาก Command Line
cd line-bot-chumsa
vercel

# ดู Logs แบบ Real-time
vercel logs --follow

# ตั้ง Environment Variable จาก CLI
vercel env add LINE_CHANNEL_ACCESS_TOKEN
```

---

## ติดต่อ / สอบถาม

ถ้ามีปัญหาหรือข้อสงสัย สามารถ:
1. เช็ค Vercel Logs
2. ทดสอบ `/api/health`
3. ดู Error ใน LINE Developers Console → Logs
