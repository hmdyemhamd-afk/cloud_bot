import asyncio
import os
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import UserAlreadyParticipantError, InviteHashExpiredError, InviteHashInvalidError

# إعداد خادم Flask الوهمي لإبقاء السيرفر نشطاً على Render 24/7
app = Flask('')

@app.route('/')
def home():
    return "UserBot is running 24/7 successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

API_ID = int(os.environ.get("API_ID", 39019894))
API_HASH = os.environ.get("API_HASH", "8afa7eeb02c1eef8b2f536e00cfd8157")

# استخدام ملف الجلسة المرفوع my_session.session
client = TelegramClient('my_session', API_ID, API_HASH)

active_tasks = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("🚀 بدء التشغيل والتعليمات", b"start_info"), Button.inline("📥 إدخال روابط والانضمام", b"join_menu")]
    ]
    await event.respond(
        "أهلاً بك في بوت إدارة مجموعاتك **MyGroups السحابي (UserBot)** 🛡️\n\n"
        "هذا البوت يعمل 24/7 بصلاحيات حسابك الشخصي للانضمام الفوري للروابط الخاصة والعامة.\n"
        "اختر أحد الخيارات أدناه للبدء:",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=b"start_info"))
async def start_info(event):
    await event.answer("UserBot يعمل بكامل طاقته السحابية!", alert=True)
    await event.respond(
        "ℹ️ **طريقة الاستخدام:**\n"
        "1. اضغط على زر (إدخال روابط والانضمام).\n"
        "2. أرسل رسالة تحتوي على روابط المجموعات (خاصة أو عامة).\n"
        "3. سيبدأ حسابك بالانضمام تدريجياً وبأمان."
    )

@client.on(events.CallbackQuery(data=b"join_menu"))
async def prompt_links(event):
    await event.respond("📥 **جاهز تماماً!**\nأرسل الآن رسالة نصية تحتوي على روابط المجموعات أو القنوات:")
    await event.answer()

@client.on(events.CallbackQuery(data=b"stop_process"))
async def stop_process(event):
    user_id = event.sender_id
    if user_id in active_tasks:
        active_tasks[user_id] = False
        await event.answer("⚠️ يتم إيقاف العملية الآن...", alert=True)
        await event.edit("❌ **تم إيقاف عملية الانضمام بنجاح.**")
    else:
        await event.answer("لا توجد عملية انضمام نشطة حالياً.", alert=True)

@client.on(events.NewMessage(incoming=True))
async def handle_links(event):
    if event.is_private and not event.raw_text.startswith('/'):
        user_id = event.sender_id
        text = event.raw_text
        
        raw_links = re.findall(r'(?:https?://)?t\.me/(?:\+|joinchat/)?[\w\d_-]+', text)
        links = []
        for rl in raw_links:
            clean_link = ('https://' + rl) if not rl.startswith('http') else rl
            if clean_link not in links:
                links.append(clean_link)
        
        if not links:
            return
            
        if user_id in active_tasks and active_tasks.get(user_id) == True:
            await event.respond("⚠️ هناك عملية انضمام تعمل حالياً!")
            return

        active_tasks[user_id] = True
        stop_buttons = [[Button.inline("🛑 إيقاف العملية", b"stop_process")]]
        await event.respond(f"🔍 تم استخراج **{len(links)}** رابط بنجاح. جارٍ الانضمام...", buttons=stop_buttons)
        
        success_count = 0
        fail_count = 0
        
        for index, link in enumerate(links, start=1):
            if not active_tasks.get(user_id, False):
                break
                
            try:
                if '+' in link or 'joinchat' in link:
                    invite_hash = link.split('+')[-1] if '+' in link else link.split('/')[-1]
                    await client(ImportChatInviteRequest(invite_hash))
                else:
                    channel_username = link.split('/')[-1]
                    await client(JoinChannelRequest(channel_username))
                    
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
                if "A request to join" in error_msg or "INVITE_REQUEST_SENT" in error_msg:
                    success_count += 1
                    await event.respond(f"[{index}/{len(links)}] ⏳ طلب معلق بالموافقة:\n{link}")
                else:
                    fail_count += 1
                    await event.respond(f"[{index}/{len(links)}] ❌ فشل: {link}")
            
            if index < len(links) and active_tasks.get(user_id, False):
                await asyncio.sleep(12)
                
        active_tasks[user_id] = False
        await event.respond(f"🏁 **انتهت العملية!**\n▫️ نجاح/معلق: `{success_count}`\n▫️ فاشل: `{fail_count}`")

if __name__ == "__main__":
    keep_alive()
    print("[+] UserBot السحابي يعمل الآن...")
    client.start()
    client.run_until_disconnected()
