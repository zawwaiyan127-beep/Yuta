import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHANNEL_1_USERNAME = "@mango_2_0_0"
CHANNEL_2_USERNAME = "@Srtoomyar_2_0"
CHANNEL_1_LINK     = "https://t.me/mango_2_0_0"
CHANNEL_2_LINK     = "https://t.me/Srtoomyar_2_0"
POTATO_MOD_LINK    = "https://t.me/+hMao8POVXXozNzhl"

BOT_OWNER_USERNAME = "v099c"
MOD_OWNER_USERNAME = "v98c4"

# ========== LOGGING ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

VALID_STATUSES = {"member", "administrator", "creator", "owner"}


# ========== WELCOME TEXT ==========
WELCOME_TEXT = (
    "🎉 <b>မင်္ဂလာပါ Mango🥭 Bot မှ ကြိုဆိုပါတယ်!</b>\n\n"
    "အောက်ပါ ရွေးချယ်စရာများမှ ရွေးချယ်နိုင်ပါသည် 👇"
)


# ========== KEYBOARDS ==========
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Bot Owner", callback_data="show_bot_owner")],
        [InlineKeyboardButton("📥 Mod ဒေါင်းလုပ်", callback_data="download_mod")],
        [InlineKeyboardButton("👑 Mod Owner", callback_data="show_mod_owner")],
    ])


def bot_owner_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"💬 @{BOT_OWNER_USERNAME} ကို ဆက်သွယ်ရန်",
            url=f"https://t.me/{BOT_OWNER_USERNAME}"
        )],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back")],
    ])


def mod_owner_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"💬 @{MOD_OWNER_USERNAME} ကို ဆက်သွယ်ရန်",
            url=f"https://t.me/{MOD_OWNER_USERNAME}"
        )],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back")],
    ])


def join_required_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel 1 Join", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton("📢 Channel 2 Join", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("✅ Join ပြီးပါပြီ (စစ်ဆေးမည်)", callback_data="download_mod")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back")],
    ])


def potato_download_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥔 Potato Mod ဒေါင်းလုပ်", callback_data="potato_download")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back")],
    ])


# ========== HELPERS ==========
async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    ok1 = ok2 = False
    try:
        m1 = await context.bot.get_chat_member(CHANNEL_1_USERNAME, user_id)
        ok1 = m1.status in VALID_STATUSES
    except Exception as e:
        logger.warning(f"Channel 1 check error: {e}")

    try:
        m2 = await context.bot.get_chat_member(CHANNEL_2_USERNAME, user_id)
        ok2 = m2.status in VALID_STATUSES
    except Exception as e:
        logger.warning(f"Channel 2 check error: {e}")

    return ok1, ok2


async def safe_edit(query, text, keyboard, parse_mode="HTML"):
    try:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=parse_mode)
    except Exception:
        try:
            await query.message.reply_text(text, reply_markup=keyboard, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Send failed: {e}")


# ========== HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "back":
        await safe_edit(query, WELCOME_TEXT, main_menu_keyboard())
        return

    if data == "show_bot_owner":
        text = (
            "👤 <b>Bot Owner အချက်အလက်</b>\n\n"
            f"📌 Username: <b>@{BOT_OWNER_USERNAME}</b>\n"
            f"🔗 Link: https://t.me/{BOT_OWNER_USERNAME}\n\n"
            "အောက်ပါ ခလုတ်ကို နှိပ်ပြီး ဆက်သွယ်နိုင်ပါသည် 👇"
        )
        await safe_edit(query, text, bot_owner_keyboard())
        return

    if data == "show_mod_owner":
        text = (
            "👑 <b>Mod Owner အချက်အလက်</b>\n\n"
            f"📌 Username: <b>@{MOD_OWNER_USERNAME}</b>\n"
            f"🔗 Link: https://t.me/{MOD_OWNER_USERNAME}\n\n"
            "အောက်ပါ ခလုတ်ကို နှိပ်ပြီး ဆက်သွယ်နိုင်ပါသည် 👇"
        )
        await safe_edit(query, text, mod_owner_keyboard())
        return

    if data == "download_mod":
        ok1, ok2 = await check_membership(context, user_id)

        if not (ok1 and ok2):
            missing = []
            if not ok1:
                missing.append(f"📢 Channel 1 — {CHANNEL_1_USERNAME}")
            if not ok2:
                missing.append(f"📢 Channel 2 — {CHANNEL_2_USERNAME}")

            text = (
                "❌ <b>ERROR!</b>\n\n"
                "သင်သည် အောက်ပါ Channel များကို မ Join ရသေးပါ 👇\n\n"
                "• " + "\n• ".join(missing) + "\n\n"
                "⚠️ Mod ဒေါင်းလုပ်ရန် <b>Channel ၂ခုလုံး</b> ကို Join ပေးပါ။\n"
                "Join ပြီးပါက ✅ ခလုတ်ကို ပြန်နှိပ်ပါ။"
            )
            await safe_edit(query, text, join_required_keyboard())
            return

        text = (
            "🙏 <b>ကျေးဇူးတင်ပါသည်!</b>\n\n"
            "✅ သင့်အောင်မြင်စွာ Join ပြီးပါပြီ။\n"
            "🥔 <b>Potato Mod</b> အား စတင်ဒေါင်းလို့ရပါပြီ။"
        )
        await safe_edit(query, text, potato_download_keyboard())
        return

    if data == "potato_download":
        text = (
            "🥔 <b>Potato Mod Download</b>\n\n"
            "အောက်ပါ Channel သို့ Join ပြီး Potato Mod အား "
            "စတင်ဒေါင်းလုပ်လို့ရပါပြီ 👇\n\n"
            f"🔗 {POTATO_MOD_LINK}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🥔 Potato Mod Channel Join", url=POTATO_MOD_LINK)],
            [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back")],
        ])
        await query.message.reply_text(text, reply_markup=kb, parse_mode="HTML")
        await query.answer("✅ Link ပေးလိုက်ပါပြီ", show_alert=False)
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if text.startswith("/"):
        return
    await update.message.reply_text(
        WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML"
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


# ========== MAIN ==========
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN မရှိပါ။ Environment Variable ထည့်ပါ။")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    logger.info("🥭 Mango Bot စတင်လည်ပတ်နေပါပြီ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
