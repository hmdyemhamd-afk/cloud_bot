import asyncio
import os
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import UserAlreadyParticipantError, InviteHashExpiredError, InviteHashInvalidError

# --- إعداد خادم Flask الوهمي لإبقاء البوت نشطاً على Render ---
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
# -------------------------------------------------------------

# قراءة بيانات الاتصال وأمان البيئة السحابية
API_ID = int(os.environ.get("API_ID", 39019894))
API_HASH = os.environ.get("API_HASH", "8afa7eeb02c1eef8b2f536e00cfd8157")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8835766089:AAHQ9mxL1j6C3cGMejcbUVWstS_aiQfUirY")

# إطلاق البوت الرسمي باستخدام التوكن حصراً (يعمل فوراً بدون جلسة أو رقم هاتف)
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# متجر لتخزين حالات المهام وزر الإيقاف
active_tasks = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("🚀 بدء التشغيل والتعليمات", b"start_info"), Button.inline("📥 إدخال روابط والانضمام", b"join_menu")]
    ]
    await event.respond(
        "أهلاً بك في بوت إدارة مجموعاتك **MyGroups السحابي** 🛡️\n\n"
        "هذا البوت يعمل 24/7 على السيرفر ومخصص لإدارة وانضمام المجموعات بكفاءة.\n"
        "اختر أحد الخيارات أدناه للبدء:",
        buttons=buttons
    )

@bot.on(events.CallbackQuery(data=b"start_info"))
async def start_info(event):
    await event.answer("البوت يعمل بكامل طاقته السحابية!", alert=True)
    await event.respond(
        "ℹ️ **طريقة الاستخدام:**\n"
        "1. اضغط على زر (إدخال روابط والانضمام).\n"
        "2. أرسل رسالة تحتوي على روابط المجموعات (معاً أو متفرقة).\n"
        "3. سيبدأ البوت بالانضمام تدريجياً مع فاصل أمان.\n"
        "4. يمكنك إيقاف العملية في أي وقت عبر زر الإيقاف."
    )

@bot.on(events.CallbackQuery(data=b"join_menu"))
async def prompt_links(event):
    await event.respond("📥 **جاهز تماماً!**\nأرسل الآن رسالة نصية تحتوي على روابط المجموعات أو القنوات التي تريد الانضمام إليها:")
    await event.answer()

@bot.on(events.CallbackQuery(data=b"stop_process"))
async def stop_process(event):
    user_id = event.sender_id
    if user_id in active_tasks:
        active_tasks[user_id] = False  # إيقاف العملية فوراً
        await event.answer("⚠️ يتم إيقاف العملية الآن...", alert=True)
        await event.edit("❌ **تم إيقاف عملية الانضمام بنجاح بناءً على رغبتك.**")
    else:
        await event.answer("لا توجد عملية انضمام نشطة حالياً.", alert=True)

@bot.on(events.NewMessage(incoming=True))
async def handle_links(event):
    if event.is_private and not event.raw_text.startswith('/'):
        user_id = event.sender_id
        text = event.raw_text
        
        # استخراج وتنقية الروابط بدقة عالية
        raw_links = re.findall(r'(?:https?://)?t\.me/(?:\+|joinchat/)?[\w\d_-]+', text)
        links = []
        for rl in raw_links:
            clean_link = ('https://' + rl) if not rl.startswith('http') else rl
            if clean_link not in links:
                links.append(clean_link)
        
        if not links:
            return  # تجاهل الرسائل العادية التي لا تحتوي على روابط
            
        if user_id in active_tasks and active_tasks.get(user_id) == True:
            await event.respond("⚠️ هناك عملية انضمام تعمل حالياً! اضغط على زر 🛑 إيقاف العملية أولاً إن أردت بدء عملية جديدة.")
            return

        # تفعيل حالة العمل وإظهار زر الإيقاف الفوري
        active_tasks[user_id] = True
        
        stop_buttons = [[Button.inline("🛑 إيقاف العملية", b"stop_process")]]
        await event.respond(f"🔍 تم استخراج **{len(links)}** رابط بنجاح. جارٍ بدء العمليات...", buttons=stop_buttons)
        
        success_count = 0
        fail_count = 0
        
        for index, link in enumerate(links, start=1):
            if not active_tasks.get(user_id, False):
                break
                
            try:
                if '+' in link or 'joinchat' in link:
                    invite_hash = link.split('+')[-1] if '+' in link else link.split('/')[-1]
                    await bot(ImportChatInviteRequest(invite_hash))
                else:
                    channel_username = link.split('/')[-1]
                    await bot(JoinChannelRequest(channel_username))
                    
                success_count += 1
                await event.respond(f"[{index}/{len(links)}] ✅ تم الانضمام:\n{link}")
            
            except UserAlreadyParticipantError:
                success_count += 1
                await event.respond(f"[{index}/{len(links)}] ℹ️ منضم مسبقاً:\n{link}")
                
            except (InviteHashExpiredError, InviteHashInvalidError):
                fail_count += 1
                await event.respond(f"[{index}/{len(links)}] ❌ فشل (رابط منتهي أو غير صالح):\n{link}")
                
            except Exception as e:
                error_msg = str(e)
                if "A request to join" in error_msg or "successfully requested" in error_msg or "INVITE_REQUEST_SENT" in error_msg:
                    success_count += 1
                    await event.respond(f"[{index}/{len(links)}] ⏳ طلب معلق (بانتظار موافقة المشرفين):\n{link}")
                else:
                    fail_count += 1
                    await event.respond(f"[{index}/{len(links)}] ❌ فشل: {link}")
            
            if index < len(links) and active_tasks.get(user_id, False):
                await asyncio.sleep(12)
                
        active_tasks[user_id] = False
        await event.respond(
            f"🏁 **انتهت العملية بنجاح!**\n\n"
            f"▫️ مجموعات ناجحة / طلبات معلقة: `{success_count}`\n"
            f"▫️ روابط فاشلة: `{fail_count}`"
        )

if __name__ == "__main__":
    # تشغيل خادم الويب للحفاظ على نشاط السيرفر
    keep_alive()
    print("[+] البوت الرسمي السحابي يعمل الآن بكامل طاقته...")
    bot.run_until_disconnected()
