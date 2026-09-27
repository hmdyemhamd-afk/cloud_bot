import asyncio
import os
import re
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.errors import (
    UserAlreadyParticipantError, 
    InviteHashExpiredError, 
    InviteHashInvalidError, 
    InviteRequestSentError
)

# إعداد خادم سياسة التشغيل 24/7
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

# البيانات الأساسية مع وضع التوكن الجديد مباشرة
API_ID = int(os.environ.get("API_ID", "39019894"))
API_HASH = os.environ.get("API_HASH", "8afa7eeb02c1eef8b2f536e00cfd8157")
BOT_TOKEN = "8811537964:AAGyJ-aETFDtLU7JiY3ity7lZo8Xm8cL-gU"

# استخدام اسم جلسة جديد كلياً لمنع تداخل الملفات القديمة
bot = TelegramClient('new_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
client = TelegramClient('new_friend_session', API_ID, API_HASH)

active_tasks = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("📥 إدخال روابط والانضمام إليها", b"join_menu")]
    ]
    await event.respond("أهلاً بك في بوت إدارة مجموعاتك **New_my_group**!\nاختر من الأزرار أدناه:", buttons=buttons)

@bot.on(events.CallbackQuery(data=b"join_menu"))
async def prompt_links(event):
    await event.respond("أرسل الآن رسالة تحتوي على روابط المجموعات التي تريد الانضمام إليها:")
    await event.answer()

@bot.on(events.CallbackQuery(data=b"stop_process"))
async def stop_process(event):
    user_id = event.sender_id
    if user_id in active_tasks:
        active_tasks[user_id] = False
        await event.answer("⚠️ يتم إيقاف العملية الآن...", alert=True)
        await event.edit("❌ **تم إيقاف عملية الانضمام بناءً على رغبتك.**")
    else:
        await event.answer("لا توجد عملية نشطة حالياً.", alert=True)

@bot.on(events.NewMessage(incoming=True))
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
            await event.respond("⚠️ هناك عملية انضمام تعمل حالياً! اضغط على زر الإيقاف أولاً.")
            return

        active_tasks[user_id] = True
        
        stop_buttons = [[Button.inline("🛑 إيقاف العملية", b"stop_process")]]
        await event.respond(f"🔍 تم استخراج {len(links)} رابط. جارٍ المعالجة الصحيحة...", buttons=stop_buttons)
        
        success_count = 0
        fail_count = 0
        
        for index, link in enumerate(links, start=1):
            if not active_tasks.get(user_id, False):
                break
                
            try:
                if '+' in link or 'joinchat' in link:
                    invite_hash = link.split('+')[-1] if '+' in link else link.split('/')[-1]
                    
                    try:
                        invite_info = await client(CheckChatInviteRequest(invite_hash))
                        if getattr(invite_info, 'request_needed', False):
                            try:
                                await client(ImportChatInviteRequest(invite_hash))
                                success_count += 1
                                await event.respond(f"[{index}/{len(links)}] ⏳ تم تقديم طلب الانضمام بنجاح:\n{link}")
                            except InviteRequestSentError:
                                success_count += 1
                                await event.respond(f"[{index}/{len(links)}] ⏳ تم تقديم طلب الانضمام رسمياً:\n{link}")
                        else:
                            await client(ImportChatInviteRequest(invite_hash))
                            success_count += 1
                            await event.respond(f"[{index}/{len(links)}] ✅ تم الانضمام بنجاح:\n{link}")
                    except Exception:
                        try:
                            await client(ImportChatInviteRequest(invite_hash))
                            success_count += 1
                            await event.respond(f"[{index}/{len(links)}] ✅ تم الانضمام بنجاح:\n{link}")
                        except InviteRequestSentError:
                            success_count += 1
                            await event.respond(f"[{index}/{len(links)}] ⏳ تم تقديم طلب الانضمام بنجاح:\n{link}")
                else:
                    channel_username = link.split('/')[-1]
                    try:
                        await client(JoinChannelRequest(channel_username))
                        success_count += 1
                        await event.respond(f"[{index}/{len(links)}] ✅ تم الانضمام بنجاح:\n{link}")
                    except InviteRequestSentError:
                        success_count += 1
                        await event.respond(f"[{index}/{len(links)}] ⏳ تم تقديم طلب الانضمام رسمياً:\n{link}")
            
            except UserAlreadyParticipantError:
                success_count += 1
                await event.respond(f"[{index}/{len(links)}] ℹ️ أنت منضم مسبقاً في هذه المجموعة:\n{link}")
                
            except InviteHashExpiredError:
                fail_count += 1
                await event.respond(f"[{index}/{len(links)}] ❌ فشل: الرابط منتهي الصلاحية\n{link}")
                
            except InviteHashInvalidError:
                fail_count += 1
                await event.respond(f"[{index}/{len(links)}] ❌ فشل: الرابط غير صالح\n{link}")
                
            except Exception as e:
                err_str = str(e).lower()
                if any(k in err_str for k in ["request", "invite_request_sent", "join request", "chat_write_forbidden"]):
                    success_count += 1
                    await event.respond(f"[{index}/{len(links)}] ⏳ تم تقديم طلب الانضمام بنجاح:\n{link}")
                elif "already" in err_str or "participant" in err_str:
                    success_count += 1
                    await event.respond(f"[{index}/{len(links)}] ℹ️ أنت منضم مسبقاً:\n{link}")
                else:
                    fail_count += 1
                    await event.respond(f"[{index}/{len(links)}] ❌ فشل:\n{link}\nالسبب: {str(e)}")
            
            if index < len(links) and active_tasks.get(user_id, False):
                await asyncio.sleep(12)
                
        active_tasks[user_id] = False
        await event.respond(f"🏁 **انتهت العملية!**\n- تم بنجاح / طلبات مقبولة: {success_count}\n- فاشل: {fail_count}")

if __name__ == "__main__":
    keep_alive()
    print("[+] البوت يعمل بكفاءة تامة...")
    with client:
        client.loop.run_until_complete(bot.run_until_disconnected())
