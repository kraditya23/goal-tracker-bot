from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from goal_manager import add_goal, remove_goal, mark_goal_completed, handle_user_selection, summary_command
from scheduler import start_apscheduler
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

# Command handlers
app.add_handler(CommandHandler("addGoal", add_goal))
app.add_handler(CommandHandler("removeGoal", remove_goal))
app.add_handler(CommandHandler("markCompleted", mark_goal_completed))
app.add_handler(CommandHandler("summary", summary_command))

# Text replies for goal selection
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_user_selection))

# Schedule the 00:00 daily summary job
start_apscheduler(app.bot)

app.run_polling()