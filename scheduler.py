import asyncio
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from firebase_init import db
from goal_manager import get_today_summary_text
from pytz import timezone

async def _send_daily_summary(bot):
    users = db.collection("users").list_documents()
    today = date.today().isoformat()

    for user_doc in users:
        user_id = user_doc.id

        # 💡 Auto-fill missing habit tracker responses with "no"
        habits_ref = db.collection("users").document(user_id).collection("trackers").list_documents()
        for habit_doc in habits_ref:
            entry_ref = habit_doc.collection("entries").document(today)
            if not entry_ref.get().exists:
                entry_ref.set({"response": "no"})

        try:
            text = await get_today_summary_text(user_id)
            await bot.send_message(chat_id=int(user_id), text=text)
        except Exception:
            continue

def start_apscheduler(bot):
    """
    Starts the APScheduler AsyncIOScheduler and schedules daily summary.
    Must be called after the bot is built (so you can pass bot instance).
    """
    scheduler = AsyncIOScheduler()
    # CronTrigger: every day at 00:00 local time
    trigger = CronTrigger(hour=0, minute=0, timezone=timezone("Asia/Kolkata"))
    # schedule the job
    scheduler.add_job(
        func=lambda: asyncio.create_task(_send_daily_summary(bot)),
        trigger=trigger,
        id="daily_summary_job",
        replace_existing=True,
    )
    scheduler.start()