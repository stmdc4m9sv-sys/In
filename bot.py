import telebot
from telebot import types
import requests
import time
import threading

# إعدادات البوت - التوكن الخاص بك
API_TOKEN = '8340668436:AAG1FehM_WdoAvb97goQ_DNiYdTu9fMF2Eo'
bot = telebot.TeleBot(API_TOKEN)

class InstagramSniperPro:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.instagram.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "X-IG-App-ID": "936619743392459",
        }
        self.is_running = False
        self.targets = []
        self.user_id = None
        self.stats = {"attempts": 0}
        self.account_info = {"username": "", "email": "", "name": ""}

    def login_via_session(self, session_id):
        self.session.cookies.set("sessionid", session_id)
        try:
            r = self.session.get(f"{self.base_url}/accounts/edit/?__a=1&__d=dis", headers=self.headers)
            if "form_data" in r.text:
                data = r.json()["form_data"]
                self.account_info["username"] = data.get("username", "")
                self.account_info["email"] = data.get("email", "")
                self.account_info["name"] = data.get("first_name", "")
                
                # تحديث الـ CSRF Token من الكوكيز
                for cookie in self.session.cookies:
                    if cookie.name == "csrftoken":
                        self.headers["X-CSRFToken"] = cookie.value
                return True
            return False
        except: return False

    def claim_username(self, target_username):
        data = {
            "username": target_username,
            "email": self.account_info["email"],
            "first_name": self.account_info["name"],
            "phone_number": ""
        }
        try:
            r = self.session.post(f"{self.base_url}/accounts/edit/", headers=self.headers, data=data)
            self.stats["attempts"] += 1
            if '"status":"ok"' in r.text:
                return True
        except: pass
        return False

sniper = InstagramSniperPro()

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_login = types.InlineKeyboardButton("🔑 دخول (Session ID)", callback_data="login_session")
    btn_add = types.InlineKeyboardButton("➕ إضافة يوزر", callback_data="add")
    btn_list = types.InlineKeyboardButton("📋 القائمة", callback_data="list")
    btn_run = types.InlineKeyboardButton("🚀 بدء الصيد", callback_data="run")
    btn_stop = types.InlineKeyboardButton("🛑 إيقاف", callback_data="stop")
    btn_status = types.InlineKeyboardButton("📊 الحالة", callback_data="status")
    markup.add(btn_login, btn_add, btn_list, btn_run, btn_stop, btn_status)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    sniper.user_id = message.chat.id
    bot.send_message(message.chat.id, "👋 أهلاً بك! تم تحديث البوت ليعمل بنظام الـ Session ID الأضمن.\n\nاضغط على الزر الأول لتسجيل الدخول:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "login_session":
        msg = bot.send_message(call.message.chat.id, "أرسل كود الـ **Session ID** الخاص بك الآن:")
        bot.register_next_step_handler(msg, process_session_login)
    elif call.data == "add":
        msg = bot.send_message(call.message.chat.id, "أرسل اليوزر الذي تريد صيده (بدون @):")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "list":
        if not sniper.targets:
            bot.answer_callback_query(call.id, "القائمة فارغة!")
        else:
            bot.send_message(call.message.chat.id, "📋 القائمة:\n" + "\n".join([f"@{t}" for t in sniper.targets]))
    elif call.data == "run":
        if not sniper.account_info["username"]:
            bot.answer_callback_query(call.id, "سجل دخول أولاً!")
        elif not sniper.targets:
            bot.answer_callback_query(call.id, "أضف يوزرات!")
        else:
            sniper.is_running = True
            bot.send_message(call.message.chat.id, "🚀 بدأ الصيد...")
            threading.Thread(target=sniper_loop).start()
    elif call.data == "stop":
        sniper.is_running = False
        bot.answer_callback_query(call.id, "تم الإيقاف.")
    elif call.data == "status":
        status = "🟢 يعمل" if sniper.is_running else "🔴 متوقف"
        bot.send_message(call.message.chat.id, f"📊 الحالة: {status}\n👤 الحساب: @{sniper.account_info['username']}\n🔢 المحاولات: {sniper.stats['attempts']}")

def process_session_login(message):
    session_id = message.text.strip()
    bot.send_message(message.chat.id, "⏳ جاري التحقق من الـ Session...")
    if sniper.login_via_session(session_id):
        bot.send_message(message.chat.id, f"✅ تم الدخول بنجاح!\n👤 الحساب: @{sniper.account_info['username']}")
    else:
        bot.send_message(message.chat.id, "❌ الـ Session ID غير صحيح أو منتهي الصلاحية.")

def process_add(message):
    target = message.text.strip().replace("@", "")
    sniper.targets.append(target)
    bot.send_message(message.chat.id, f"✅ تم إضافة @{target}")

def sniper_loop():
    while sniper.is_running:
        for target in sniper.targets:
            if not sniper.is_running: break
            if sniper.claim_username(target):
                bot.send_message(sniper.user_id, f"🎊 مبروك! تم صيد @{target} 🎊")
                sniper.is_running = False
                break
            time.sleep(2)

bot.polling()
