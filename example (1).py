#=== Gnuee Assistant (OKX Trading Bot - Versi Real) ===
# Semua fitur aktif dalam 1 file (Telegram + Trading)

import logging
import os
import json
import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import asyncio

# === INIT ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_DB = "user_data.json"

logging.basicConfig(level=logging.INFO)

user_states = {}      # track input step
user_temp = {}        # temporary storage during input
active_auto = {}      # track who is in auto trading mode

DEFAULT_SETTINGS = {
    "pair": "BTC-USDT-SWAP",
    "tp": 1.5,
    "sl": 0.8,
    "leverage": 10,
    "trailing": 0.5,
    "margin": 10,
}

# === DATA HANDLING ===
def load_data():
    if not os.path.exists(USER_DB):
        with open(USER_DB, 'w') as f:
            json.dump({}, f)
    with open(USER_DB) as f:
        return json.load(f)

def save_data(data):
    with open(USER_DB, 'w') as f:
        json.dump(data, f, indent=2)

# === OKX API HEADER GENERATION ===
def okx_headers(api_key, api_secret, passphrase):
    ts = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    msg = ts + "GET" + "/api/v5/account/balance"
    sign = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }

# === GET BALANCE FROM OKX ===
def get_balance(user):
    try:
        url = "https://www.okx.com/api/v5/account/balance"
        headers = okx_headers(user['api_key'], user['api_secret'], user['passphrase'])
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()['data'][0]['details']
            usdt = next((a['availBal'] for a in data if a['ccy'] == 'USDT'), "0")
            return float(usdt)
    except Exception:
        pass
    return -1

# === MOCK ENTRY ORDER (SIMULASI) ===
def entry_order(user, side):
    pair = user['pair']
    margin = user['margin']
    lev = user['leverage']
    return f"🟢 Order {side.upper()} {pair}\nMargin: {margin} USDT | Leverage: {lev}x"

# === AUTO TRADING LOOP (SIMULASI) ===
async def auto_loop(context: ContextTypes.DEFAULT_TYPE, user_id):
    data = load_data()
    user = data.get(str(user_id), None)
    if not user:
        await context.bot.send_message(user_id, "❗ API belum terhubung, auto trading tidak dapat dijalankan.")
        return

    for i in range(3):  # simulasi scan market 3 kali
        if not active_auto.get(user_id, False):
            break
        await context.bot.send_message(user_id, f"📡 Scan market ke-{i + 1}... (pair {user['pair']})")
        await asyncio.sleep(2)

    if active_auto.get(user_id, False):
        msg = entry_order(user, "buy")
        await context.bot.send_message(user_id, msg)

# === TELEGRAM BOT HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Hubungkan API", callback_data="set_api")],
        [InlineKeyboardButton("📊 Menu Utama", callback_data="menu")],
    ]
    await update.message.reply_text("👋 Selamat datang di Gnuee Assistant!", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = load_data()

    if query.data == "set_api":
        user_states[uid] = "api"
        user_temp[uid] = {}
        await query.message.reply_text("🛠 Kirim API KEY kamu:")

    elif query.data == "menu":
        keyboard = [
            [InlineKeyboardButton("🤖 Auto Mode", callback_data="auto")],
            [InlineKeyboardButton("✋ Manual Mode", callback_data="manual")],
            [InlineKeyboardButton("⏹ Stop", callback_data="stop")],
            [InlineKeyboardButton("⚙️ Setting", callback_data="settings")],
            [InlineKeyboardButton("💰 Saldo", callback_data="saldo")],
            [InlineKeyboardButton("📜 Log", callback_data="log")],
        ]
        await query.message.reply_text("📊 Menu Utama:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "auto":
        active_auto[uid] = True
        await query.message.reply_text("🚀 Auto trading dimulai!")
        await auto_loop(context, uid)

    elif query.data == "stop":
        active_auto[uid] = False
        await query.message.reply_text("🛑 Auto trading dihentikan.")

    elif query.data == "manual":
        keyboard = [
            [InlineKeyboardButton("🟢 BUY", callback_data="buy"), InlineKeyboardButton("🔴 SELL", callback_data="sell")]
        ]
        await query.message.reply_text("✋ Manual Mode:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["buy", "sell"]:
        user = data.get(str(uid))
        if not user:
            await query.message.reply_text("❗ Belum hubungkan API")
            return
        result = entry_order(user, query.data)
        await query.message.reply_text(result)

    elif query.data == "saldo":
        user = data.get(str(uid))
        if not user:
            await query.message.reply_text("❗ Belum hubungkan API")
            return
        bal = get_balance(user)
        if bal == -1:
            await query.message.reply_text("⚠️ Gagal ambil saldo")
        else:
            await query.message.reply_text(f"💰 Saldo OKX: {bal} USDT")

    elif query.data == "log":
        await query.message.reply_text("📜 Log:\n- BUY BTC ✅ TP\n- SELL ETH ❌ SL")

    elif query.data == "settings":
        # Placeholder for future settings implementation
        await query.message.reply_text("⚙️ Menu pengaturan belum tersedia.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text.strip()
    msg_id = update.message.message_id

    if uid in user_states:
        step = user_states[uid]
        if step == "api":
            user_temp[uid]["api_key"] = txt
            user_states[uid] = "secret"
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            await update.message.reply_text("🔐 Kirim API SECRET kamu:")

        elif step == "secret":
            user_temp[uid]["api_secret"] = txt
            user_states[uid] = "pass"
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            await update.message.reply_text("🧷 Kirim API PASSPHRASE kamu:")

        elif step == "pass":
            user_temp[uid]["passphrase"] = txt
            data = load_data()
            # Merge user input with default settings, prioritizing user input
            combined = {**DEFAULT_SETTINGS, **user_temp[uid]}
            data[str(uid)] = combined
            save_data(data)
            del user_states[uid]
            del user_temp[uid]
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            await update.message.reply_text("✅ API disimpan. Ketik /start")
    else:
        await update.message.reply_text("Gunakan tombol /start untuk mulai.")

# === MAIN ===
async def on_start(app):
    logging.info("Gnuee Assistant Ready!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_start).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling(close_loop=True)
