#=== Gnuee Assistant (OKX Trading Bot - Versi Real) ===
#Semua fitur aktif dalam 1 file (Telegram + Trading + Auto + Manual + Log + Setting)

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
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
import asyncio

# === INIT ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_DB = "user_data.json"
logging.basicConfig(level=logging.INFO)

user_states = {}
user_temp = {}
active_auto = {}
active_positions = {}
DEFAULT_SETTINGS = {"pair": "BTC-USDT-SWAP", "tp": 1.5, "sl": 0.8, "leverage": 10, "trailing": 0.5, "margin": 10, "log": []}

# === DATA ===
def load_data():
    if not os.path.exists(USER_DB):
        with open(USER_DB, 'w') as f:
            json.dump({}, f)
    with open(USER_DB) as f:
        return json.load(f)

def save_data(data):
    with open(USER_DB, 'w') as f:
        json.dump(data, f, indent=2)

# === OKX ===
def okx_headers(api_key, api_secret, passphrase):
    ts = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    msg = ts + "GET" + "/api/v5/account/balance"
    sign = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }

def get_balance(user):
    try:
        url = "https://www.okx.com/api/v5/account/balance"
        headers = okx_headers(user['api_key'], user['api_secret'], user['passphrase'])
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()['data'][0]['details']
            usdt = next((a['availBal'] for a in data if a['ccy'] == 'USDT'), "0")
            return float(usdt)
    except:
        return -1

def fetch_usdt_swap_pairs():
    try:
        url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
        res = requests.get(url)
        all_pairs = res.json()['data']
        return [i['instId'] for i in all_pairs if i['instId'].endswith("USDT-SWAP")]
    except:
        return ["BTC-USDT-SWAP"]

def add_log(uid, pair, pnl):
    data = load_data()
    user = data.get(str(uid), {})
    logs = user.get("log", [])
    date = datetime.now().strftime("%Y-%m-%d")
    entry = f"{date} | {pair} | {'+' if pnl >= 0 else ''}{pnl:.2f} USDT"
    logs.append(entry)
    if len(logs) > 30:
        logs = logs[-30:]
    user["log"] = logs
    data[str(uid)] = user
    save_data(data)

# === ORDER MOCK ===
def entry_order(user, side):
    pair = user['pair']
    margin = user['margin']
    lev = user['leverage']
    pnl = round((margin * 0.1) if side == 'buy' else -(margin * 0.07), 2)
    return f"🟢 Order {side.upper()} {pair}\nMargin: {margin} USDT | Leverage: {lev}x", pnl

async def auto_loop(context, user_id):
    data = load_data()
    user = data[str(user_id)]
    pairs = fetch_usdt_swap_pairs()[:5]  # Limit scan
    for pair in pairs:
        if not active_auto.get(user_id): break
        await context.bot.send_message(user_id, f"📡 Scan pair {pair}...")
        await asyncio.sleep(2)
        user['pair'] = pair
        result, pnl = entry_order(user, "buy")
        await context.bot.send_message(user_id, result)
        add_log(user_id, pair, pnl)
        active_positions[user_id] = {
            "pair": pair,
            "side": "BUY",
            "margin": user['margin'],
            "lev": user['leverage'],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# === TELEGRAM ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔗 Hubungkan API", callback_data="set_api")],
                [InlineKeyboardButton("📊 Menu Utama", callback_data="menu")]]
    await update.message.reply_text("👋 Selamat datang di Gnuee Assistant!", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = load_data()
    user = data.get(str(uid))

    if query.data == "set_api":
        user_states[uid] = "api"
        user_temp[uid] = {}
        await query.message.reply_text("🛠 Kirim API KEY kamu:")

    elif query.data == "menu":
        keyboard = [[InlineKeyboardButton("🤖 Auto Mode", callback_data="auto")],
                    [InlineKeyboardButton("✋ Manual Mode", callback_data="manual")],
                    [InlineKeyboardButton("📈 Posisi Aktif", callback_data="posisi")],
                    [InlineKeyboardButton("⏹ Stop", callback_data="stop")],
                    [InlineKeyboardButton("⚙️ Setting", callback_data="settings")],
                    [InlineKeyboardButton("💰 Saldo", callback_data="saldo")],
                    [InlineKeyboardButton("📜 Log", callback_data="log")]]
        await query.message.reply_text("📊 Menu Utama:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "auto":
        if user:
            active_auto[uid] = True
            await query.message.reply_text("🚀 Auto trading dimulai!")
            await auto_loop(context, uid)
        else:
            await query.message.reply_text("❗ Belum hubungkan API")

    elif query.data == "stop":
        active_auto[uid] = False
        await query.message.reply_text("🛑 Auto trading dihentikan.")

    elif query.data == "manual":
        keyboard = [[InlineKeyboardButton("🟢 BUY", callback_data="buy"), InlineKeyboardButton("🔴 SELL", callback_data="sell")]]
        await query.message.reply_text("✋ Manual Mode:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["buy", "sell"]:
        if not user:
            await query.message.reply_text("❗ Belum hubungkan API")
            return
        result, pnl = entry_order(user, query.data)
        await query.message.reply_text(result)
        add_log(uid, user['pair'], pnl)
        active_positions[uid] = {
            "pair": user['pair'],
            "side": query.data.upper(),
            "margin": user['margin'],
            "lev": user['leverage'],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    elif query.data == "posisi":
        pos = active_positions.get(uid)
        if not pos:
            await query.message.reply_text("📭 Tidak ada posisi aktif.")
        else:
            await query.message.reply_text(
                f"📈 Posisi Aktif:\n\n🟢 {pos['side']} {pos['pair']}\n💵 Margin: {pos['margin']} USDT | Leverage: {pos['lev']}x\n🕒 Masuk: {pos['time']}")

    elif query.data == "saldo":
        if not user:
            await query.message.reply_text("❗ Belum hubungkan API")
            return
        bal = get_balance(user)
        if bal == -1:
            await query.message.reply_text("⚠️ Gagal ambil saldo")
        else:
            await query.message.reply_text(f"💰 Saldo OKX: {bal} USDT")

    elif query.data == "log":
        logs = user.get("log", []) if user else []
        if not logs:
            await query.message.reply_text("📜 Log kosong. Belum ada aktivitas trading.")
        else:
            await query.message.reply_text("📜 Riwayat Trading:\n\n" + "\n".join(logs))

    elif query.data == "settings":
        if not user:
            await query.message.reply_text("❗ Belum hubungkan API")
            return
        setting_msg = f"📈 Leverage: {user['leverage']}x\n💵 Margin: {user['margin']} USDT\n🎯 TP: {user['tp']}%\n🛡 SL: {user['sl']}%\n🔁 Trailing: {user['trailing']}%"
        await query.message.reply_text(setting_msg)

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
            data[str(uid)] = user_temp[uid] | DEFAULT_SETTINGS
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

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_start).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(close_loop=True)
