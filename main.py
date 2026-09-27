import os
import asyncio
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button

# إعداد خادم الويب 24/7
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7 successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# بيانات البوت الجديد مباشرة
API_ID = 39019894
API_HASH = "8afa7eeb02c1eef8b2f536e00cfd8157"
BOT_TOKEN = "8811537964:AAGyJ-aETFDtLU7JiY3ity7lZo8Xm8cL-gU"

# تشغيل البوت فقط بدون الحاجة لجلسة مستخدم معلقة
bot = TelegramClient('pure_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("📥 مرحباً بك يا حمدي", b"welcome_btn")]
    ]
    await event.respond("أهلاً بك! تم تشغيل البوت الجديد بنجاح تام وسريع 🚀", buttons=buttons)

@bot.on(events.CallbackQuery(data=b"welcome_btn"))
async def callback_handler(event):
    await event.answer("البوت يعمل بكفاءة عالية!", alert=True)

if __name__ == "__main__":
    keep_alive()
    print("[+] البوت الصرف يعمل الآن بنجاح...")
    bot.run_until_disconnected()
