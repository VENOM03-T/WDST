import telebot
import requests
import random
import time
import logging
import json
from datetime import datetime
import os
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# إعداد التوكن - استبدل هذا بتوكن البوت الخاص بك
BOT_TOKEN = '8680723152:AAEGDndik3KsdOj9aoxKvrq2UQZWVQoaRJM'
bot = telebot.TeleBot(BOT_TOKEN)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('djezzy_bot.log'),
        logging.StreamHandler()
    ]
)

HEADERS = {
    'User-Agent': "MobileApp/3.0.0",
    'Accept': "application/json",
    'Content-Type': "application/json",
    'accept-language': "ar",
    'Connection': "keep-alive"
}

# ملفات لحفظ البيانات
REGISTERED_NUMBERS_FILE = "registered_numbers.json"
USER_SESSIONS_FILE = "user_sessions.json"
PREMIUM_USERS_FILE = "premium_users.json"
BROADCAST_FILE = "broadcast.json"

# تحميل المستخدمين المميزين
def load_premium_users():
    if os.path.exists(PREMIUM_USERS_FILE):
        with open(PREMIUM_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_premium_user(user_id):
    users = load_premium_users()
    if user_id not in users:
        users.append(user_id)
        with open(PREMIUM_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    return False

def remove_premium_user(user_id):
    users = load_premium_users()
    if user_id in users:
        users.remove(user_id)
        with open(PREMIUM_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    return False

def is_premium(user_id):
    users = load_premium_users()
    return user_id in users

# تحميل الجلسات
def load_user_sessions():
    if os.path.exists(USER_SESSIONS_FILE):
        with open(USER_SESSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_session(user_id, data):
    sessions = load_user_sessions()
    sessions[str(user_id)] = data
    with open(USER_SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def get_user_session(user_id):
    sessions = load_user_sessions()
    return sessions.get(str(user_id), {})

# تحميل الأرقام المسجلة
def load_registered_numbers():
    if os.path.exists(REGISTERED_NUMBERS_FILE):
        with open(REGISTERED_NUMBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_registered_number(number_data):
    numbers = load_registered_numbers()
    numbers.append(number_data)
    with open(REGISTERED_NUMBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(numbers, f, ensure_ascii=False, indent=2)

# الدوال الأساسية من السورس الأصلي
def format_num(phone):
    phone = str(phone).strip()
    if phone.startswith('0'):
        return "213" + phone[1:]
    elif not phone.startswith('213'):
        return "213" + phone
    return phone

def generate_random_djezzy_no():
    prefix = random.choice(["077", "078", "079"])
    number = prefix + "".join([str(random.randint(0, 9)) for _ in range(7)])
    return number

def request_otp(msisdn):
    url = "https://apim.djezzy.dz/mobile-api/oauth2/registration"
    params = {
        'msisdn': msisdn,
        'client_id': "87pIExRhxBb3_wGsA5eSEfyATloa",
        'scope': "smsotp"
    }
    payload = {
        "consent-agreement": [{"marketing-notifications": False}],
        "is-consent": True
    }
    try:
        return requests.post(url, params=params, json=payload, headers=HEADERS, timeout=10)
    except Exception as e:
        logging.error(f"خطأ في طلب OTP: {e}")
        return None

def login_with_otp(mobile_number, otp):
    payload = {
        'otp': otp,
        'mobileNumber': mobile_number,
        'scope': "djezzyAppV2",
        'client_id': "87pIExRhxBb3_wGsA5eSEfyATloa",
        'client_secret': "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa",
        'grant_type': "mobile"
    }
    try:
        res = requests.post(
            "https://apim.djezzy.dz/mobile-api/oauth2/token",
            data=payload,
            headers={'User-Agent': "MobileApp/3.0.0"},
            timeout=10
        )
        if res.status_code == 200:
            return f"Bearer {res.json().get('access_token')}"
        return None
    except Exception as e:
        logging.error(f"خطأ في تسجيل الدخول: {e}")
        return None

def send_invitation(token, sender, receiver):
    try:
        inv = requests.post(
            f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/send-invitation/{sender}",
            json={"msisdnReciever": receiver},
            headers={**HEADERS, 'authorization': token},
            timeout=10
        )
        return inv.status_code in [200, 201]
    except Exception as e:
        logging.error(f"خطأ في إرسال الدعوة: {e}")
        return False

def activate_reward(token, sender):
    try:
        act = requests.post(
            f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/activate-reward/{sender}",
            json={"packageCode": "MGMBONUS1Go"},
            headers={**HEADERS, 'authorization': token},
            timeout=10
        )
        return act.status_code in [200, 201]
    except Exception as e:
        logging.error(f"خطأ في تفعيل المكافأة: {e}")
        return False

def process_registration(sender_number, otp, chat_id, message_id, attempts=50):
    """معالجة التسجيل وإرسال التحديثات"""
    
    # تحديث الحالة
    bot.edit_message_text(
        "🔄 جاري تسجيل الدخول...",
        chat_id,
        message_id
    )
    
    token = login_with_otp(sender_number, otp)
    if not token:
        bot.edit_message_text(
            "❌ فشل تسجيل الدخول. تأكد من صحة الكود.",
            chat_id,
            message_id
        )
        return False
    
    bot.edit_message_text(
        "✅ تم تسجيل الدخول بنجاح\n🔄 جاري البحث عن أرقام صالحة...",
        chat_id,
        message_id
    )
    
    max_attempts = attempts
    success_count = 0
    
    for attempt in range(max_attempts):
        # تحديث الحالة كل 10 محاولات
        if attempt % 10 == 0:
            try:
                bot.edit_message_text(
                    f"🔄 جاري المحاولة {attempt + 1}/{max_attempts}\n✅ تم التسجيل: {success_count} جيغا",
                    chat_id,
                    message_id
                )
            except:
                pass
        
        target = generate_random_djezzy_no()
        target_f = format_num(target)
        
        logging.info(f"محاولة {attempt + 1}: إرسال دعوة للرقم {target}")
        
        if send_invitation(token, sender_number, target_f):
            logging.info(f"✅ تم إرسال الدعوة بنجاح للرقم {target}")
            
            request_otp(target_f)
            time.sleep(2)
            
            if activate_reward(token, sender_number):
                success_count += 1
                
                # حفظ الرقم المسجل
                number_data = {
                    "user_id": chat_id,
                    "sender": sender_number,
                    "target": target,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success"
                }
                save_registered_number(number_data)
                
                # تحديث الحالة
                bot.edit_message_text(
                    f"✅ تم تفعيل {success_count} جيغا بنجاح!\n🔄 جاري الاستمرار...",
                    chat_id,
                    message_id
                )
        
        time.sleep(1)
    
    # النتيجة النهائية
    final_message = f"""🎉 **اكتملت العملية!**

✅ تم تفعيل: {success_count} جيغا
📱 الرقم: {sender_number}
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

لبدء عملية جديدة أرسل /start
"""
    bot.edit_message_text(final_message, chat_id, message_id, parse_mode='Markdown')
    
    # إرسال إحصائيات للمستخدم
    stats = get_user_stats(chat_id)
    bot.send_message(chat_id, stats, parse_mode='Markdown')
    
    return True

def get_user_stats(user_id):
    """الحصول على إحصائيات المستخدم"""
    numbers = load_registered_numbers()
    user_numbers = [n for n in numbers if n.get('user_id') == user_id]
    
    total_gb = len(user_numbers)
    
    if total_gb == 0:
        return "📊 لا توجد إحصائيات بعد"
    
    last_5 = user_numbers[-5:]
    
    stats = f"""📊 **إحصائياتك الشخصية**

✅ إجمالي الجيغا المفعلة: {total_gb}

📱 آخر 5 أرقام مسجلة:
"""
    for i, num in enumerate(last_5, 1):
        stats += f"{i}. {num['sender']} -> +1GB ({num['timestamp']})\n"
    
    return stats

def get_global_stats():
    """إحصائيات عامة للبوت"""
    numbers = load_registered_numbers()
    users = set()
    total_gb = 0
    
    for num in numbers:
        users.add(num.get('user_id'))
        total_gb += 1
    
    premium_users = load_premium_users()
    
    stats = f"""📊 **إحصائيات البوت العامة**

👥 عدد المستخدمين: {len(users)}
⭐ المستخدمين المميزين: {len(premium_users)}
📦 إجمالي الجيغا المفعلة: {total_gb}
📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

تم التطوير بواسطة: @i1veno (VENOM)
"""
    return stats

# أوامر البوت
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome = f"""🌟 **مرحباً بك في بوت تفعيل 1 جيغا من اتصالات الجزائر!** 🌟

👤 **المطور:** @i1veno (VENOM)

هذا البوت يساعدك في تفعيل عروض 1 جيغا بشكل آلي.

**الأوامر المتاحة:**
/start - بدء الاستخدام
/help - المساعدة
/stats - إحصائياتك
/new - عملية جديدة
/vip - العضوية المميزة
/info - معلومات البوت
/about - عن المطور

**لبدء عملية جديدة أرسل /new**
"""
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # الصف الأول
    keyboard.add(
        InlineKeyboardButton("🚀 عملية جديدة", callback_data="new_process"),
        InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats")
    )
    
    # الصف الثاني
    keyboard.add(
        InlineKeyboardButton("⭐ العضوية المميزة", callback_data="show_vip"),
        InlineKeyboardButton("ℹ️ معلومات البوت", callback_data="show_info")
    )
    
    # الصف الثالث
    keyboard.add(
        InlineKeyboardButton("📢 قناة السورس", url="https://t.me/flt_8"),
        InlineKeyboardButton("👤 المطور VENOM", url="https://t.me/i1veno")
    )
    
    # الصف الرابع (أزرار إضافية)
    keyboard.add(
        InlineKeyboardButton("❓ مساعدة", callback_data="show_help"),
        InlineKeyboardButton("📞 دعم فني", url="https://t.me/i1veno")
    )
    
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = f"""📚 **كيفية استخدام البوت:**

1️⃣ أرسل /new لبدء عملية جديدة
2️⃣ أدخل رقم اتصالات الجزائر الخاص بك
3️⃣ أدخل الكود الذي سيصلك في الرسالة
4️⃣ انتظر حتى يكتمل التفعيل

**مميزات العضوية المميزة VIP:**
• 100 محاولة بدلاً من 50
• دعم فني مباشر
• أولوية في التحديثات
• خصومات على العروض

**ملاحظات مهمة:**
• تأكد من إدخال الرقم بشكل صحيح
• البوت يعمل 24/7
• يمكنك تفعيل عدة جيغا في نفس العملية

**للاستفسار والدعم الفني:**
👤 المطور: @i1veno (VENOM)
📢 القناة: @flt_8
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    stats = get_user_stats(message.chat.id)
    bot.send_message(message.chat.id, stats, parse_mode='Markdown')

@bot.message_handler(commands=['vip'])
def vip_command(message):
    chat_id = message.chat.id
    vip_text = f"""⭐ **العضوية المميزة VIP** ⭐

**مميزات VIP:**
✅ 100 محاولة في كل عملية (بدلاً من 50)
✅ دعم فني مباشر من المطور
✅ أولوية في التحديثات الجديدة
✅ إمكانية طلب ميزات خاصة
✅ خصومات على العروض القادمة

**السعر:**
💎 VIP مجاني حالياً (قيد التطوير)

**لطلب VIP:**
👤 تواصل مع المطور: @i1veno (VENOM)

{ '🌟 أنت عضو VIP حالياً!' if is_premium(chat_id) else '⚡ لست عضواً VIP بعد' }
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("👤 تواصل مع المطور", url="https://t.me/i1veno")
    )
    
    bot.send_message(message.chat.id, vip_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['info'])
def info_command(message):
    info_text = f"""ℹ️ **معلومات البوت:**

• **الاسم:** Djezzy GB Bot
• **الإصدار:** 2.0
• **اللغة:** Python
• **المطور:** @i1veno (VENOM)
• **تاريخ التحديث:** 2024

**المميزات:**
✅ تفعيل آلي 1GB
✅ يعمل 24/7
✅ حفظ الإحصائيات
✅ واجهة تفاعلية
✅ دعم فني مباشر

**إحصائيات سريعة:**
{get_global_stats()}
"""
    bot.send_message(message.chat.id, info_text, parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def about_command(message):
    about_text = f"""👤 **عن المطور VENOM**

• **الاسم:** VENOM
• **اليوزر:** @i1veno
• **الاختصاص:** برمجة بوتات تليغرام
• **الخبرة:** 3+ سنوات

**المشاريع:**
✅ بوتات تفعيل
✅ بوتات تسويق
✅ بوتات خدمات

**للتواصل:**
📱 تليغرام: @i1veno
📢 القناة: https://t.me/flt_8

**شكراً لاستخدامك البوت!** 🌟
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("👤 تواصل مع المطور", url="https://t.me/i1veno"),
        InlineKeyboardButton("📢 القناة", url="https://t.me/your_channel")
    )
    
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['new'])
def new_process(message):
    chat_id = message.chat.id
    
    # بدء جلسة جديدة
    session = {
        'step': 'waiting_phone',
        'phone': None,
        'otp': None,
        'message_id': None
    }
    save_user_session(chat_id, session)
    
    msg = bot.send_message(
        chat_id,
        "📱 **أدخل رقم اتصالات الجزائر الخاص بك**\nمثال: `0770123456`",
        parse_mode='Markdown'
    )
    
    # حفظ ID الرسالة للتحديث لاحقاً
    session['prompt_message_id'] = msg.message_id
    save_user_session(chat_id, session)

# أوامر المطور (Admin)
@bot.message_handler(commands=['admin'])
def admin_command(message):
    chat_id = message.chat.id
    # التحقق من أن المستخدم هو المطور
    if str(chat_id) != 'YOUR_ADMIN_ID':  # ضع معرفك هنا
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    admin_text = f"""🔧 **أوامر المطور VENOM**

👤 المستخدم: @i1veno

**أوامر الإدارة:**
/addpremium [user_id] - إضافة مستخدم VIP
/removepremium [user_id] - إزالة مستخدم VIP
/listpremium - عرض قائمة VIP
/globalstats - إحصائيات عامة
/broadcast [رسالة] - إرسال للجميع
/getusers - عدد المستخدمين

**مثال:**
/addpremium 123456789
"""
    bot.send_message(chat_id, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['addpremium'])
def add_premium(message):
    chat_id = message.chat.id
    # التحقق من أن المستخدم هو المطور
    if str(chat_id) != '8076256532':
        return
    
    try:
        user_id = int(message.text.split()[1])
        if save_premium_user(user_id):
            bot.reply_to(message, f"✅ تمت إضافة المستخدم {user_id} إلى VIP")
        else:
            bot.reply_to(message, f"⚠️ المستخدم {user_id} موجود بالفعل في VIP")
    except:
        bot.reply_to(message, "❌ استخدام: /addpremium [user_id]")

@bot.message_handler(commands=['removepremium'])
def remove_premium(message):
    chat_id = message.chat.id
    # التحقق من أن المستخدم هو المطور
    if str(chat_id) != 'YOUR_ADMIN_ID':
        return
    
    try:
        user_id = int(message.text.split()[1])
        if remove_premium_user(user_id):
            bot.reply_to(message, f"✅ تمت إزالة المستخدم {user_id} من VIP")
        else:
            bot.reply_to(message, f"⚠️ المستخدم {user_id} غير موجود في VIP")
    except:
        bot.reply_to(message, "❌ استخدام: /removepremium [user_id]")

@bot.message_handler(commands=['listpremium'])
def list_premium(message):
    chat_id = message.chat.id
    # التحقق من أن المستخدم هو المطور
    if str(chat_id) != '8076256532':
        return
    
    premium_users = load_premium_users()
    if premium_users:
        text = "⭐ **قائمة VIP:**\n\n"
        for user in premium_users:
            text += f"• `{user}`\n"
    else:
        text = "📭 لا يوجد مستخدمين VIP حالياً"
    
    bot.send_message(chat_id, text, parse_mode='Markdown')

@bot.message_handler(commands=['globalstats'])
def global_stats(message):
    chat_id = message.chat.id
    # التحقق من أن المستخدم هو المطور
    if str(chat_id) != '8076256532':
        return
    
    stats = get_global_stats()
    bot.send_message(chat_id, stats, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "new_process":
        bot.answer_callback_query(call.id)
        new_process(call.message)
    elif call.data == "show_stats":
        bot.answer_callback_query(call.id)
        stats = get_user_stats(call.message.chat.id)
        bot.send_message(call.message.chat.id, stats, parse_mode='Markdown')
    elif call.data == "show_vip":
        bot.answer_callback_query(call.id)
        vip_command(call.message)
    elif call.data == "show_info":
        bot.answer_callback_query(call.id)
        info_command(call.message)
    elif call.data == "show_help":
        bot.answer_callback_query(call.id)
        help_command(call.message)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    session = get_user_session(chat_id)
    
    if not session or session.get('step') == 'waiting_phone':
        # معالجة إدخال الرقم
        phone = message.text.strip()
        
        # التحقق من صحة الرقم
        if not phone.replace(' ', '').isdigit() or len(phone) < 9:
            bot.reply_to(message, "❌ رقم غير صالح. أعد المحاولة مع /new")
            return
        
        # تنسيق الرقم
        formatted_phone = format_num(phone)
        
        # طلب OTP
        status_msg = bot.send_message(chat_id, "🔄 جاري إرسال كود التحقق...")
        
        otp_response = request_otp(formatted_phone)
        
        if otp_response and otp_response.status_code in [200, 201]:
            bot.edit_message_text(
                "✅ تم إرسال الكود بنجاح!\n📨 **أدخل الكود الذي وصلتك:**",
                chat_id,
                status_msg.message_id,
                parse_mode='Markdown'
            )
            
            # تحديث الجلسة
            session['step'] = 'waiting_otp'
            session['phone'] = formatted_phone
            session['status_message_id'] = status_msg.message_id
            save_user_session(chat_id, session)
        else:
            bot.edit_message_text(
                "❌ فشل إرسال الكود. تأكد من صحة الرقم وحاول مرة أخرى.\nللبدء من جديد أرسل /new",
                chat_id,
                status_msg.message_id
            )
    
    elif session.get('step') == 'waiting_otp':
        # معالجة إدخال OTP
        otp = message.text.strip()
        
        if not otp.isdigit() or len(otp) != 4:
            bot.reply_to(message, "❌ الكود غير صالح. يجب أن يكون 4 أرقام.\nأرسل /new للمحاولة مرة أخرى")
            return
        
        # إعلام المستخدم ببدء العملية
        processing_msg = bot.send_message(
            chat_id,
            "🔄 **جاري بدء عملية التفعيل...**\nقد تستغرق العملية بضع دقائق",
            parse_mode='Markdown'
        )
        
        # تحديد عدد المحاولات حسب نوع العضوية
        attempts = 100 if is_premium(chat_id) else 50
        
        # بدء المعالجة في thread منفصل
        thread = threading.Thread(
            target=process_registration,
            args=(session['phone'], otp, chat_id, processing_msg.message_id, attempts)
        )
        thread.start()
        
        # تنظيف الجلسة
        session = {}
        save_user_session(chat_id, session)

# دالة لتشغيل البوت بشكل مستمر
def run_bot():
    while True:
        try:
            logging.info("🚀 بدء تشغيل البوت...")
            print("✅ البوت يعمل الآن...")
            print("👤 المطور: @i1veno (VENOM)")
            print("📱 توكن البوت:", BOT_TOKEN[:10] + "...")
            print("⚡ في انتظار الرسائل...")
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            logging.error(f"❌ خطأ في البوت: {e}")
            print(f"❌ حدث خطأ: {e}")
            print("🔄 جاري إعادة التشغيل بعد 5 ثواني...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    run_bot()