"""
Vercel Serverless Function - LINE Bot ชุมสาย
ใช้ Google Sheets เป็นแหล่งข้อมูล
"""
import os
import json
import math
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, LocationMessage, TextMessage, TextSendMessage, FlexSendMessage

# ใช้ gspread สำหรับอ่าน Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# ============================================================
# ตั้งค่า LINE Bot
# ============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ============================================================
# ตั้งค่า Google Sheets
# ============================================================
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
MAP_ID = "1hyMB4Sb3fpkfYkYIFFnG6Y6-Jq3EPAQ"

# Cache ข้อมูลใน Memory (ลด API calls)
_pins_cache = None
_cache_timestamp = 0
CACHE_DURATION = 300  # 5 นาที

# ============================================================
# เชื่อมต่อ Google Sheets
# ============================================================
def get_google_sheets_client():
    """สร้าง client สำหรับ Google Sheets"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # ใช้ Service Account credentials จาก Environment Variable
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def load_pins_from_sheets():
    """โหลดข้อมูลหมุดจาก Google Sheets (มี cache)"""
    global _pins_cache, _cache_timestamp
    import time
    
    current_time = time.time()
    
    # ถ้ามี cache และยังไม่หมดอายุ → ใช้ cache
    if _pins_cache and (current_time - _cache_timestamp) < CACHE_DURATION:
        return _pins_cache
    
    # อ่านจาก Google Sheets
    try:
        client = get_google_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet('pins')
        data = sheet.get_all_records()
        
        # แปลงเป็น list ของ dict
        pins = []
        for row in data:
            pins.append({
                'chumsa': row['chumsa'],
                'lat': float(row['lat']),
                'lng': float(row['lng'])
            })
        
        # บันทึก cache
        _pins_cache = pins
        _cache_timestamp = current_time
        
        return pins
    except Exception as e:
        print(f"Error loading from Sheets: {e}")
        # ถ้า error และมี cache เก่า → ใช้ cache เก่า
        if _pins_cache:
            return _pins_cache
        raise

# ============================================================
# คำนวณระยะทาง Haversine
# ============================================================
def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (math.sin(dphi/2)**2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ============================================================
# หาชุมสายจากพิกัด
# ============================================================
def find_chumsa(user_lat, user_lng):
    """หาหมุดที่ใกล้ที่สุด"""
    pins = load_pins_from_sheets()
    
    best_pin = None
    best_dist = float('inf')
    
    for pin in pins:
        dist = haversine(user_lat, user_lng, pin['lat'], pin['lng'])
        if dist < best_dist:
            best_dist = dist
            best_pin = pin
    
    return best_pin['chumsa'], best_dist

# ============================================================
# สร้าง Flex Message
# ============================================================
def build_flex_message(chumsa_name, dist_m, user_lat, user_lng):
    map_url = f"https://www.google.com/maps/d/viewer?mid={MAP_ID}&z=14"
    user_location_url = f"https://www.google.com/maps?q={user_lat},{user_lng}"
    dist_text = f"{dist_m/1000:.1f} km" if dist_m >= 1000 else f"{dist_m:.0f} m"

    flex_content = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📍 พบชุมสายของคุณ", "color": "#ffffff", "size": "sm", "weight": "bold"},
                {"type": "text", "text": chumsa_name, "color": "#ffffff", "size": "xl", "weight": "bold", "wrap": True}
            ],
            "backgroundColor": "#006064",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "📡 ชุมสาย", "size": "sm", "color": "#555555", "flex": 2},
                        {"type": "text", "text": chumsa_name, "size": "sm", "color": "#111111", "weight": "bold", "flex": 3, "wrap": True}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "📏 หมุดใกล้สุด", "size": "sm", "color": "#555555", "flex": 2},
                        {"type": "text", "text": dist_text, "size": "sm", "color": "#111111", "flex": 3}
                    ]
                },
                {"type": "separator"},
                {"type": "text", "text": "กดปุ่มด้านล่างเพื่อดูหมุดทั้งหมดในพื้นที่", "size": "xs", "color": "#888888", "wrap": True}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "uri", "label": f"🗺️ ดูแผนที่", "uri": map_url},
                    "style": "primary",
                    "color": "#006064"
                },
                {
                    "type": "button",
                    "action": {"type": "uri", "label": "📍 ตำแหน่งของฉัน", "uri": user_location_url},
                    "style": "secondary"
                }
            ]
        }
    }
    return FlexSendMessage(alt_text=f"พบชุมสาย: {chumsa_name}", contents=flex_content)

# ============================================================
# Webhook Handler
# ============================================================
@app.route('/api/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    return jsonify({'status': 'ok'})

@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_lat = event.message.latitude
    user_lng = event.message.longitude
    
    try:
        chumsa_name, dist_m = find_chumsa(user_lat, user_lng)
        line_bot_api.reply_message(
            event.reply_token,
            build_flex_message(chumsa_name, dist_m, user_lat, user_lng)
        )
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้งครับ")
        )

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip()
    
    if text in ['สวัสดี', 'help', 'ช่วยเหลือ', 'วิธีใช้']:
        reply = (
            "📡 วิธีใช้งาน LINE Bot ชุมสาย\n\n"
            "1️⃣ กด 📎 (แนบไฟล์)\n"
            "2️⃣ เลือก 📍 ตำแหน่ง\n"
            "3️⃣ ส่งตำแหน่งของคุณมา\n\n"
            "Bot จะแสดงชุมสายที่ใกล้ที่สุด พร้อมลิงก์ดูหมุดทั้งหมดในพื้นที่ครับ 🗺️"
        )
    else:
        reply = "📍 กรุณาส่ง ตำแหน่งที่ตั้ง (Location) เพื่อค้นหาชุมสายครับ"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# ============================================================
# Health Check
# ============================================================
@app.route('/api/health', methods=['GET'])
def health():
    try:
        pins = load_pins_from_sheets()
        return jsonify({
            'status': 'ok',
            'pins_count': len(pins),
            'cache_age_seconds': int(time.time() - _cache_timestamp) if _pins_cache else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# สำหรับ Local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)
