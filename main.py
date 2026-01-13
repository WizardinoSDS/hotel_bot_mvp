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

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_CHAT_ID")

logging.basicConfig(level=logging.INFO)
db_sheets = SheetsService()

# States
GET_ROOM, GET_STATUS = range(2)
GET_ISSUE = 2
GET_TASK = 3

ROLES = {}

def check_admin(update):
    uid = str(update.effective_chat.id)
    return ROLES.get(uid) == 'admin' or uid == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    user = update.effective_user
    if not ROLES: ROLES[uid] = 'admin'
    
    current_role = ROLES.get(uid, 'staff')
    msg = f"HotelFlow System - Welcome {user.first_name}!\nRole: {current_role.upper()}\n\n"
    
    if current_role == 'admin':
        msg += "Commands:\n/admin - Control Panel\n/setrole - Manage Staff"
    else:
        msg += "Commands:\n/clean - Cleaning Progress\n/issue - Maintenance\n/tasks - Daily List"
        
    await update.message.reply_text(msg)

async def cmd_clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Which room number?")
    return GET_ROOM

async def handle_room_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['active_room'] = update.message.text
    btns = [['Clean', 'In Progress', 'Dirty']]
    await update.message.reply_text(
        f"Status for {context.user_data['active_room']}?",
        reply_markup=ReplyKeyboardMarkup(btns, one_time_keyboard=True)
    )
    return GET_STATUS

async def save_cleaning_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stat = update.message.text
    room = context.user_data['active_room']
    worker = update.effective_user.full_name
    db_sheets.log_cleaning(worker, room, stat)
    
    await update.message.reply_text(f"Done. Room {room} is now {stat}.", reply_markup=ReplyKeyboardRemove())
    if ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"HOTEL UPDATE\nStaff: {worker}\nRoom: {room}\nStatus: {stat}")
        except: pass
    return ConversationHandler.END

async def cmd_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Describe the problem:")
    return GET_ISSUE

async def save_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    problem = update.message.text
    worker = update.effective_user.full_name
    db_sheets.log_maintenance(worker, problem)
    await update.message.reply_text("Maintenance reported. Admin notified.")
    if ADMIN_ID:
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️MAINTENANCE\nFrom: {worker}\nIssue: {problem}")
        except: pass
    return ConversationHandler.END

async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btns = [['Morning Audit', 'Laundry Check', 'Breakfast Prep']]
    await update.message.reply_text("Task to confirm:", reply_markup=ReplyKeyboardMarkup(btns, one_time_keyboard=True))
    return GET_TASK

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t_name = update.message.text
    worker = update.effective_user.full_name
    db_sheets.log_task(worker, t_name)
    await update.message.reply_text(f"Task '{t_name}' saved.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_admin(update):
        await update.message.reply_text("Restricted area.")
        return
    menu = [[InlineKeyboardButton("Today's Summary", callback_data='view_reports')], [InlineKeyboardButton("Reset Tasks", callback_data='reset_tasks')]]
    await update.message.reply_text("--- ADMIN DASHBOARD ---", reply_markup=InlineKeyboardMarkup(menu))

async def handle_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'view_reports':
        data = db_sheets.get_today_reports()
        if not data: await query.edit_message_text("No data for today.")
        else:
            txt = "REPORTS:\n"
            for r in data: txt += f"- Room {r['Room']}: {r['Status']}\n"
            await query.edit_message_text(txt)

async def stop_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', admin_panel))
    
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('clean', cmd_clean)],
        states={GET_ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_room_input)], GET_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_cleaning_data)]},
        fallbacks=[CommandHandler('cancel', stop_action)]
    ))
    
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('issue', cmd_issue)],
        states={GET_ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_issue)]},
        fallbacks=[CommandHandler('cancel', stop_action)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('tasks', cmd_tasks)],
        states={GET_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)]},
        fallbacks=[CommandHandler('cancel', stop_action)]
    ))

    app.add_handler(CallbackQueryHandler(handle_clicks))
    
    print("Bot is up...")
    app.run_polling()
