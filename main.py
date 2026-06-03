import json
import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "8812103720:AAFgQvhz5WQOEiLRi7n2G3N0iKAAAGudEZg" # حطي التوكن تبعك هون
FILE_PATH = "todays_users.json"
TIMEZONE = timezone("Asia/Riyadh") # توقيت دمشق ومكة

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# سيرفر وهمي لتأمين استقرار السيرفر على Railway
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), WebServer).serve_forever()

def load_users():
    if not os.path.exists(FILE_PATH): return []
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_users(users):
    with open(FILE_PATH, "w", encoding="utf-8") as f: json.dump(users, f, ensure_ascii=False, indent=4)

async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user: return
    user = update.message.from_user
    display_name = user.first_name
    if user.username: display_name += f" (@{user.username})"
    users = load_users()
    if display_name not in users:
        users.append(display_name)
        save_users(users)

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users:
        await update.message.reply_text("القائمة فارغة حالياً.")
        return
    response = "📋 **الأشخاص الذين أرسلوا اليوم:**\n\n" + "\n".join(f"- {user}" for user in users)
    await update.message.reply_text(response, parse_mode="Markdown")

def reset_daily_list():
    save_users([])
    print("تم تصفير القائمة اليومية تلقائياً.")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    application = Application.builder().token(TOKEN).build()
    
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(reset_daily_list, 'cron', hour=6, minute=0)
    scheduler.start()

    application.add_handler(CommandHandler("list", show_list))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_user))
    
    print("Bot is starting on Railway...")
    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
