# scheduler.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from firebase_init import db
from goal_manager import get_today_summary_text

async def _send_daily_summary(bot):
    """Fetches each user’s summary and sends it via bot."""
    users = db.collection("users").list_documents()
    for user_doc in users:
        user_id = user_doc.id
        try:
            text = await get_today_summary_text(user_id)
            await bot.send_message(chat_id=int(user_id), text=text)
        except Exception:
            # user might have blocked the bot or invalid ID
            continue

def start_apscheduler(bot):
    """
    Starts the APScheduler AsyncIOScheduler and schedules daily summary.
    Must be called after the bot is built (so you can pass bot instance).
    """
    scheduler = AsyncIOScheduler()
    # CronTrigger: every day at 00:00 local time
    trigger = CronTrigger(hour=0, minute=0)
    # schedule the job
    scheduler.add_job(
        func=lambda: asyncio.create_task(_send_daily_summary(bot)),
        trigger=trigger,
        id="daily_summary_job",
        replace_existing=True,
    )
    scheduler.start()