import telebot
from telebot import types
import requests
import time
import threading

# إعدادات البوت - التوكن الخاص بك
API_TOKEN = '8340668436:AAG1FehM_WdoAvb97goQ_DNiYdTu9fMF2Eo'
bot = telebot.TeleBot(API_TOKEN)

class InstagramRadar:
    def __init__(self):
        self.is_running = False
        self.targets = []
        self.user_id = None
        self.stats = {"checks": 0}

    def check_username(self, username):
        """يفحص إذا كان اليوزر متاحاً بدون تسجيل دخول"""
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        try:
            r = requests.get(url, headers=headers, timeout=5)
            self.stats["checks"] += 1
            # إذا أعاد إنستغرام كود 404، فهذا يعني أن اليوزر غالباً متاح أو محذوف
            if r.status_code == 404:
                return True
            return False
        except:
            return False

sniper_radar = InstagramRadar()

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_add = types.InlineKeyboardButton("➕ إضافة يوزر للقنص", callback_data="add")
    btn_list = types.InlineKeyboardButton("📋 قائمة المراقبة", callback_data="list")
    btn_run = types.InlineKeyboardButton("🚀 تشغيل الرادار", callback_data="run")
    btn_stop = types.InlineKeyboardButton("🛑 إيقاف", callback_data="stop")
    btn_status = types.InlineKeyboardButton("📊 حالة الرادار", callback_data="status")
    markup.add(btn_add, btn_list, btn_run, btn_stop, btn_status)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    sniper_radar.user_id = message.chat.id
    welcome_text = (
        "🎯 **مرحباً بك في رادار القنص السحري!**\n\n"
        "هذا البوت سيفحص اليوزرات 24/7. بمجرد توفر اليوزر، سيرسل لك رابطاً "
        "تفتحه من متصفحك لنقل اليوزر فوراً بأمان تامة."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add":
        msg = bot.send_message(call.message.chat.id, "أرسل اليوزر الذي تريد مراقبته:")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "list":
        targets = "\n".join([f"@{t}" for t in sniper_radar.targets]) if sniper_radar.targets else "لا يوجد"
        bot.send_message(call.message.chat.id, f"📋 قائمة المراقبة:\n{targets}")
    elif call.data == "run":
        if not sniper_radar.targets:
            bot.answer_callback_query(call.id, "أضف يوزرات أولاً!")
        else:
            sniper_radar.is_running = True
            bot.send_message(call.message.chat.id, "🚀 الرادار يعمل الآن 24/7...")
            threading.Thread(target=radar_loop).start()
    elif call.data == "stop":
        sniper_radar.is_running = False
        bot.answer_callback_query(call.id, "تم إيقاف الرادار.")
    elif call.data == "status":
        status = "🟢 نشط" if sniper_radar.is_running else "🔴 متوقف"
        bot.send_message(call.message.chat.id, f"📊 الحالة: {status}\n🔢 عدد الفحوصات: {sniper_radar.stats['checks']}")

def process_add(message):
    target = message.text.strip().replace("@", "")
    sniper_radar.targets.append(target)
    bot.send_message(message.chat.id, f"✅ تمت إضافة @{target} للرادار.")

def radar_loop():
    while sniper_radar.is_running:
        for target in sniper_radar.targets:
            if not sniper_radar.is_running: break
            if sniper_radar.check_username(target):
                # الرابط السحري للنقل الفوري
                magic_link = f"https://www.instagram.com/accounts/edit/?username={target}"
                alert_msg = (
                    f"🚨 **عاجل! اليوزر @{target} قد يكون متاحاً الآن!**\n\n"
                    f"اضغط على الرابط أدناه فوراً لنقله:\n"
                    f"[👉 اضغط هنا للنقل الفوري]({magic_link})"
                )
                bot.send_message(sniper_radar.user_id, alert_msg, parse_mode="Markdown")
                # إيقاف مؤقت لليوزر الذي وجدناه لكي لا يكرر التنبيه
                sniper_radar.targets.remove(target)
                if not sniper_radar.targets: sniper_radar.is_running = False
                break
            time.sleep(2) # فحص كل ثانيتين لتجنب الحظر

bot.polling()
