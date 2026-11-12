import asyncio
import aiosqlite
import re
from telethon import TelegramClient, events
from telethon.errors import (
    UserAlreadyParticipantError,
    FloodWaitError,
    InviteHashExpiredError,
    InviteHashInvalidError,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

# ============================================================
# ၁။ Configuration (Account ခုနစ်ခုစလုံးအတွက်)
# ============================================================
API_ID_1 = 38856868                              
API_HASH_1 = "c221d599cacd92804e4d3abcdf756086"  
SESSION_1 = "session1"
PHONE_1 = "+959779409453"

API_ID_2 = 38382066
API_HASH_2 = "2405f7c95c3b4219ade9dfe44b14126f"
SESSION_2 = "session2"
PHONE_2 = "+959753434745"  

API_ID_3 = 37768961
API_HASH_3 = "aff7aa655b12d652ab82efce9f727b40"
SESSION_3 = "session3"
PHONE_3 = "+959773212806"  

API_ID_4 = 37963093
API_HASH_4 = "bb4fd1384a8f093f494ac4e9a43509c4"
SESSION_4 = "session4"
PHONE_4 = "+959652319318"  

API_ID_5 = 33616471
API_HASH_5 = "d2f27dc99d707c88e49c8cf4b97f285e"
SESSION_5 = "session5"
PHONE_5 = "+959774676470"

API_ID_6 = 38031634
API_HASH_6 = "67a76ddf77488863acc56d7335d5d1e6"
SESSION_6 = "session6"
PHONE_6 = "+959673538542"

API_ID_7 = 35108444  
API_HASH_7 = "3f76f2d81b10b6badddc9bd138b10e95" 
SESSION_7 = "session7"
PHONE_7 = "+959670652392"  

BOT_TOKEN = "9037455170:AAGJhRwOQZfuxVIlPbkMa6nvUCDlK1mckQI"
OWNER_ID = 8524222225                          

# ============================================================
# ၂။ Global State
# ============================================================
clients = []
bot_client = None
messages_cache = []
ALLOWED_IDS = set()
is_sending = False
delay_time = 1.5  
spam_task = None

AUTH_PASSWORD = "Yuta@21"
AUTH_USERS = set()  
WAITING_PASSWORD = set()  

DB_PATH = "data.db"

# ============================================================
# ၃။ Database
# ============================================================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS permissions (
                user_id INTEGER PRIMARY KEY
            )"""
        )
        await db.commit()

async def reload_caches():
    global messages_cache, ALLOWED_IDS
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, content FROM messages ORDER BY id") as cur:
            rows = await cur.fetchall()
            messages_cache = [{"id": r[0], "content": r[1]} for r in rows]

        async with db.execute("SELECT user_id FROM permissions") as cur:
            rows = await cur.fetchall()
            ALLOWED_IDS = {r[0] for r in rows}

async def db_add_message(content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
        await db.commit()
    await reload_caches()

async def db_del_message(msg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        await db.commit()
    await reload_caches()

async def db_add_permission(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO permissions (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()
    await reload_caches()

async def db_del_permission(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM permissions WHERE user_id = ?", (user_id,))
        await db.commit()
    await reload_caches()

# ============================================================
# ၄။ Permission Check
# ============================================================
def is_allowed(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ALLOWED_IDS

# ============================================================
# ၅။ ခေတ်မီ Join Function
# ============================================================
async def safe_join_chat(client, link):
    if "joinchat" in link or "/+" in link:
        match = re.search(r'(?:\+|joinchat/)([a-zA-Z0-9_-]+)', link)
        if match:
            invite_hash = match.group(1)
            await client(ImportChatInviteRequest(invite_hash))
            return
        else:
            raise ValueError("Private Link ပုံစံ မမှန်ကန်ပါ")
    else:
        if link.startswith("https://t.me/"):
            username = link.replace("https://t.me/", "").strip("/")
        elif link.startswith("@"):
            username = link.replace("@", "")
        else:
            username = link.strip()
        await client(JoinChannelRequest(username))

# ============================================================
# ၆။ Bot Handler
# ============================================================
async def bot_handler(event):
    global is_sending, spam_task, delay_time

    user_id = event.sender_id
    text = (event.raw_text or "").strip()
    
    is_privileged = is_allowed(user_id) or user_id in AUTH_USERS

    # Password စစ်ဆေးခြင်း (DM ထဲမှာပဲ မေးမယ်၊ Group ထဲမှာ လုံးဝ မမေးဘူး)
    if user_id != OWNER_ID and not is_privileged:
        if event.is_group:
            return  
            
        if user_id in WAITING_PASSWORD:
            if text == AUTH_PASSWORD:
                AUTH_USERS.add(user_id)
                WAITING_PASSWORD.remove(user_id)
                await event.reply("✅ **Password မှန်ကန်ပါတယ်။** Bot ကို အသုံးပြုနိုင်ပါပြီ။\n\n👉 /help ရိုက်ပြီး အသုံးပြုနည်း ကြည့်နိုင်ပါတယ်။")
            else:
                # ⭐ စာသား ၃ ကြောင်းကို တစ်ကြောင်းချင်းစီ ခွဲပြီး ပို့ခြင်း
                await event.reply("❌ Password မှားနေတယ် မအေလိုး မှန်အောင်ပြန်ရေးစမ်း")
                await asyncio.sleep(0.5) # စာတွေ အမြန်လွန်းမသွားအောင် ခဏစောင့်
                await event.reply("👉 Bot Owner Account: @v099c")
                await asyncio.sleep(0.5)
                await event.reply("Password လိုချင်ရင် Owner ကို အဖိုးလို့ခေါ်ပြီး သွားတောင်းစမ်း")
            return

        if user_id not in AUTH_USERS:
            WAITING_PASSWORD.add(user_id)
            if event.is_private:
                await event.reply("🔒 **Bot အသုံးပြုရန် Password ထည့်ပါ:**")
            return

    if not is_privileged:
        return

    if not text:
        return

    if is_sending and not is_privileged:
        return

    # ---------- /setmsg ----------
    if text.startswith("/setmsg "):
        content = text.split(" ", 1)[1].strip()
        if not content:
            await event.reply("စာသား ထည့်ပါ")
            return
        await db_add_message(content)
        await event.reply(f"✅ ထည့်ပြီး ({len(messages_cache)} ခု)")

    # ---------- /delmsg ----------
    elif text.startswith("/delmsg "):
        try:
            msg_id = int(text.split(" ", 1)[1].strip())
        except (IndexError, ValueError):
            await event.reply("ID မှန်ကန်စွာ ထည့်ပါ")
            return
        await db_del_message(msg_id)
        await event.reply(f"🗑 ဖျက်ပြီး ({len(messages_cache)} ခု ကျန်)")

    # ---------- /list ----------
    elif text == "/list":
        if not messages_cache:
            await event.reply("စာသား မရှိပါ")
            return
        lines = ["📝 **Messages**\n"]
        for m in messages_cache:
            preview = m["content"][:60]
            lines.append(f"{m['id']}. {preview}")
        await event.reply("\n".join(lines))

    # ---------- /permission ----------
    elif text.startswith("/permission "):
        try:
            uid = int(text.split(" ", 1)[1].strip())
        except (IndexError, ValueError):
            await event.reply("ID မှန်ကန်စွာ ထည့်ပါ")
            return
        await db_add_permission(uid)
        await event.reply(f"✅ {uid} ခွင့်ပြုပြီး")

    # ---------- /removepermission ----------
    elif text.startswith("/removepermission "):
        try:
            uid = int(text.split(" ", 1)[1].strip())
        except (IndexError, ValueError):
            await event.reply("ID မှန်ကန်စွာ ထည့်ပါ")
            return
        await db_del_permission(uid)
        await event.reply(f"🗑 {uid} ဖယ်ပြီး")

    # ---------- /time ----------
    elif text.startswith("/time "):
        try:
            sec = float(text.split(" ", 1)[1].strip())
        except (IndexError, ValueError):
            await event.reply("အချိန် (sec) မှန်ကန်စွာ ထည့်ပါ")
            return
        delay_time = sec
        await event.reply(f"⏱ Delay = {delay_time}s")

    # ---------- /active ----------
    elif text == "/active":
        if not clients:
            await event.reply("Account မရှိပါ")
            return
        lines = ["🟢 **Accounts**\n"]
        for i, c in enumerate(clients, 1):
            try:
                me = await c.get_me()
                lines.append(f"{i}. {me.first_name} (@{me.username or 'N/A'})")
            except Exception as e:
                lines.append(f"{i}. ❌ {e}")
        await event.reply("\n".join(lines))

    # ---------- /status ----------
    elif text == "/status":
        await event.reply(
            f"📊 **Status**\n"
            f"Sending: {is_sending}\n"
            f"Messages: {len(messages_cache)}\n"
            f"Delay: {delay_time}s\n"
            f"Allowed: {len(ALLOWED_IDS)}\n"
            f"Accounts: {len(clients)}"
        )

    # ---------- /help ----------
    elif text in ["/help", "/start"]:
        await event.reply(
            "🤖 **Bot Commands များ**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📝 **/setmsg** `<စာသား>`\n"
            "• နင်းရန် စာသားအသစ် ထည့်ရန်\n"
            "• (HTML Format သုံးလို့ရပါတယ်)\n\n"
            "🗑 **/delmsg** `<id>`\n"
            "• ထည့်ထားသော စာသားကို ဖျက်ရန်\n\n"
            "📋 **/list**\n"
            "• ထည့်ထားသော စာသားများ ကြည့်ရန်\n\n"
            "🔑 **/permission** `<id>`\n"
            "• သူငယ်ချင်းများကို ခွင့်ပြုရန်\n\n"
            "🚫 **/removepermission** `<id>`\n"
            "• ခွင့်ပြုချက် ပြန်ဖယ်ရန်\n\n"
            "⏱ **/time** `<sec>`\n"
            "• စာပို့မည့် အချိန်ခြားရန် (ဥပမာ- /time 1)\n\n"
            "👥 **/active**\n"
            "• အသုံးပြုနေသော အကောင့်များ ကြည့်ရန်\n\n"
            "📊 **/status**\n"
            "• Bot ၏ အခြေအနေ ကြည့်ရန်\n\n"
            "🔗 **/join** `<link>`\n"
            "• Group သို့ အကောင့်အားလုံး ဝင်ရန်\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔥 **ဖိုက် / တိုက် / နင်း / သတ် / ဖြုတ်** (reply ဖြင့်)\n"
            "• စတင် နင်းရန်\n\n"
            "🛑 **ရပ်**\n"
            "• နင်းနေခြင်းကို ရပ်ရန်\n\n"
            "🧹 **မထန်နဲ့**\n"
            "• စာသားအားလုံး ရှင်းရန်"
        )

    # ---------- /join ----------
    elif text.startswith("/join "):
        link = text.split(" ", 1)[1].strip()
        await event.reply("⏳ ဝင်နေတယ်...")

        results = []

        if bot_client and bot_client.is_connected():
            try:
                await safe_join_chat(bot_client, link)
                results.append("✅ Bot OK")
            except UserAlreadyParticipantError:
                results.append("ℹ️ Bot ရှိပြီးသား")
            except Exception as e:
                results.append(f"❌ Bot: {e}")
        else:
            results.append("❌ Bot မချိတ်ထား")

        for i, client in enumerate(clients, 1):
            try:
                await safe_join_chat(client, link)
                results.append(f"✅ Acc{i} OK")
            except UserAlreadyParticipantError:
                results.append(f"ℹ️ Acc{i} ရှိပြီးသား")
            except FloodWaitError as e:
                results.append(f"⏳ Acc{i} FloodWait {e.seconds}s")
                await asyncio.sleep(e.seconds)
                try:
                    await safe_join_chat(client, link)
                    results.append(f"✅ Acc{i} OK (retry)")
                except Exception as e2:
                    results.append(f"❌ Acc{i} retry: {e2}")
            except Exception as e:
                results.append(f"❌ Acc{i}: {e}")
            await asyncio.sleep(1.5)

        await event.reply("\n".join(results))

    # ---------- ရပ် ----------
    elif text == "ရပ်":
        is_sending = False
        if spam_task and not spam_task.done():
            spam_task.cancel()
        await event.reply("ဟုတ်ကဲ့ ဆရာ")

    # ---------- မထန်နဲ့ ----------
    elif text == "မထန်နဲ့":
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM messages")
            await db.commit()
        await reload_caches()
        await event.reply("🗑 Messages အားလုံး ရှင်းပြီး")

    # ---------- fight (တစ်လုံးတည်း စာသားများ) ----------
    elif text in ["ဖိုက်", "တိုက်", "နင်း", "သတ်", "ဖြုတ်"]:
        if not event.is_reply:
            await event.reply("ဘယ်သူ့ကိုလဲ (reply လုပ်ပါ)")
            return
        if not messages_cache:
            await event.reply("အရင် /setmsg နဲ့ စာသား ထည့်ပါ")
            return
        if is_sending:
            await event.reply("ရပ်တာမလား ဆရာ")
            return

        reply_msg = await event.get_reply_message()
        target = reply_msg.sender
        target_name = target.first_name or "သူငယ်ချင်း"

        is_sending = True
        await event.reply(f"🔥 {target_name} ကို နင်းမယ်...")
        spam_task = asyncio.create_task(
            start_spamming(event.chat_id, target.id, target_name)
        )


# ============================================================
# ၇။ Spam Loop
# ============================================================
async def start_spamming(chat_id, target_id, target_name):
    global is_sending, messages_cache, delay_time
    idx = 0

    try:
        while is_sending:
            if not messages_cache:
                break

            for client in clients:
                if not is_sending:
                    break

                for _ in range(3):
                    if not is_sending or not messages_cache:
                        break

                    if idx >= len(messages_cache):
                        idx = 0
                    content = messages_cache[idx]["content"]
                    idx += 1

                    try:
                        await client.send_message(
                            chat_id,
                            f"{content} {target_name}",
                            parse_mode='html'
                        )
                        print(f"✅ {content} {target_name}")
                        await asyncio.sleep(delay_time)
                    except FloodWaitError as e:
                        print(f"⏳ FloodWait {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        print(f"❌ {e}")

                await asyncio.sleep(0.1)

            if is_sending:
                await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        print("Spam task cancelled")
    finally:
        is_sending = False


# ============================================================
# ၈။ Main
# ============================================================
async def main():
    global bot_client

    await init_db()
    print("✅ Database ready")

    await reload_caches()
    print(f"Loaded: {len(messages_cache)} msgs, {len(ALLOWED_IDS)} allowed")

    accounts = [
        (SESSION_1, API_ID_1, API_HASH_1, PHONE_1),
        (SESSION_2, API_ID_2, API_HASH_2, PHONE_2),
        (SESSION_3, API_ID_3, API_HASH_3, PHONE_3),
        (SESSION_4, API_ID_4, API_HASH_4, PHONE_4),
        (SESSION_5, API_ID_5, API_HASH_5, PHONE_5),
        (SESSION_6, API_ID_6, API_HASH_6, PHONE_6),
        (SESSION_7, API_ID_7, API_HASH_7, PHONE_7)
    ]

    for session, api_id, api_hash, phone in accounts:
        try:
            client = TelegramClient(session, api_id, api_hash)
            if phone:
                await client.start(phone=phone)
            else:
                await client.start()
                
            clients.append(client)
            me = await client.get_me()
            print(f"✅ {session} → {me.first_name}")
        except Exception as e:
            print(f"❌ {session} fail: {e}")

    bot_client = TelegramClient("bot_session", API_ID_1, API_HASH_1)
    await bot_client.start(bot_token=BOT_TOKEN)
    bot_client.add_event_handler(
        bot_handler,
        events.NewMessage(incoming=True),
    )
    print("✅ Bot started")

    await bot_client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())