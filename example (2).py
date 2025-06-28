import os
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Load BOT TOKEN from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "user_data.json"
DEFAULT_SETTINGS = {
    "api_key": None,
    "api_secret": None,
    "passphrase": None,
    "pair": "BTC-USDT",
    "tp": 0,
    "sl": 0,
    "leverage": 10,
    "trailing": False,
    "margin": 50,
    "log": [],
    "trading_mode": None,
    "active_position": False,
}

user_states = {}  # track user current input state ("api", "settings", None)
user_temp = {}    # temporarily hold partial api input data per user


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    user = data.get(str(uid), DEFAULT_SETTINGS.copy())

    user_states.pop(uid, None)
    user_temp.pop(uid, None)

    welcome_text = "👋 Selamat datang di Gnuee Assistant!"
    keyboard = [
        [InlineKeyboardButton("🛠️ Hubungkan API OKX", callback_data="connect_api")],
        [InlineKeyboardButton("📊 Menu Utama", callback_data="main_menu")]
    ]
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = load_data()
    user = data.get(str(uid), DEFAULT_SETTINGS.copy())

    await query.answer()

    if query.data == "connect_api":
        user_states[uid] = "api"
        user_temp[uid] = {}
        await query.message.reply_text("📌 Kirim API KEY kamu:")
    elif query.data == "main_menu":
        if not user["api_key"]:
            await query.message.reply_text("⚠️ Kamu belum menghubungkan API. Silakan hubungkan API dulu.")
            return
        await show_main_menu(query.message, user)
    elif query.data == "auto":
        user["trading_mode"] = "auto"
        data[str(uid)] = user
        save_data(data)
        await query.message.reply_text("🤖 Auto Mode diaktifkan. Bot akan trading secara otomatis.")
    elif query.data == "manual":
        user["trading_mode"] = "manual"
        data[str(uid)] = user
        save_data(data)
        await query.message.reply_text("✋ Manual Mode diaktifkan. Kamu harus memasukkan perintah trading secara manual.")
    elif query.data == "stop":
        user["trading_mode"] = None
        user["active_position"] = False
        data[str(uid)] = user
        save_data(data)
        await query.message.reply_text("⏹ Trading dihentikan.")
    elif query.data == "settings":
        # Bisa diperluas untuk setting lain
        await query.message.reply_text("⚙️ Menu Pengaturan sedang dalam pengembangan.")
    elif query.data == "saldo":
        # Mock saldo OKX (bisa diganti dengan API call real)
        saldo = 42.75
        await query.message.reply_text(f"💰 Saldo OKX kamu: {saldo} USDT")
    elif query.data == "log":
        logs = user.get("log", [])
        if not logs:
            await query.message.reply_text("📜 Belum ada log trading.")
        else:
            last_logs = "\n".join(logs[-10:])
            await query.message.reply_text(f"📜 Log trading terbaru:\n{last_logs}")
    else:
        await query.message.reply_text("❗ Perintah tidak dikenali, silakan gunakan menu yang tersedia.")


async def show_main_menu(message, user):
    keyboard = [
        [InlineKeyboardButton("🤖 Auto Mode", callback_data="auto")],
        [InlineKeyboardButton("✋ Manual Mode", callback_data="manual")],
        [InlineKeyboardButton("📈 Posisi Aktif", callback_data="posisi")],
        [InlineKeyboardButton("⏹ Stop Trading", callback_data="stop")],
        [InlineKeyboardButton("⚙️ Pengaturan", callback_data="settings")],
        [InlineKeyboardButton("💰 Balance", callback_data="saldo")],
        [InlineKeyboardButton("📜 Log History", callback_data="log")]
    ]
    balance_msg = f"💰 Saldo OKX kamu: 42.75 USDT"  # mock saldo, ganti pakai API real jika mau
    await message.reply_text(balance_msg)
    await message.reply_text("📊 Pilih Mode Trading:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text.strip()
    state = user_states.get(uid)

    data = load_data()
    user = data.get(str(uid), DEFAULT_SETTINGS.copy())

    if state == "api":
        temp = user_temp.get(uid, {})
        if "api_key" not in temp:
            temp["api_key"] = txt
            user_temp[uid] = temp
            await update.message.reply_text("📌 Kirim API SECRET kamu:")
        elif "api_secret" not in temp:
            temp["api_secret"] = txt
            user_temp[uid] = temp
            await update.message.reply_text("🔐 Kirim API PASSPHRASE kamu:")
        elif "passphrase" not in temp:
            temp["passphrase"] = txt
            user.update({
                "api_key": temp["api_key"],
                "api_secret": temp["api_secret"],
                "passphrase": temp["passphrase"]
            })
            data[str(uid)] = user
            save_data(data)
            user_states.pop(uid, None)
            user_temp.pop(uid, None)
            await update.message.reply_text("✅ API Key & Passphrase berhasil disimpan!")

            await show_main_menu(update.message, user)
        return

    # Jika bukan sedang input API, bisa buat handler input fitur lain di sini

    await update.message.reply_text("❗ Perintah tidak dikenali, gunakan tombol menu atau /start.")


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot sudah dijalankan.")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
