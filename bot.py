import os
import re
import json
import random
import string
import asyncio
import logging
import tempfile
import datetime
import math
from io import BytesIO
from pathlib import Path
from functools import wraps
import requests
import qrcode
#from PIL import Image
from gtts import gTTS
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    filters, ContextTypes
)
from telegram.constants import ParseMode, ChatAction

# ═══════════════════════════════════════════
#                 الإعدادات
# ═══════════════════════════════════════════
BOT_TOKEN = "8680723152:AAEGDndik3KsdOj9aoxKvrq2UQZWVQoaRJM"
OWNER_ID = 0
BOT_NAME = "وعد"
DATA_FILE = "bot_data.json"
TEMP_DIR = tempfile.mkdtemp()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
#             قاعدة البيانات البسيطة
# ═══════════════════════════════════════════
class Database:
    def __init__(self):
        self.data = {
            "users": {},
            "banned": [],
            "stats": {"messages": 0, "commands": 0},
            "games": {}
        }
        self.load()

    def load(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
        except Exception:
            pass

    def save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_user(self, user):
        uid = str(user.id)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {
                "name": user.full_name,
                "username": user.username,
                "joined": str(datetime.datetime.now()),
                "messages": 0
            }
            self.save()

    def inc_messages(self, user_id):
        uid = str(user_id)
        if uid in self.data["users"]:
            self.data["users"][uid]["messages"] += 1
        self.data["stats"]["messages"] += 1
        self.save()

    def inc_commands(self):
        self.data["stats"]["commands"] += 1
        self.save()

    def ban_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data["banned"]:
            self.data["banned"].append(uid)
            self.save()

    def unban_user(self, user_id):
        uid = str(user_id)
        if uid in self.data["banned"]:
            self.data["banned"].remove(uid)
            self.save()

    def is_banned(self, user_id):
        return str(user_id) in self.data["banned"]

    def get_user_count(self):
        return len(self.data["users"])

    def get_all_users(self):
        return list(self.data["users"].keys())


db = Database()

# ═══════════════════════════════════════════
#              المحتوى العربي
# ═══════════════════════════════════════════
JOKES = [
    "واحد راح للدكتور قاله: يا دكتور كل ما أشرب شاي عيني تألمني\nقاله الدكتور: طلّع الملعقة من الكاس 😂",
    "مرة واحد نملة شالت فيل... قالوا لها: كيف؟ قالت: حب يقدر 😂",
    "واحد حاطط صورته على الثلاجة... عشان ينزل وزنه من الخوف 😂",
    "مدرس سأل طالب: وين البحر الميت؟ قال: والله ما دريت إنه مريض 😂",
    "واحد تزوج وحدة قصيرة عشان يقلل من المصايب 😂",
    "مرة واحد نام بالمقبرة... صحي لقى نفسه ميت من البرد 😂",
    "واحد قال لصاحبه: تعرف الفرق بين الجهل والذكاء؟ قال: لا. قال: شفت! 😂",
    "واحد دخل مكتبة قال: عندكم كتاب 'الرجل المتفوق'؟ قالوا: قسم الخيال العلمي 😂",
    "ليش النملة ما تدخل المستشفى؟ لأنها من الحشرات مو من المرضى 😂",
    "مدرس: اذكر 3 حيوانات فيها حرف السين. طالب: 3 سمكات 😂",
    "واحد اتصل على صاحبه قاله: وينك؟ قال: بالبيت. قال: طيب متى ترجع؟ 😂",
    "مرة واحد حرامي سرق كتاب رياضيات... عشان يحسب حساباته 😂",
    "واحد قال لأمه: أبي أتزوج. قالت: أولاً خلّص واجباتك 😂",
    "دكتور قال للمريض: عندك ضغط وسكر. قال: لا يا دكتور أنا ما جبت حلاوة 😂",
    "واحد فاتح محل وكاتب: نصلح كل شيء. جاه واحد قال: صلحلي حياتي 😂",
]

WISDOM = [
    "العقل زينة، والأدب خزينة 🌟",
    "من جدّ وجد، ومن زرع حصد 🌾",
    "لا تؤجل عمل اليوم إلى الغد ⏰",
    "العلم نور والجهل ظلام 📚",
    "الصبر مفتاح الفرج 🔑",
    "قل خيراً أو اصمت 🤫",
    "من صبر ظفر 🏆",
    "رب أخ لك لم تلده أمك 👥",
    "الوقت كالسيف إن لم تقطعه قطعك ⚔️",
    "العلم في الصغر كالنقش على الحجر 🪨",
    "خير الكلام ما قلّ ودلّ 💎",
    "إذا هبّت رياحك فاغتنمها 🌬️",
    "ليس الجمال بأثواب تزيّننا، إن الجمال جمال العلم والأدب ✨",
    "اطلبوا العلم من المهد إلى اللحد 📖",
    "الحكمة ضالة المؤمن 🕌",
]

DUAS = [
    "اللهم إني أسألك العفو والعافية في الدنيا والآخرة 🤲",
    "ربنا آتنا في الدنيا حسنة وفي الآخرة حسنة وقنا عذاب النار 🕌",
    "اللهم اغفر لي ذنبي كله، دقّه وجلّه، وأوله وآخره 🤲",
    "اللهم إني أعوذ بك من الهم والحزن والعجز والكسل 🤲",
    "رب اشرح لي صدري ويسر لي أمري 🌟",
    "اللهم لا سهل إلا ما جعلته سهلاً وأنت تجعل الحزن إذا شئت سهلاً 🤲",
    "اللهم إني أسألك الهدى والتقى والعفاف والغنى 🤲",
    "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم 🕌",
    "لا إله إلا أنت سبحانك إني كنت من الظالمين 🤲",
    "اللهم صلّ وسلم على نبينا محمد ﷺ",
]

AZKAR_SABAH = [
    "أصبحنا وأصبح الملك لله والحمد لله 🌅",
    "اللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور 🌟",
    "سبحان الله وبحمده عدد خلقه ورضا نفسه وزنة عرشه ومداد كلماته 📿",
    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم 🛡️",
    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري 🤲",
    "اللهم إني أصبحت أشهدك وأشهد حملة عرشك وملائكتك أنك أنت الله لا إله إلا أنت 🕌",
    "رضيت بالله رباً وبالإسلام ديناً وبمحمد ﷺ نبياً ورسولاً ☪️",
]

QUOTES = [
    "النجاح ليس نهاية الطريق، والفشل ليس قاتلاً. الشجاعة للاستمرار هي ما يهم — ونستون تشرشل 💪",
    "كن التغيير الذي تريد أن تراه في العالم — غاندي 🌍",
    "الخيال أهم من المعرفة — أينشتاين 🧠",
    "لا تخف من الفشل بل خف من عدم المحاولة — روي بينيت 🚀",
    "ابدأ من حيث أنت، استخدم ما لديك، افعل ما تستطيع — آرثر آش ⭐",
    "الطريقة الوحيدة لعمل شيء عظيم هي أن تحب ما تفعله — ستيف جوبز 🍎",
    "لا يهم كم تسير ببطء طالما لا تتوقف — كونفوشيوس 🐢",
    "كل إنجاز عظيم كان في البداية حلماً — هاريت تابمان ✨",
]

RIDDLES = [
    {"q": "ما هو الشيء الذي يمشي بلا أرجل؟ 🤔", "a": "الساعة"},
    {"q": "شيء له رقبة ولا رأس له، ما هو؟ 🤔", "a": "القارورة"},
    {"q": "ما هو الشيء الذي كلما أخذت منه كبر؟ 🤔", "a": "الحفرة"},
    {"q": "ما هو الباب الذي لا يمكن فتحه؟ 🤔", "a": "الباب المفتوح"},
    {"q": "ما الذي له عين ولا يرى؟ 🤔", "a": "الإبرة"},
    {"q": "شيء موجود في السماء وإذا أضفت إليه حرفاً أصبح في الأرض؟ 🤔", "a": "نجم - منجم"},
    {"q": "ما الذي يسمع بلا أذن ويتكلم بلا لسان؟ 🤔", "a": "الهاتف"},
    {"q": "أنا ابن الماء وإذا تركوني في الماء أموت، من أنا؟ 🤔", "a": "الثلج"},
    {"q": "ما هو الشيء الذي يوجد مرة في الدقيقة ومرتين في اللحظة ولا يوجد في الساعة؟ 🤔", "a": "حرف القاف"},
    {"q": "كلمة مكونة من 8 حروف ولكنها تجمع كل الحروف؟ 🤔", "a": "أبجدية"},
]

PROVERBS = [
    {"q": "أكمل المثل: اللي ما يعرف الصقر...", "a": "يشويه"},
    {"q": "أكمل المثل: عصفور في اليد خير من...", "a": "عشرة على الشجرة"},
    {"q": "أكمل المثل: من حفر حفرة...", "a": "لأخيه وقع فيها"},
    {"q": "أكمل المثل: الصبر...", "a": "مفتاح الفرج"},
    {"q": "أكمل المثل: رب أخ لك...", "a": "لم تلده أمك"},
    {"q": "أكمل المثل: العين بصيرة...", "a": "واليد قصيرة"},
    {"q": "أكمل المثل: على قد لحافك...", "a": "مد رجليك"},
    {"q": "أكمل المثل: يد واحدة ما...", "a": "تصفق"},
]

TRIVIA = [
    {"q": "ما هي عاصمة اليابان؟", "options": ["بكين", "طوكيو", "سيول", "بانكوك"], "correct": 1},
    {"q": "كم عدد كواكب المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "correct": 1},
    {"q": "ما هو أكبر محيط في العالم؟", "options": ["الأطلسي", "الهندي", "الهادئ", "المتجمد"], "correct": 2},
    {"q": "من هو مخترع المصباح الكهربائي؟", "options": ["نيوتن", "أديسون", "تسلا", "فاراداي"], "correct": 1},
    {"q": "ما هي أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "المسيسيبي", "اليانغتسي"], "correct": 0},
    {"q": "كم عدد أركان الإسلام؟", "options": ["4", "5", "6", "7"], "correct": 1},
    {"q": "ما هو أكبر كوكب في المجموعة الشمسية؟", "options": ["زحل", "المشتري", "نبتون", "أورانوس"], "correct": 1},
    {"q": "في أي سنة هبط الإنسان على القمر؟", "options": ["1965", "1967", "1969", "1971"], "correct": 2},
    {"q": "ما هي أصغر دولة في العالم؟", "options": ["موناكو", "الفاتيكان", "سان مارينو", "مالطا"], "correct": 1},
    {"q": "كم عدد سور القرآن الكريم؟", "options": ["110", "112", "114", "116"], "correct": 2},
]

EMOJI_MOVIES = [
    {"emoji": "🦁👑", "answer": "الأسد الملك"},
    {"emoji": "❄️👸", "answer": "فروزن"},
    {"emoji": "🕷️🦸‍♂️", "answer": "سبايدرمان"},
    {"emoji": "🧞‍♂️🏺", "answer": "علاء الدين"},
    {"emoji": "🤖👦", "answer": "وول إي"},
    {"emoji": "🦇🌃", "answer": "باتمان"},
    {"emoji": "💍🌋", "answer": "سيد الخواتم"},
    {"emoji": "🚢💔", "answer": "تايتنك"},
]

TRUTH_OR_FALSE = [
    {"q": "الشمس تدور حول الأرض", "a": False},
    {"q": "الحوت الأزرق هو أكبر حيوان على الأرض", "a": True},
    {"q": "عدد أسنان الإنسان البالغ 32 سناً", "a": True},
    {"q": "القمر ينتج ضوءه بنفسه", "a": False},
    {"q": "الماء يتكون من ذرة أكسجين وذرتي هيدروجين", "a": True},
    {"q": "أستراليا هي أصغر قارة في العالم", "a": True},
    {"q": "البطريق يستطيع الطيران", "a": False},
    {"q": "القاهرة عاصمة المغرب", "a": False},
    {"q": "جبل إيفرست هو أعلى جبل في العالم", "a": True},
    {"q": "الذهب ينجذب للمغناطيس", "a": False},
]

HOROSCOPES = {
    "الحمل": "♈ الحمل: يومك مليء بالطاقة والحيوية! استغل هذه الطاقة في إنجاز أهدافك 🔥",
    "الثور": "♉ الثور: فرص مالية رائعة تلوح في الأفق، كن مستعداً لاقتناصها 💰",
    "الجوزاء": "♊ الجوزاء: التواصل هو مفتاحك اليوم، تحدث مع من تحب 💬",
    "السرطان": "♋ السرطان: اعتنِ بصحتك النفسية اليوم وامنح نفسك بعض الراحة 🌊",
    "الأسد": "♌ الأسد: أنت نجم اليوم! الجميع يتطلع إليك وينتظر إبداعك ⭐",
    "العذراء": "♍ العذراء: ترتيب أفكارك سيساعدك على اتخاذ قرارات أفضل 📋",
    "الميزان": "♎ الميزان: التوازن في حياتك يبدأ من قراراتك اليوم ⚖️",
    "العقرب": "♏ العقرب: قوتك الداخلية ستساعدك على تجاوز أي تحدي 💪",
    "القوس": "♐ القوس: مغامرة جديدة بانتظارك، لا تخف من المجهول 🏹",
    "الجدي": "♑ الجدي: العمل الجاد سيؤتي ثماره قريباً، استمر 🏔️",
    "الدلو": "♒ الدلو: أفكارك المبتكرة ستفاجئ الجميع اليوم 💡",
    "الحوت": "♓ الحوت: حدسك قوي اليوم، اتبع قلبك 🐟",
}

# ═══════════════════════════════════════════
#              وظائف مساعدة
# ═══════════════════════════════════════════
def owner_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("⛔ هذا الأمر خاص بمالك البوت فقط!")
            return
        return await func(update, context)
    return wrapper

def not_banned(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if db.is_banned(update.effective_user.id):
            await update.message.reply_text("🚫 أنت محظور من استخدام البوت!")
            return
        return await func(update, context)
    return wrapper

async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

# ═══════════════════════════════════════════
#             الأوامر الأساسية
# ═══════════════════════════════════════════
@not_banned
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user)
    db.inc_commands()

    keyboard = [
        [InlineKeyboardButton("🎵 موسيقى", callback_data="menu_music"),
         InlineKeyboardButton("🖼️ صور", callback_data="menu_images")],
        [InlineKeyboardButton("🎮 ألعاب", callback_data="menu_games"),
         InlineKeyboardButton("🔍 بحث", callback_data="menu_search")],
        [InlineKeyboardButton("💬 تسلية", callback_data="menu_fun"),
         InlineKeyboardButton("🛠️ أدوات", callback_data="menu_tools")],
        [InlineKeyboardButton("📋 كل الأوامر", callback_data="menu_help")],
    ]

    welcome = (
        f"مرحباً {user.first_name}! 👋\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 أنا *{BOT_NAME}*، بوتك الذكي!\n\n"
        f"🎵 أحمّل لك الموسيقى\n"
        f"🖼️ أبحث لك عن الصور\n"
        f"🎮 ألعب معك ألعاب ممتعة\n"
        f"🔍 أبحث لك عن أي معلومة\n"
        f"💬 أتحدث معك وأسليك\n\n"
        f"اختر من القائمة أدناه أو أرسل /help 👇"
    )

    await update.message.reply_text(
        welcome, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    help_text = f"""
🤖 *أوامر {BOT_NAME}*
━━━━━━━━━━━━━━━━━━━

🎵 *الموسيقى:*
/music [اسم] — بحث وتحميل أغنية
/song [رابط] — تحميل من رابط يوتيوب
/lyrics [اسم] — كلمات أغنية
/voice [نص] — تحويل نص لصوت

🖼️ *الصور:*
/img [بحث] — بحث عن صور
/sticker — تحويل صورة لملصق
/qr [نص] — إنشاء كود QR

🎮 *الألعاب:*
/game — قائمة الألعاب
/guess — خمّن الرقم
/quiz — أسئلة ثقافية
/riddle — ألغاز
/rps — حجر ورقة مقص
/truth — صح أم خطأ
/word — لعبة الكلمات
/math — تحدي رياضيات
/emoji — خمّن الفيلم
/proverb — أكمل المثل

🔍 *البحث:*
/wiki [بحث] — ويكيبيديا
/tr [لغة] [نص] — ترجمة
/weather [مدينة] — الطقس
/calc [عملية] — حاسبة

💬 *التسلية:*
/joke — نكتة
/wisdom — حكمة
/dua — دعاء
/azkar — أذكار
/quote — اقتباس
/horoscope [برج] — حظك اليوم
/love — نسبة التوافق

⚙️ *عام:*
/start — القائمة الرئيسية
/help — كل الأوامر
/id — معرفك في تلغرام
/info — معلومات البوت
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════
#           تحميل الموسيقى
# ═══════════════════════════════════════════
@not_banned
async def music_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🎵 أرسل اسم الأغنية بعد الأمر\nمثال: /music فيروز صباح الخير")
        return

    query = " ".join(context.args)
    await send_typing(update, context)

    status_msg = await update.message.reply_text(f"🔍 جاري البحث عن: *{query}*...", parse_mode=ParseMode.MARKDOWN)

    try:
        import yt_dlp

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', query)
            duration = info.get('duration', 0)
            thumbnail = info.get('thumbnail', '')

            # Find the downloaded file
            filename = ydl.prepare_filename(info)
            mp3_file = filename.rsplit('.', 1)[0] + '.mp3'

            if os.path.exists(mp3_file):
                await status_msg.edit_text(f"📤 جاري إرسال: *{title}*...", parse_mode=ParseMode.MARKDOWN)

                with open(mp3_file, 'rb') as audio:
                    await update.message.reply_audio(
                        audio=audio,
                        title=title,
                        performer=BOT_NAME,
                        duration=duration,
                        caption=f"🎵 {title}\n⏱ المدة: {duration//60}:{duration%60:02d}\n\n🤖 بواسطة {BOT_NAME}"
                    )

                os.remove(mp3_file)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ حدث خطأ في التحميل، حاول مرة أخرى")

    except ImportError:
        await status_msg.edit_text(
            "⚠️ مكتبة yt-dlp غير مثبتة!\n"
            "ثبتها بالأمر:\n"
            "`pip install yt-dlp`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Music error: {e}")
        await status_msg.edit_text(f"❌ حدث خطأ: {str(e)[:100]}")

@not_banned
async def song_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🔗 أرسل رابط يوتيوب بعد الأمر\nمثال: /song https://youtube.com/watch?v=...")
        return

    url = context.args[0]
    await send_typing(update, context)
    status_msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        import yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio')
            duration = info.get('duration', 0)
            filename = ydl.prepare_filename(info)
            mp3_file = filename.rsplit('.', 1)[0] + '.mp3'

            if os.path.exists(mp3_file):
                with open(mp3_file, 'rb') as audio:
                    await update.message.reply_audio(
                        audio=audio, title=title, performer=BOT_NAME, duration=duration,
                        caption=f"🎵 {title}\n🤖 بواسطة {BOT_NAME}"
                    )
                os.remove(mp3_file)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ فشل التحميل")
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {str(e)[:100]}")

@not_banned
async def lyrics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🎤 أرسل اسم الأغنية\nمثال: /lyrics Imagine John Lennon")
        return
    query = " ".join(context.args)
    await send_typing(update, context)
    try:
        r = requests.get(f"https://api.lyrics.ovh/v1/{query.split()[0]}/{' '.join(query.split()[1:])}", timeout=10)
        if r.status_code == 200:
            lyrics = r.json().get("lyrics", "")[:3000]
            await update.message.reply_text(f"🎤 *كلمات الأغنية:*\n\n{lyrics}", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ لم أجد كلمات هذه الأغنية")
    except Exception:
        await update.message.reply_text("❌ حدث خطأ في البحث عن الكلمات")

@not_banned
async def voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🗣️ أرسل النص لتحويله لصوت\nمثال: /voice مرحبا كيف حالك")
        return
    text = " ".join(context.args)
    await send_typing(update, context)
    try:
        tts = gTTS(text=text, lang='ar')
        fp = os.path.join(TEMP_DIR, f"voice_{random.randint(1000,9999)}.mp3")
        tts.save(fp)
        with open(fp, 'rb') as voice:
            await update.message.reply_voice(voice=voice, caption=f"🗣️ {text[:50]}...")
        os.remove(fp)
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:100]}")


# ═══════════════════════════════════════════
#              الصور والميديا
# ═══════════════════════════════════════════
@not_banned
async def img_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🖼️ أرسل ما تريد البحث عنه\nمثال: /img قطط جميلة")
        return
    query = " ".join(context.args)
    await send_typing(update, context)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(
            f"https://www.google.com/search?q={query}&tbm=isch",
            headers=headers, timeout=10
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src.startswith('http') and 'gstatic' not in src:
                images.append(src)

        if images:
            selected = random.sample(images, min(3, len(images)))
            for img_url in selected:
                try:
                    await update.message.reply_photo(photo=img_url, caption=f"🖼️ {query}\n🤖 {BOT_NAME}")
                except Exception:
                    continue
        else:
            # Fallback: use Unsplash
            for i in range(3):
                url = f"https://source.unsplash.com/800x600/?{query}&sig={random.randint(1,10000)}"
                try:
                    await update.message.reply_photo(photo=url, caption=f"🖼️ {query}\n🤖 {BOT_NAME}")
                except Exception:
                    continue
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:100]}")

@not_banned
async def sticker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("📸 قم بالرد على صورة لتحويلها لملصق!")
        return
    try:
        photo = update.message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()

        img = Image.open(BytesIO(img_bytes))
        img = img.resize((512, 512))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        await update.message.reply_sticker(sticker=buf)
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:100]}")

@not_banned
async def qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("📱 أرسل النص أو الرابط\nمثال: /qr https://google.com")
        return
    text = " ".join(context.args)
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        await update.message.reply_photo(photo=buf, caption=f"📱 QR Code\n📝 {text[:100]}\n🤖 {BOT_NAME}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:100]}")


# ═══════════════════════════════════════════
#                 الألعاب
# ═══════════════════════════════════════════
@not_banned
async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    keyboard = [
        [InlineKeyboardButton("🔢 خمّن الرقم", callback_data="play_guess"),
         InlineKeyboardButton("❓ أسئلة ثقافية", callback_data="play_quiz")],
        [InlineKeyboardButton("🧩 ألغاز", callback_data="play_riddle"),
         InlineKeyboardButton("✊ حجر ورقة مقص", callback_data="play_rps")],
        [InlineKeyboardButton("✅ صح أم خطأ", callback_data="play_truth"),
         InlineKeyboardButton("🔤 لعبة الكلمات", callback_data="play_word")],
        [InlineKeyboardButton("🔢 تحدي رياضيات", callback_data="play_math"),
         InlineKeyboardButton("🎬 خمّن الفيلم", callback_data="play_emoji")],
        [InlineKeyboardButton("📜 أكمل المثل", callback_data="play_proverb")],
    ]
    await update.message.reply_text(
        "🎮 *اختر اللعبة:*\n━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    number = random.randint(1, 100)
    context.user_data['guess_number'] = number
    context.user_data['guess_attempts'] = 0
    context.user_data['in_game'] = 'guess'
    await update.message.reply_text(
        "🔢 *لعبة خمّن الرقم!*\n\n"
        "اخترت رقماً بين 1 و 100\n"
        "حاول تخمينه! أرسل رقماً 👇\n\n"
        "أرسل /cancel للإلغاء",
        parse_mode=ParseMode.MARKDOWN
    )

@not_banned
async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    q = random.choice(TRIVIA)
    context.user_data['quiz_answer'] = q['correct']
    keyboard = []
    for i, opt in enumerate(q['options']):
        keyboard.append([InlineKeyboardButton(opt, callback_data=f"quiz_{i}")])

    await update.message.reply_text(
        f"❓ *سؤال ثقافي:*\n\n{q['q']}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def riddle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    r = random.choice(RIDDLES)
    context.user_data['riddle_answer'] = r['a']
    context.user_data['in_game'] = 'riddle'
    keyboard = [[InlineKeyboardButton("💡 أظهر الإجابة", callback_data="riddle_show")]]
    await update.message.reply_text(
        f"🧩 *لغز:*\n\n{r['q']}\n\nأرسل إجابتك أو اضغط الزر 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def rps_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    keyboard = [
        [InlineKeyboardButton("🪨 حجر", callback_data="rps_rock"),
         InlineKeyboardButton("📄 ورقة", callback_data="rps_paper"),
         InlineKeyboardButton("✂️ مقص", callback_data="rps_scissors")],
    ]
    await update.message.reply_text(
        "✊ *حجر ورقة مقص!*\n\nاختر سلاحك 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def truth_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    q = random.choice(TRUTH_OR_FALSE)
    context.user_data['truth_answer'] = q['a']
    keyboard = [
        [InlineKeyboardButton("✅ صح", callback_data="truth_true"),
         InlineKeyboardButton("❌ خطأ", callback_data="truth_false")],
    ]
    await update.message.reply_text(
        f"✅❌ *صح أم خطأ:*\n\n{q['q']}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def word_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    words = ["برمجة", "تلغرام", "بايثون", "حاسوب", "إنترنت", "هاتف", "شاشة", "لوحة", "ذكاء", "روبوت"]
    word = random.choice(words)
    hidden = list("_" * len(word))
    # Show first and last letter
    hidden[0] = word[0]
    hidden[-1] = word[-1]
    context.user_data['word_game'] = word
    context.user_data['word_hidden'] = hidden
    context.user_data['word_attempts'] = 5
    context.user_data['in_game'] = 'word'

    await update.message.reply_text(
        f"🔤 *لعبة الكلمات!*\n\n"
        f"الكلمة: `{' '.join(hidden)}`\n"
        f"عدد الحروف: {len(word)}\n"
        f"المحاولات المتبقية: 5\n\n"
        f"أرسل حرفاً واحداً لتخمينه 👇",
        parse_mode=ParseMode.MARKDOWN
    )

@not_banned
async def math_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    ops = ['+', '-', '*']
    op = random.choice(ops)
    if op == '*':
        a, b = random.randint(2, 12), random.randint(2, 12)
    else:
        a, b = random.randint(10, 99), random.randint(10, 99)
    answer = eval(f"{a}{op}{b}")
    context.user_data['math_answer'] = answer
    context.user_data['in_game'] = 'math'

    op_display = {'*': '×', '+': '+', '-': '-'}[op]
    await update.message.reply_text(
        f"🔢 *تحدي رياضيات!*\n\n"
        f"❓ كم يساوي: *{a} {op_display} {b}* = ؟\n\n"
        f"أرسل الإجابة 👇",
        parse_mode=ParseMode.MARKDOWN
    )

@not_banned
async def emoji_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    movie = random.choice(EMOJI_MOVIES)
    context.user_data['emoji_answer'] = movie['answer']
    context.user_data['in_game'] = 'emoji'
    keyboard = [[InlineKeyboardButton("💡 أظهر الإجابة", callback_data="emoji_show")]]
    await update.message.reply_text(
        f"🎬 *خمّن الفيلم من الإيموجي!*\n\n"
        f"{movie['emoji']}\n\n"
        f"أرسل اسم الفيلم 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@not_banned
async def proverb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    p = random.choice(PROVERBS)
    context.user_data['proverb_answer'] = p['a']
    context.user_data['in_game'] = 'proverb'
    keyboard = [[InlineKeyboardButton("💡 أظهر الإجابة", callback_data="proverb_show")]]
    await update.message.reply_text(
        f"📜 *أكمل المثل:*\n\n{p['q']}\n\nأرسل الإجابة 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ═══════════════════════════════════════════
#            البحث والمعرفة
# ═══════════════════════════════════════════
@not_banned
async def wiki_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("📚 أرسل ما تريد البحث عنه\nمثال: /wiki برج إيفل")
        return
    query = " ".join(context.args)
    await send_typing(update, context)
    try:
        import wikipedia
        wikipedia.set_lang("ar")
        result = wikipedia.summary(query, sentences=5)
        await update.message.reply_text(
            f"📚 *{query}*\n━━━━━━━━━━━━━━━━━\n\n{result}\n\n🤖 {BOT_NAME}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        try:
            import wikipedia
            wikipedia.set_lang("en")
            result = wikipedia.summary(query, sentences=5)
            await update.message.reply_text(
                f"📚 *{query}*\n━━━━━━━━━━━━━━━━━\n\n{result}\n\n🤖 {BOT_NAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await update.message.reply_text("❌ لم أجد نتائج لبحثك")

@not_banned
async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if len(context.args) < 2:
        await update.message.reply_text(
            "🌐 *الترجمة:*\n"
            "/tr en مرحبا — ترجمة للإنجليزية\n"
            "/tr ar Hello — ترجمة للعربية\n"
            "/tr fr مرحبا — ترجمة للفرنسية",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    target_lang = context.args[0]
    text = " ".join(context.args[1:])
    await send_typing(update, context)
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        await update.message.reply_text(
            f"🌐 *الترجمة:*\n\n"
            f"📝 الأصل: {text}\n"
            f"🔄 الترجمة: {translated}\n\n"
            f"🤖 {BOT_NAME}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في الترجمة: {str(e)[:100]}")

@not_banned
async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🌤️ أرسل اسم المدينة\nمثال: /weather الرياض")
        return
    city = " ".join(context.args)
    await send_typing(update, context)
    try:
        # Using wttr.in free API
        r = requests.get(f"https://wttr.in/{city}?format=j1&lang=ar", timeout=10)
        if r.status_code == 200:
            data = r.json()
            current = data['current_condition'][0]
            temp = current['temp_C']
            feels = current['FeelsLikeC']
            humidity = current['humidity']
            desc = current.get('lang_ar', [{}])
            desc_text = desc[0].get('value', current.get('weatherDesc', [{}])[0].get('value', '')) if desc else ''
            wind = current['windspeedKmph']

            await update.message.reply_text(
                f"🌤️ *طقس {city}*\n━━━━━━━━━━━━━━━━━\n\n"
                f"🌡️ الحرارة: {temp}°C\n"
                f"🤔 الإحساس: {feels}°C\n"
                f"💧 الرطوبة: {humidity}%\n"
                f"💨 الرياح: {wind} كم/س\n"
                f"☁️ الحالة: {desc_text}\n\n"
                f"🤖 {BOT_NAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ لم أجد هذه المدينة")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:100]}")

@not_banned
async def calc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🔢 أرسل العملية الحسابية\nمثال: /calc 15 * 23 + 7")
        return
    expr = " ".join(context.args)
    try:
        # Safe eval
        allowed = set('0123456789+-*/().% ')
        if all(c in allowed for c in expr):
            result = eval(expr)
            await update.message.reply_text(
                f"🔢 *الحاسبة:*\n\n"
                f"📝 العملية: `{expr}`\n"
                f"✅ النتيجة: *{result}*\n\n"
                f"🤖 {BOT_NAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ عملية غير صالحة!")
    except Exception:
        await update.message.reply_text("❌ خطأ في العملية الحسابية")


# ═══════════════════════════════════════════
#            التسلية والمحادثة
# ═══════════════════════════════════════════
@not_banned
async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    await update.message.reply_text(random.choice(JOKES))

@not_banned
async def wisdom_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    await update.message.reply_text(random.choice(WISDOM))

@not_banned
async def dua_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    await update.message.reply_text(random.choice(DUAS))

@not_banned
async def azkar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    text = "📿 *أذكار الصباح:*\n━━━━━━━━━━━━━━━━━\n\n"
    for i, z in enumerate(AZKAR_SABAH, 1):
        text += f"{i}. {z}\n\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@not_banned
async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    await update.message.reply_text(random.choice(QUOTES))

@not_banned
async def horoscope_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        signs = " | ".join(HOROSCOPES.keys())
        await update.message.reply_text(
            f"🔮 *الأبراج:*\nاختر برجك:\n\n{signs}\n\nمثال: /horoscope الحمل",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    sign = context.args[0]
    if sign in HOROSCOPES:
        await update.message.reply_text(f"🔮 *حظك اليوم:*\n\n{HOROSCOPES[sign]}", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ برج غير معروف! أرسل /horoscope لمعرفة الأبراج المتاحة")

@not_banned
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    percentage = random.randint(30, 100)
    hearts = "❤️" * (percentage // 10)
    await update.message.reply_text(
        f"💕 *نسبة الحب والتوافق:*\n\n"
        f"{hearts}\n"
        f"النسبة: *{percentage}%*\n\n"
        f"{'💖 توافق رائع!' if percentage > 80 else '💛 توافق جيد!' if percentage > 60 else '🤔 محتاج شغل!'}",
        parse_mode=ParseMode.MARKDOWN
    )

@not_banned
async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"🆔 *معلوماتك:*\n━━━━━━━━━━━━━━━━━\n\n"
        f"👤 الاسم: {user.full_name}\n"
        f"🆔 الآيدي: `{user.id}`\n"
        f"📛 اليوزر: @{user.username or 'لا يوجد'}\n"
        f"💬 آيدي المحادثة: `{chat.id}`\n\n"
        f"🤖 {BOT_NAME}",
        parse_mode=ParseMode.MARKDOWN
    )

@not_banned
async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    uptime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    await update.message.reply_text(
        f"🤖 *معلومات {BOT_NAME}:*\n━━━━━━━━━━━━━━━━━\n\n"
        f"📊 المستخدمين: {db.get_user_count()}\n"
        f"💬 الرسائل: {db.data['stats']['messages']}\n"
        f"⚡ الأوامر: {db.data['stats']['commands']}\n"
        f"⏰ الوقت: {uptime}\n"
        f"🐍 بايثون: python-telegram-bot\n\n"
        f"🤖 {BOT_NAME}",
        parse_mode=ParseMode.MARKDOWN
    )

@not_banned
async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.inc_commands()
    if not context.args:
        await update.message.reply_text("🧠 اسألني أي سؤال!\nمثال: /ask ما هي عاصمة فرنسا؟")
        return
    question = " ".join(context.args)
    await send_typing(update, context)

    # Simple AI-like responses
    responses = {
        "كيف حالك": "أنا بخير والحمد لله! 😊 كيف حالك أنت؟",
        "اسمك": f"اسمي {BOT_NAME}! 🤖 أنا بوت ذكي مصمم لخدمتك",
        "من صنعك": "صنعني مطوّر موهوب باستخدام بايثون! 🐍",
        "عمرك": "أنا لا أكبر بالعمر، أنا أتطور بالتحديثات! 😄",
    }

    for key, response in responses.items():
        if key in question:
            await update.message.reply_text(response)
            return

    # Try Wikipedia
    try:
        import wikipedia
        wikipedia.set_lang("ar")
        result = wikipedia.summary(question, sentences=3)
        await update.message.reply_text(f"🧠 *إجابة:*\n\n{result}\n\n🤖 {BOT_NAME}", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        smart_replies = [
            f"🤔 سؤال رائع! '{question}' - دعني أفكر... أنصحك بالبحث في جوجل للحصول على إجابة دقيقة!",
            f"💡 '{question}' - هذا سؤال مثير! جرّب /wiki للبحث في ويكيبيديا",
            f"🧠 أحتاج وقت للتفكير في '{question}'! لكن يمكنك استخدام /wiki للبحث",
        ]
        await update.message.reply_text(random.choice(smart_replies))

@not_banned
async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ تم الإلغاء!")


# ═══════════════════════════════════════════
#            أوامر المالك
# ═══════════════════════════════════════════
@owner_only
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_user_count()
    msgs = db.data['stats']['messages']
    cmds = db.data['stats']['commands']
    banned = len(db.data['banned'])
    await update.message.reply_text(
        f"📊 *إحصائيات {BOT_NAME}:*\n━━━━━━━━━━━━━━━━━\n\n"
        f"👥 المستخدمين: {users}\n"
        f"💬 الرسائل: {msgs}\n"
        f"⚡ الأوامر: {cmds}\n"
        f"🚫 المحظورين: {banned}\n\n"
        f"🤖 {BOT_NAME}",
        parse_mode=ParseMode.MARKDOWN
    )

@owner_only
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📢 أرسل الرسالة بعد الأمر\nمثال: /broadcast مرحباً بالجميع!")
        return
    msg = " ".join(context.args)
    users = db.get_all_users()
    success = 0
    fail = 0
    status = await update.message.reply_text(f"📢 جاري البث لـ {len(users)} مستخدم...")

    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *رسالة من الإدارة:*\n\n{msg}", parse_mode=ParseMode.MARKDOWN)
            success += 1
        except Exception:
            fail += 1

    await status.edit_text(f"✅ تم البث!\n\n📤 نجح: {success}\n❌ فشل: {fail}")

@owner_only
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🚫 أرسل آيدي المستخدم\nمثال: /ban 123456789")
        return
    uid = context.args[0]
    db.ban_user(uid)
    await update.message.reply_text(f"✅ تم حظر المستخدم: {uid}")

@owner_only
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("✅ أرسل آيدي المستخدم\nمثال: /unban 123456789")
        return
    uid = context.args[0]
    db.unban_user(uid)
    await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم: {uid}")

@owner_only
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.data['users']
    if not users:
        await update.message.reply_text("📭 لا يوجد مستخدمين بعد")
        return
    text = f"👥 *المستخدمين ({len(users)}):*\n━━━━━━━━━━━━━━━━━\n\n"
    for uid, info in list(users.items())[:50]:
        text += f"• {info['name']} | `{uid}` | 💬{info['messages']}\n"
    if len(users) > 50:
        text += f"\n... و {len(users)-50} مستخدم آخر"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@owner_only
async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 جاري إعادة التشغيل...")
    os.execv(__file__, ['python'] + [__file__])
#          معالج الأزرار (Callbacks)
# ═══════════════════════════════════════════
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Menu callbacks
    if data == "menu_music":
        await query.edit_message_text(
            "🎵 *أوامر الموسيقى:*\n\n"
            "/music [اسم] — بحث وتحميل\n"
            "/song [رابط] — تحميل من رابط\n"
            "/lyrics [اسم] — كلمات أغنية\n"
            "/voice [نص] — تحويل لصوت",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_images":
        await query.edit_message_text(
            "🖼️ *أوامر الصور:*\n\n"
            "/img [بحث] — بحث عن صور\n"
            "/sticker — تحويل لملصق\n"
            "/qr [نص] — كود QR",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_games":
        keyboard = [
            [InlineKeyboardButton("🔢 خمّن الرقم", callback_data="play_guess"),
             InlineKeyboardButton("❓ أسئلة", callback_data="play_quiz")],
            [InlineKeyboardButton("🧩 ألغاز", callback_data="play_riddle"),
             InlineKeyboardButton("✊ حجر ورقة مقص", callback_data="play_rps")],
            [InlineKeyboardButton("✅ صح/خطأ", callback_data="play_truth"),
             InlineKeyboardButton("🔤 كلمات", callback_data="play_word")],
        ]
        await query.edit_message_text("🎮 *اختر لعبة:*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "menu_search":
        await query.edit_message_text(
            "🔍 *أوامر البحث:*\n\n"
            "/wiki [بحث] — ويكيبيديا\n"
            "/tr [لغة] [نص] — ترجمة\n"
            "/weather [مدينة] — الطقس\n"
            "/calc [عملية] — حاسبة\n"
            "/ask [سؤال] — اسأل الذكاء الاصطناعي",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_fun":
        await query.edit_message_text(
            "💬 *أوامر التسلية:*\n\n"
            "/joke — نكتة\n"
            "/wisdom — حكمة\n"
            "/dua — دعاء\n"
            "/azkar — أذكار\n"
            "/quote — اقتباس\n"
            "/horoscope — حظك اليوم\n"
            "/love — نسبة التوافق",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_tools":
        await query.edit_message_text(
            "🛠️ *الأدوات:*\n\n"
            "/id — معرفك\n"
            "/info — معلومات البوت\n"
            "/qr [نص] — كود QR\n"
            "/calc [عملية] — حاسبة\n"
            "/voice [نص] — تحويل لصوت",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_help":
        help_text = (
            "📋 *كل الأوامر:*\n━━━━━━━━━━━━━━━━━\n\n"
            "🎵 /music /song /lyrics /voice\n"
            "🖼️ /img /sticker /qr\n"
            "🎮 /game /guess /quiz /riddle /rps /truth /word /math /emoji /proverb\n"
            "🔍 /wiki /tr /weather /calc /ask\n"
            "💬 /joke /wisdom /dua /azkar /quote /horoscope /love\n"
            "🛠️ /id /info /help /start"
        )
        await query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)

    # Game play callbacks
    elif data == "play_guess":
        number = random.randint(1, 100)
        context.user_data['guess_number'] = number
        context.user_data['guess_attempts'] = 0
        context.user_data['in_game'] = 'guess'
        await query.edit_message_text(
            "🔢 *خمّن الرقم!*\n\nاخترت رقماً بين 1 و 100\nأرسل تخمينك! /cancel للإلغاء",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "play_quiz":
        q = random.choice(TRIVIA)
        context.user_data['quiz_answer'] = q['correct']
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_{i}")] for i, opt in enumerate(q['options'])]
        await query.edit_message_text(f"❓ *سؤال:*\n\n{q['q']}", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "play_riddle":
        r = random.choice(RIDDLES)
        context.user_data['riddle_answer'] = r['a']
        context.user_data['in_game'] = 'riddle'
        keyboard = [[InlineKeyboardButton("💡 الإجابة", callback_data="riddle_show")]]
        await query.edit_message_text(f"🧩 *لغز:*\n\n{r['q']}", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "play_rps":
        keyboard = [
            [InlineKeyboardButton("🪨 حجر", callback_data="rps_rock"),
             InlineKeyboardButton("📄 ورقة", callback_data="rps_paper"),
             InlineKeyboardButton("✂️ مقص", callback_data="rps_scissors")],
        ]
        await query.edit_message_text("✊ *اختر:*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "play_truth":
        q = random.choice(TRUTH_OR_FALSE)
        context.user_data['truth_answer'] = q['a']
        keyboard = [
            [InlineKeyboardButton("✅ صح", callback_data="truth_true"),
             InlineKeyboardButton("❌ خطأ", callback_data="truth_false")],
        ]
        await query.edit_message_text(f"✅❌ *صح أم خطأ:*\n\n{q['q']}", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "play_word":
        words = ["برمجة", "تلغرام", "بايثون", "حاسوب", "إنترنت"]
        word = random.choice(words)
        hidden = list("_" * len(word))
        hidden[0] = word[0]
        hidden[-1] = word[-1]
        context.user_data['word_game'] = word
        context.user_data['word_hidden'] = hidden
        context.user_data['word_attempts'] = 5
        context.user_data['in_game'] = 'word'
        await query.edit_message_text(
            f"🔤 *لعبة الكلمات!*\n\nالكلمة: `{' '.join(hidden)}`\nالمحاولات: 5\nأرسل حرفاً 👇",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "play_math":
        a, b = random.randint(10, 99), random.randint(10, 99)
        op = random.choice(['+', '-', '*'])
        answer = eval(f"{a}{op}{b}")
        context.user_data['math_answer'] = answer
        context.user_data['in_game'] = 'math'
        op_d = {'*': '×', '+': '+', '-': '-'}[op]
        await query.edit_message_text(
            f"🔢 *تحدي:* {a} {op_d} {b} = ؟\nأرسل الإجابة 👇",
            parse_mode=ParseMode.MARKDOWN
        )

    # Quiz answer
    elif data.startswith("quiz_"):
        idx = int(data.split("_")[1])
        correct = context.user_data.get('quiz_answer', -1)
        if idx == correct:
            await query.edit_message_text("✅ *إجابة صحيحة! أحسنت!* 🎉", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text("❌ *إجابة خاطئة!* حاول مرة أخرى مع /quiz", parse_mode=ParseMode.MARKDOWN)

    # RPS
    elif data.startswith("rps_"):
        choices = {'rock': '🪨 حجر', 'paper': '📄 ورقة', 'scissors': '✂️ مقص'}
        user_choice = data.split("_")[1]
        bot_choice = random.choice(list(choices.keys()))

        wins = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
        if user_choice == bot_choice:
            result = "🤝 تعادل!"
        elif wins[user_choice] == bot_choice:
            result = "🎉 فزت!"
        else:
            result = "😔 خسرت!"

        await query.edit_message_text(
            f"✊ *النتيجة:*\n\n"
            f"أنت: {choices[user_choice]}\n"
            f"أنا: {choices[bot_choice]}\n\n"
            f"*{result}*",
            parse_mode=ParseMode.MARKDOWN
        )

    # Truth
    elif data.startswith("truth_"):
        user_ans = data == "truth_true"
        correct = context.user_data.get('truth_answer', True)
        if user_ans == correct:
            await query.edit_message_text("✅ *صحيح! أحسنت!* 🎉", parse_mode=ParseMode.MARKDOWN)
        else:
            ans_text = "صح ✅" if correct else "خطأ ❌"
            await query.edit_message_text(f"❌ *خطأ!* الإجابة الصحيحة: {ans_text}", parse_mode=ParseMode.MARKDOWN)

    # Show answers
    elif data == "riddle_show":
        ans = context.user_data.get('riddle_answer', '...')
        context.user_data['in_game'] = None
        await query.edit_message_text(f"💡 *الإجابة:* {ans}", parse_mode=ParseMode.MARKDOWN)
    elif data == "emoji_show":
        ans = context.user_data.get('emoji_answer', '...')
        context.user_data['in_game'] = None
        await query.edit_message_text(f"🎬 *الفيلم:* {ans}", parse_mode=ParseMode.MARKDOWN)
    elif data == "proverb_show":
        ans = context.user_data.get('proverb_answer', '...')
        context.user_data['in_game'] = None
        await query.edit_message_text(f"📜 *الإجابة:* {ans}", parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════
#          معالج الرسائل النصية
# ═══════════════════════════════════════════
@not_banned
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    db.add_user(user)
    db.inc_messages(user.id)

    text = update.message.text.strip()
    game = context.user_data.get('in_game')

    # Game: Guess the number
    if game == 'guess':
        try:
            guess = int(text)
            number = context.user_data.get('guess_number', 50)
            context.user_data['guess_attempts'] += 1
            attempts = context.user_data['guess_attempts']

            if guess == number:
                context.user_data['in_game'] = None
                await update.message.reply_text(
                    f"🎉 *أحسنت! الرقم هو {number}!*\n"
                    f"عدد المحاولات: {attempts}\n\n"
                    f"{'🏆 ممتاز!' if attempts <= 5 else '👍 جيد!' if attempts <= 10 else '😅 المرة الجاية أفضل!'}",
                    parse_mode=ParseMode.MARKDOWN
                )
            elif guess < number:
                await update.message.reply_text(f"⬆️ الرقم أكبر! (محاولة {attempts})")
            else:
                await update.message.reply_text(f"⬇️ الرقم أصغر! (محاولة {attempts})")
        except ValueError:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً!")
        return

    # Game: Riddle
    if game == 'riddle':
        answer = context.user_data.get('riddle_answer', '')
        if text.strip() in answer or answer in text.strip():
            context.user_data['in_game'] = None
            await update.message.reply_text("✅ *إجابة صحيحة! أحسنت!* 🎉", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ إجابة خاطئة، حاول مرة أخرى!")
        return

    # Game: Math
    if game == 'math':
        try:
            user_ans = int(text)
            correct = context.user_data.get('math_answer', 0)
            context.user_data['in_game'] = None
            if user_ans == correct:
                await update.message.reply_text("✅ *صحيح! أحسنت!* 🎉", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(f"❌ خطأ! الإجابة: *{correct}*", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ أرسل رقماً!")
        return

    # Game: Emoji movie
    if game == 'emoji':
        answer = context.user_data.get('emoji_answer', '')
        context.user_data['in_game'] = None
        if text.strip() in answer or answer in text.strip():
            await update.message.reply_text("✅ *صحيح!* 🎉", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ خطأ! الفيلم: *{answer}*", parse_mode=ParseMode.MARKDOWN)
        return

    # Game: Proverb
    if game == 'proverb':
        answer = context.user_data.get('proverb_answer', '')
        context.user_data['in_game'] = None
        if text.strip() in answer or answer in text.strip():
            await update.message.reply_text("✅ *صحيح!* 🎉", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ خطأ! الإجابة: *{answer}*", parse_mode=ParseMode.MARKDOWN)
        return

    # Game: Word
    if game == 'word':
        word = context.user_data.get('word_game', '')
        hidden = context.user_data.get('word_hidden', [])
        attempts = context.user_data.get('word_attempts', 0)

        if len(text) == 1:  # Single letter guess
            letter = text
            if letter in word:
                for i, ch in enumerate(word):
                    if ch == letter:
                        hidden[i] = letter
                context.user_data['word_hidden'] = hidden
                if '_' not in hidden:
                    context.user_data['in_game'] = None
                    await update.message.reply_text(
                        f"🎉 *أحسنت! الكلمة هي: {word}*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await update.message.reply_text(
                        f"✅ حرف صحيح!\n\nالكلمة: `{' '.join(hidden)}`\nالمتبقي: {attempts}",
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                attempts -= 1
                context.user_data['word_attempts'] = attempts
                if attempts <= 0:
                    context.user_data['in_game'] = None
                    await update.message.reply_text(
                        f"😔 *خسرت! الكلمة هي: {word}*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await update.message.reply_text(
                        f"❌ حرف خطأ!\n\nالكلمة: `{' '.join(hidden)}`\nالمتبقي: {attempts}",
                        parse_mode=ParseMode.MARKDOWN
                    )
        elif text == word:  # Full word guess
            context.user_data['in_game'] = None
            await update.message.reply_text(f"🎉 *أحسنت! الكلمة هي: {word}*", parse_mode=ParseMode.MARKDOWN)
        else:
            attempts -= 1
            context.user_data['word_attempts'] = attempts
            if attempts <= 0:
                context.user_data['in_game'] = None
                await update.message.reply_text(f"😔 *خسرت! الكلمة هي: {word}*", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(f"❌ خطأ! المتبقي: {attempts}")
        return

    # Smart auto-reply for non-command messages
    greetings = ["مرحبا", "هلا", "السلام", "اهلا", "هاي", "مساء", "صباح"]
    if any(g in text for g in greetings):
        replies = [
            f"أهلاً وسهلاً! 👋 كيف أقدر أساعدك؟",
            f"مرحباً بك! 😊 أرسل /help لمعرفة أوامري",
            f"هلا والله! 🌟 شخبارك؟",
            f"يا هلا فيك! 💕 تحتاج شيء؟",
        ]
        await update.message.reply_text(random.choice(replies))
        return

    thanks = ["شكرا", "مشكور", "يعطيك", "تسلم"]
    if any(t in text for t in thanks):
        await update.message.reply_text(random.choice([
            "العفو! 😊 دائماً في الخدمة",
            "لا شكر على واجب! 💕",
            "الله يسلمك! 🌟",
        ]))
        return

    # Default response
    if len(text) > 2:
        keyboard = [
            [InlineKeyboardButton("🎵 موسيقى", callback_data="menu_music"),
             InlineKeyboardButton("🎮 ألعاب", callback_data="menu_games")],
            [InlineKeyboardButton("📋 الأوامر", callback_data="menu_help")],
        ]
        await update.message.reply_text(
            f"🤖 مرحباً! لم أفهم رسالتك\n"
            f"جرّب أحد الأوامر أو اختر من القائمة 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ═══════════════════════════════════════════
#              تشغيل البوت
# ═══════════════════════════════════════════
def main():
    print(f"""
╔══════════════════════════════════════════════════╗
║          🤖 {BOT_NAME} Bot is Starting...          ║
║         Powered by python-telegram-bot          ║
╚══════════════════════════════════════════════════╝
    """)

    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))

    # Music
    app.add_handler(CommandHandler("music", music_cmd))
    app.add_handler(CommandHandler("song", song_cmd))
    app.add_handler(CommandHandler("lyrics", lyrics_cmd))
    app.add_handler(CommandHandler("voice", voice_cmd))

    # Images
    app.add_handler(CommandHandler("img", img_cmd))
    app.add_handler(CommandHandler("sticker", sticker_cmd))
    app.add_handler(CommandHandler("qr", qr_cmd))

    # Games
    app.add_handler(CommandHandler("game", game_cmd))
    app.add_handler(CommandHandler("guess", guess_cmd))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("riddle", riddle_cmd))
    app.add_handler(CommandHandler("rps", rps_cmd))
    app.add_handler(CommandHandler("truth", truth_cmd))
    app.add_handler(CommandHandler("word", word_cmd))
    app.add_handler(CommandHandler("math", math_cmd))
    app.add_handler(CommandHandler("emoji", emoji_cmd))
    app.add_handler(CommandHandler("proverb", proverb_cmd))

    # Search
    app.add_handler(CommandHandler("wiki", wiki_cmd))
    app.add_handler(CommandHandler("tr", translate_cmd))
    app.add_handler(CommandHandler("weather", weather_cmd))
    app.add_handler(CommandHandler("calc", calc_cmd))

    # Fun
    app.add_handler(CommandHandler("joke", joke_cmd))
    app.add_handler(CommandHandler("wisdom", wisdom_cmd))
    app.add_handler(CommandHandler("dua", dua_cmd))
    app.add_handler(CommandHandler("azkar", azkar_cmd))
    app.add_handler(CommandHandler("quote", quote_cmd))
    app.add_handler(CommandHandler("horoscope", horoscope_cmd))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))

    # Utility
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("info", info_cmd))

    # Owner
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))

    # Callbacks & Messages
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()