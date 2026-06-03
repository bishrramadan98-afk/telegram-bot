import os
import logging
import sqlite3
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8812103720:AAGvFnh8pXjJyVLPFvJQk5yQWxCHkbot_pI
"
ADMIN_ID = -1003852568635 # ضع آيدي الجروب الخاص بك هنا (مع علامة السالب)

# ---- خادم ويب وهمي لإرضاء Hugging Face ----
app = Flask('')
@app.route('/')
def home():
    return "Bot is Running successfully!"

def run_flask():
    # منفذ 7860 هو المنفذ الافتراضي الذي يبحث عنه Hugging Face
    app.run(host='0.0.0.0', port=7860)

def init_db():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

async def reset_daily_list(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM daily_users')
    conn.commit()
    conn.close()
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text="🔄 تم إعادة ضبط قائمة الأسماء اليومية بنجاح (الساعة الآن 6:00 AM).")
    except Exception as e:
        print(f"Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    full_name = user.full_name 

    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO daily_users (user_id, full_name) VALUES (?, ?)', (user_id, full_name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass 
    finally:
        conn.close()

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return 

    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name FROM daily_users')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📋 القائمة فارغة حالياً.")
        return

    text = f"📋 **قائمة المسجلين اليوم:**\n\n"
    for index, row in enumerate(rows, start=1):
        text += f"{index}. {row[0]}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    init_db()
    
    # تشغيل خادم الويب في خلفية مستقلة لكي لا يعترض الموقع
    Thread(target=run_flask).start()

    application = Application.builder().token(TOKEN).build()

    scheduler = AsyncIOScheduler(timezone="Asia/Damascus")
    scheduler.add_job(
        reset_daily_list,
        CronTrigger(hour=6, minute=0),
        args=[application.job_queue]
    )
    scheduler.start()

    application.add_handler(CommandHandler("list", show_list))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
