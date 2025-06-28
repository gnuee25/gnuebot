# gnuebot

# 🚀 Gnuee Assistant - OKX Futures Trading Bot (Real Version)

Bot Telegram untuk trading **OKX Futures** secara otomatis maupun manual.  
Dibuat untuk real use-case dengan kontrol penuh via Telegram.

---

## ✨ Fitur Utama

- 🤖 **Auto Trading**: Scan market dan entry otomatis
- ✋ **Manual Mode**: Buy/Sell langsung dari Telegram
- ⚙️ **Setting fleksibel**: Leverage, Margin, TP, SL
- 🔐 **Multi-user**: Setiap user bisa input API masing-masing
- 🧼 **Keamanan API**: Pesan API otomatis terhapus
- 💰 **Realtime Balance**: Cek saldo OKX Futures langsung dari bot

---

## 📁 Struktur File

```bash
okx-multibot/
├── main.py            # File utama bot Telegram
├── .env               # Token bot Telegram
├── user_data.json     # Data API dan setting masing-masing user
```
#⚙️ Cara Instalasi

1. Update dan Install Dependensi
```bash
sudo apt update && sudo apt install python3-pip -y
pip install python-telegram-bot requests python-dotenv
```
2. Buat File .env
```bash
nano .env
```
Isi seperti berikut:
```bash
BOT_TOKEN=isi_token_bot_telegram_kamu
```
3. Jalankan Bot
```bash
python3 main.py
```

---

🤖 Menu Bot Telegram

Tombol	Fungsi

🔗 Hubungkan API	Input API Key OKX (key, secret, passphrase)
🤖 Auto Mode	Jalankan trading otomatis
✋ Manual Mode	Buy/Sell langsung via tombol
⏹ Stop	Hentikan auto trading
⚙️ Setting	(Segera) Atur TP/SL/Leverage/Margin
💰 Saldo	Tampilkan saldo akun OKX
📜 Log	Riwayat trade singkat



---

🛡 Keamanan

Setiap user input API sendiri (multi-user)

Pesan API langsung dihapus (tidak bocor)

Tidak menyimpan credential sensitif secara terbuka

