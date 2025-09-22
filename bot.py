import os
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from concurrent.futures import ThreadPoolExecutor

# Ambil TOKEN dari Railway Environment Variable
TOKEN = os.getenv("TOKEN")

# Step Conversation
TEMPLATE, WORDS = range(2)

# Command rahasia
SECRET_CMD = "inirahasia"

# Variabel sementara
user_template = {}

# ===== Fungsi cek link =====
def check_link(link):
    try:
        r = requests.head(link, timeout=2)
        return link if r.status_code == 200 else None
    except:
        return None

# ===== START command rahasia =====
def secret(update, context):
    chat_id = update.message.chat_id
    user_template[chat_id] = None
    update.message.reply_text("Silakan masukkan template link (gunakan [word] di bagian yang mau diganti).")
    return TEMPLATE

# ===== STEP 1: Simpan Template =====
def set_template(update, context):
    chat_id = update.message.chat_id
    template = update.message.text.strip()

    if "[word]" not in template:
        update.message.reply_text("Template harus ada [word]. Coba lagi.")
        return TEMPLATE

    user_template[chat_id] = template
    update.message.reply_text("Template disimpan ✅\nSekarang masukkan kata (bisa lebih dari satu, pisahkan dengan koma).")
    return WORDS

# ===== STEP 2: Generate & Cek Link, lalu OFF =====
def set_words(update, context):
    chat_id = update.message.chat_id
    words = [w.strip() for w in update.message.text.split(",")]
    template = user_template[chat_id]

    # Generate link
    generated = [template.replace("[word]", w) for w in words]

    # Cek paralel dengan 50 worker
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(check_link, generated))
    active_links = [link for link in results if link]

    # Kirim hasil
    if active_links:
        response = f"Selamat 🎉 Terdapat {len(active_links)} Link Yang Ditemukan:\n"
        response += "\n".join(active_links)
    else:
        response = "Maaf 😢 Tidak Ada Link Yang Ditemukan."

    update.message.reply_text(response)

    # === Matikan bot setelah selesai ===
    context.bot_data['updater'].stop()
    return ConversationHandler.END

# ===== Cancel =====
def cancel(update, context):
    update.message.reply_text("Dibatalkan ❌")
    context.bot_data['updater'].stop()
    return ConversationHandler.END

# ===== Default response (biar orang lain nggak bisa apa-apa) =====
def default_response(update, context):
    update.message.reply_text("Tidak ada apa apa disini bot ini telah off, silakan blokir bot ini🗿\n\n"
                              "There is nothing here, this bot is already off, please block this bot 🗿")

# ===== Main =====
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Simpan updater supaya bisa dipanggil di handler
    dp.bot_data['updater'] = updater

    # Conversation untuk command rahasia
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(SECRET_CMD, secret)],
        states={
            TEMPLATE: [MessageHandler(Filters.text & ~Filters.command, set_template)],
            WORDS: [MessageHandler(Filters.text & ~Filters.command, set_words)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)

    # Default handler untuk /start dan chat random
    dp.add_handler(CommandHandler("start", default_response))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, default_response))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()