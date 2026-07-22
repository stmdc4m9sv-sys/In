import telebot
from telebot import types
import requests
import time
import threading
from flask import Flask

# إعدادات البوت - التوكن الخاص بك
API_TOKEN = '8340668436:AAG1FehM_WdoAvb97goQ_DNiYdTu9fMF2Eo'
bot = telebot.TeleBot(API_TOKEN)

# خادم ويب صغير لإبقاء البوت حياً على Render
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

class InstagramSniperPro:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.instagram.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.instagram.com/",
        }
        self.csrf_token = None
        self.email = ""
        self.name = ""
        self.is_running = False
        self.targets = []
        self.user_id = None
        self.stats = {"attempts": 0}

    def get_csrf_token(self):
        try:
            r = self.session.get(self.base_url + "/data/shared_data/", headers=self.headers, timeout=10)
            self.csrf_token = r.json()["config"]["csrf_token"]
            return self.csrf_token
        except: return None

    def login(self, username, password):
        csrf_token = self.get_csrf_token()
        if not csrf_token: return False
        data = {"enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}", "username": username, "queryParams": {}, "optIntoOneTap": "false"}
        self.headers["X-CSRFToken"] = csrf_token
        try:
            r = self.session.post(self.base_url + "/accounts/login/ajax/", headers=self.headers, data=data, timeout=10)
            if "userId" in r.text:
                for cookie in r.cookies:
                    if cookie.name == "csrftoken":
                        self.csrf_token = cookie.value
                        self.headers["X-CSRFToken"] = self.csrf_token
                return True
            return False
        except: return False

    def get_account_info(self):
        try:
            r = self.session.get(self.base_url + "/accounts/edit/", headers=self.headers, timeout=10)
            self.email = r.text.split('"email":"')[1].split('"')[0]
            self.name = r.text.split('"first_name":"')[1].split('"')[0]
            return True
        except: return False

    def claim_username(self, target_username):
        data = {"username": target_username, "email": self.email, "first_name": self.name}
        try:
            r = self.session.post(self.base_url + "/accounts/edit/", headers=self.headers, data=data, timeout=10)
            self.stats["attempts"] += 1
            if '"status":"ok"' in r.text: return True
        except: pass
        return False

sniper = InstagramSniperPro()

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_login = types.InlineKeyboardButton("🔐 تسجيل الدخول", callback_data="login")
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
    bot.send_message(message.chat.id, "👋 أهلاً بك! البوت يعمل 24/7.\n\nاستخدم الأزرار للتحكم:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "login":
        msg = bot.send_message(call.message.chat.id, "أرسل بيانات الحساب: `username:password`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_login)
    elif call.data == "add":
        msg = bot.send_message(call.message.chat.id, "أرسل اليوزر الذي تريد صيده (بدون @):")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "list":
        if not sniper.targets: bot.answer_callback_query(call.id, "القائمة فارغة!")
        else: bot.send_message(call.message.chat.id, "📋 القائمة:\n" + "\n".join([f"@{t}" for t in sniper.targets]))
    elif call.data == "run":
        if not sniper.targets: bot.answer_callback_query(call.id, "أضف يوزرات أولاً!")
        elif sniper.is_running: bot.answer_callback_query(call.id, "البوت يعمل بالفعل!")
        else:
            sniper.is_running = True
            bot.send_message(call.message.chat.id, "🚀 تم بدء الصيد!")
            threading.Thread(target=sniper_loop).start()
    elif call.data == "stop":
        sniper.is_running = False
        bot.answer_callback_query(call.id, "تم الإيقاف.")
    elif call.data == "status":
        status = "🟢 يعمل" if sniper.is_running else "🔴 متوقف"
        bot.send_message(call.message.chat.id, f"📊 الحالة: {status}\n🔢 المحاولات: {sniper.stats['attempts']}")

def process_login(message):
    try:
        user, pw = message.text.split(":")
        bot.send_message(message.chat.id, "⏳ جاري التحقق...")
        if sniper.login(user, pw) and sniper.get_account_info():
            bot.send_message(message.chat.id, f"✅ تم تسجيل الدخول: @{user}")
        else: bot.send_message(message.chat.id, "❌ فشل تسجيل الدخول.")
    except: bot.send_message(message.chat.id, "⚠️ استخدم الصيغة `user:pass`")

def process_add(message):
    target = message.text.strip().replace("@", "")
    sniper.targets.append(target)
    bot.send_message(message.chat.id, f"✅ تم إضافة @{target}")

def sniper_loop():
    while sniper.is_running:
        for target in sniper.targets:
            if not sniper.is_running: break
            if sniper.claim_username(target):
                bot.send_message(sniper.user_id, f"🎊 مبروك! تم صيد @{target} بنجاح! 🎊")
                sniper.is_running = False
                break
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.polling()
