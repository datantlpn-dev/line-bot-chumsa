# LINE Bot ชุมสาย ลำพูน - Vercel + Google Sheets

LINE Bot ที่รับตำแหน่งที่ตั้งแล้วแสดงชุมสายที่ใกล้ที่สุด โดยใช้ข้อมูลจาก Google Sheets

---

## คุณสมบัติ

- ✅ **ไม่ต้องมี Server** - ใช้ Vercel Serverless Functions
- ✅ **อัปเดตข้อมูลง่าย** - แก้ไขใน Google Sheets โดยตรง
- ✅ **ฟรี 100%** - ไม่มีค่าใช้จ่าย
- ✅ **ไม่หลับ** - พร้อมใช้งาน 24/7
- ✅ **มี Cache** - ลด API calls และเพิ่มความเร็ว

---

## โครงสร้างโปรเจค

```
line-bot-chumsa/
├── api/
│   └── webhook.py          # Vercel Function หลัก
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel configuration
├── SETUP_GUIDE.md         # คู่มือติดตั้งแบบละเอียด
└── README.md
```

---

## ข้อมูลที่ต้องเตรียม

1. **LINE Channel Access Token** และ **Channel Secret**
   - จาก https://developers.line.biz/console

2. **Google Sheet ID**
   - สร้าง Google Sheets ใหม่
   - Import ข้อมูล 6,800 หมุดจาก `pins_import.csv`

3. **Google Service Account JSON**
   - สร้างจาก Google Cloud Console
   - แชร์ Google Sheets ให้ Service Account

---

## ติดตั้งแบบย่อ

```bash
# 1. Clone repo
git clone https://github.com/your-username/line-bot-chumsa.git
cd line-bot-chumsa

# 2. Deploy ไป Vercel
vercel

# 3. ตั้งค่า Environment Variables ใน Vercel Dashboard:
#    - LINE_CHANNEL_ACCESS_TOKEN
#    - LINE_CHANNEL_SECRET
#    - GOOGLE_SHEET_ID
#    - GOOGLE_CREDENTIALS_JSON

# 4. ตั้ง Webhook URL ใน LINE Developers:
#    https://your-project.vercel.app/api/webhook
```

**คู่มือละเอียด**: อ่านใน [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## การใช้งาน

1. Add Friend LINE Bot
2. ส่ง Location (📍) ให้ Bot
3. Bot จะตอบชุมสายที่ใกล้ที่สุด พร้อมลิงก์ดูแผนที่

---

## การอัปเดตข้อมูล

### วิธีที่ 1: แก้ไขใน Google Sheets
1. เปิด Google Sheets
2. แก้ไข/เพิ่ม/ลบแถว
3. รอ 5 นาที (cache หมดอายุ) หรือ Deploy ใหม่ทันที

### วิธีที่ 2: Import CSV ใหม่
1. แก้ไข `pins_import.csv`
2. Import ทับใน Google Sheets
3. รอ 5 นาที หรือ Deploy ใหม่

---

## Technical Details

### Cache Strategy
- ข้อมูลจาก Google Sheets cache นาน **5 นาที**
- ลด API calls จาก 300/นาที → ~12/ชั่วโมง
- ถ้าต้องการ real-time แก้ `CACHE_DURATION` ในโค้ด

### Performance
- **Cold start**: 2-4 วินาที (ครั้งแรก)
- **Warm**: ~1 วินาที (มี cache)
- รองรับ: ~1,500 users/นาที

### Quota & Limits
- Vercel: 100 GB Bandwidth/เดือน (ฟรี)
- Google Sheets API: 300 requests/นาที (ฟรี)
- Timeout: 10 วินาที/request

---

## Troubleshooting

### Bot ไม่ตอบ
```bash
# เช็ค Vercel logs
vercel logs --follow

# ทดสอบ Health Check
curl https://your-project.vercel.app/api/health
```

### ข้อมูลไม่อัปเดต
- รอ 5 นาที (cache)
- หรือ Deploy ใหม่ `vercel --prod`

### Error "Insufficient Permission"
- ตรวจสอบ Share Google Sheets ให้ Service Account
- เช็ค `client_email` ใน JSON ตรงกับที่ Share

---

## ข้อมูลเพิ่มเติม

- ข้อมูลชุมสาย: **195 ชุมสาย**
- ข้อมูลหมุด: **6,800 จุด**
- พื้นที่: **จังหวัดลำพูน**
- Google My Maps: `1hyMB4Sb3fpkfYkYIFFnG6Y6-Jq3EPAQ`

---

## License

MIT
