import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
)
from sheets_service import SheetsService

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Initialize Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Sheets Service
sheets = SheetsService()

# Conversation States
CLEANING_ROOM, CLEANING_STATUS = range(2)
MAINTENANCE_DESC = range(2, 3)
TASK_CONFIRM = range(3, 4)

# Simple Role Storage (In-memory for MVP, can be moved to Sheets/DB later)
# In a real scenario, you'd populate this from a config or database
USER_ROLES = {
    # 'CHAT_ID': 'admin' or 'staff'
}

def is_admin(update: Update):
    chat_id = str(update.effective_chat.id)
    return USER_ROLES.get(chat_id) == 'admin' or chat_id == ADMIN_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    
    # Auto-assign first user as admin if ADMIN_CHAT_ID is not set, or if it matches
    if not USER_ROLES:
        USER_ROLES[chat_id] = 'admin'
    
    role = USER_ROLES.get(chat_id, 'staff')
    
    welcome_text = (
        f"Welcome to HotelFlow, {user.first_name}!\n"
        f"Your current role: **{role.upper()}**\n\n"
    )
    
    if role == 'admin':
        welcome_text += "Admin Commands:\n/admin - Admin Dashboard\n/setrole - Change user roles"
    else:
        welcome_text += "Staff Commands:\n/clean - Report Cleaning\n/issue - Report Maintenance\n/tasks - Daily Tasks"
        
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# --- Housekeeping / Cleaning ---
async def start_cleaning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter the Room Number:")
    return CLEANING_ROOM

async def get_cleaning_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['room'] = update.message.text
    reply_keyboard = [['Clean', 'In Progress', 'Dirty']]
    await update.message.reply_text(
        f"Status for Room {context.user_data['room']}?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CLEANING_STATUS

async def finish_cleaning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = update.message.text
    room = context.user_data['room']
    user_name = update.effective_user.full_name
    
    sheets.log_cleaning(user_name, room, status)
    
    await update.message.reply_text(f"✅ Room {room} updated to {status}.", reply_markup=ReplyKeyboardRemove())
    
    # Alert Admin
    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🔔 *Cleaning Alert*\nStaff: {user_name}\nRoom: {room}\nStatus: {status}",
            parse_mode='Markdown'
        )
    return ConversationHandler.END

# --- Maintenance ---
async def start_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please describe the maintenance issue:")
    return MAINTENANCE_DESC

async def finish_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text
    user_name = update.effective_user.full_name
    
    sheets.log_maintenance(user_name, desc)
    
    await update.message.reply_text("✅ Maintenance issue filed and Admin notified.")
    
    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"⚠️ *Maintenance Issue*\nStaff: {user_name}\nIssue: {desc}",
            parse_mode='Markdown'
        )
    return ConversationHandler.END

# --- Admin Dashboard ---
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 Access Denied.")
        return

    keyboard = [
        [InlineKeyboardButton("View Today's Reports", callback_data='view_reports')],
        [InlineKeyboardButton("Reset Task List", callback_data='reset_tasks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 *Admin Control Panel*", reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'view_reports':
        reports = sheets.get_today_reports()
        if not reports:
            await query.edit_message_text("No reports for today yet.")
        else:
            msg = "*Today's Cleaning Reports:*
"
            for r in reports:
                msg += f"- Room {r['Room']}: {r['Status']} ({r['Staff']})\n"
            await query.edit_message_text(msg, parse_mode='Markdown')
            
    elif query.data == 'reset_tasks':
        await query.edit_message_text("Task list reset functionality would go here (Google Sheets cleared).")

# --- Daily Tasks ---
async def start_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['Morning Audit', 'Laundry Check', 'Breakfast Prep']]
    await update.message.reply_text(
        "Select the task you completed:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return TASK_CONFIRM

async def finish_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_name = update.message.text
    user_name = update.effective_user.full_name
    
    sheets.log_task(user_name, task_name)
    
    await update.message.reply_text(f"✅ Task '{task_name}' logged.", reply_markup=ReplyKeyboardRemove())
    
    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"📋 *Task Completed*\nStaff: {user_name}\nTask: {task_name}",
            parse_mode='Markdown'
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Action cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Conversation Handlers
    cleaning_handler = ConversationHandler(
        entry_points=[CommandHandler('clean', start_cleaning)],
        states={
            CLEANING_ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cleaning_room)],
            CLEANING_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_cleaning)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    maintenance_handler = ConversationHandler(
        entry_points=[CommandHandler('issue', start_maintenance)],
        states={
            MAINTENANCE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_maintenance)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    tasks_handler = ConversationHandler(
        entry_points=[CommandHandler('tasks', start_tasks)],
        states={
            TASK_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_task)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin_dashboard))
    application.add_handler(cleaning_handler)
    application.add_handler(maintenance_handler)
    application.add_handler(tasks_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    application.run_polling()
