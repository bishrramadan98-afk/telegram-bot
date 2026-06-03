import json
import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

# 1. ضع التوكن الخاص بك هنا بدلاً من الأرقام الوهمية
TOKEN = "8812103720:AAFgQvhz5WQOEiLRi7n2G3N0iKAAAGudEZg" 

FILE_PATH = "todays_users.json"
TIMEZONE = timezone("Asia/Riyadh") # يمكنك تغيير المدينة حسب توقيتك

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

def main():
    # بناء التطبيق وتثبيت الإعدادات
    application = Application.builder().token(TOKEN).build()
    
    # تشغيل المنبه اليومي للساعة 6 صباحاً
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(reset_daily_list, 'cron', hour=6, minute=0)
    scheduler.start()

    # الأوامر والرسائل
    application.add_handler(CommandHandler("list", show_list))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_user))
    
    # بدء الاستماع للرسائل (طريقة متوافقة مع Render)
    print("Bot is starting...")
    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
