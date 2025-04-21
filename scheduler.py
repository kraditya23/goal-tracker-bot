import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from firebase_init import db
from goal_manager import get_detailed_midnight_summary
from pytz import timezone

IST = timezone("Asia/Kolkata")

## Scheduled job: sends daily summary messages to all users.
async def _send_daily_summary(bot):
    users = list(db.collection("users").list_documents())
    # Get today's date in ISO format based on IST timezone.
    today = datetime.now(IST).date().isoformat()
    
    print(f"[⏰ APScheduler] Starting summary job for {today}")
    print(f"[⏰ APScheduler] Found {len(users)} users to notify.")

    for user_doc in users:
        user_id = user_doc.id
        
        print(f"[📤] Sending summary to user: {user_id}")

        # Auto-fill missing habit tracker responses with "no" for habits not yet answered.
        habits_ref = db.collection("users").document(user_id).collection("trackers").list_documents()
        for habit_doc in habits_ref:
            entry_ref = habit_doc.collection("entries").document(today)
            if not entry_ref.get().exists:
                entry_ref.set({"response": "no"})

        try:
            
            text = await get_detailed_midnight_summary(user_id)
            await bot.send_message(chat_id=int(user_id), text=text)
        except Exception:
            print("something's fucked")
            continue

    print("[✅] Summary job completed.")

def start_apscheduler(bot):
    """
    Starts the APScheduler AsyncIOScheduler and schedules daily summary.
    Must be called after the bot is built (so you can pass bot instance).
    """
    scheduler = AsyncIOScheduler()
    # CronTrigger: every day at 00:00 local time
    trigger = CronTrigger(hour=23, minute=59, timezone=IST)
    # schedule the job
    loop = asyncio.get_event_loop()
    scheduler.add_job(
        func=lambda: loop.call_soon_threadsafe(asyncio.create_task, _send_daily_summary(bot)),
        trigger=trigger,
        id="daily_summary_job",
        replace_existing=True,
    )
    scheduler.start()
    print("APScheduler started")