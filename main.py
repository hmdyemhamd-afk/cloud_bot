
import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# إعداد خادم الويب 24/7 على Render
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

# توكن البوت الجديد حصرياً
BOT_TOKEN = "8811537964:AAGyJ-aETFDtLU7JiY3ity7lZo8Xm8cL-gU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 إدخال روابط والانضمام إليها", callback_data="join_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "أهلاً بك في بوت إدارة مجموعاتك (New_my_group)!\nاختر من الأزرار أدناه للبدء:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "join_menu":
        await query.edit_message_text(text="أرسل الآن رسالة تحتوي على روابط المجموعات أو القنوات التي تريد التعامل معها:")

def main():
    # بناء تطبيق البوت
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("[+] البوت يعمل الآن بكفاءة تامة وبدون أي أخطاء...")
    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()
