from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters)
from goal_manager import (add_goal, 
                          remove_goal, 
                          mark_goal_completed, 
                          handle_user_selection, 
                          summary_command,
                          start_command,
                          monthly_trackers,
                          handle_tracker_response,
                          add_habit_command,
                          remove_habit_command,
                          handle_habit_removal_selection
                          )
from scheduler import start_apscheduler
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

## Main function to initialize and start the Telegram bot, set up command and message handlers, and start the scheduler.
async def start_bot():
    # Build the Telegram bot application with the provided token.
    app = ApplicationBuilder().token(TOKEN).build()

    # Register command handlers for various bot commands.
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("addgoal", add_goal))
    app.add_handler(CommandHandler("removegoal", remove_goal))
    app.add_handler(CommandHandler("markcompleted", mark_goal_completed))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("monthlytrackers", monthly_trackers))
    app.add_handler(MessageHandler(filters.Regex("^(Yes|No|Will Enter Later)$"), handle_tracker_response))

    # Text replies for goal selection
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_user_selection))
    
    app.add_handler(CommandHandler("addhabit", add_habit_command))
    app.add_handler(CommandHandler("removehabit", remove_habit_command))
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$"), handle_habit_removal_selection))

    # Start the scheduler after the app's event loop is running
    async def on_startup(application):
        start_apscheduler(application.bot)

    # Instead of run_polling (which closes the loop), use individual startup pieces
    await app.initialize()
    await on_startup(app)
    await app.start()
    await app.updater.start_polling()

    # Keep it alive until manually stopped
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        pass