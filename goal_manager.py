from telegram import Update
from telegram.ext import ContextTypes
from firebase_init import db
from datetime import datetime, date, time, timedelta

# === Add Goal ===
async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        time_str, *goal_text = context.args
        goal_text = " ".join(goal_text)
        db.collection("users").document(user_id).collection("goals").add({
            "goal": goal_text,
            "time": time_str,
            "status": "pending",
            "created_at": datetime.now()
        })
        await update.message.reply_text(f"✅ Goal added: {goal_text} at {time_str}")
    except Exception as e:
        await update.message.reply_text("⚠️ Usage: /addgoal <time> <goal>")

# === Remove Goal (Step 1) ===
async def remove_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    goals_ref = db.collection("users").document(user_id).collection("goals")
    goals = list(goals_ref.where("status", "==", "pending").stream())

    if not goals:
        await update.message.reply_text("🎉 No pending goals to remove.")
        return

    db.collection("users").document(user_id).collection("pending_action").document("current").set({
        "action": "remove",
        "goals": [{"id": g.id, **g.to_dict()} for g in goals]
    })

    goal_list = "\n".join([f"{i+1}. {g.to_dict()['goal']}" for i, g in enumerate(goals)])
    await update.message.reply_text(f"Select the goal to remove by sending a number:\n{goal_list}")

# === Mark Completed (Step 1) ===
async def mark_goal_completed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    goals_ref = db.collection("users").document(user_id).collection("goals")
    goals = list(goals_ref.where("status", "==", "pending").stream())

    if not goals:
        await update.message.reply_text("🎉 No pending goals to mark as completed.")
        return

    db.collection("users").document(user_id).collection("pending_action").document("current").set({
        "action": "complete",
        "goals": [{"id": g.id, **g.to_dict()} for g in goals]
    })

    goal_list = "\n".join([f"{i+1}. {g.to_dict()['goal']}" for i, g in enumerate(goals)])
    await update.message.reply_text(f"Select the goal to mark as completed:\n{goal_list}")

# === Handle Selection (Step 2) ===
async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_doc = db.collection("users").document(user_id)
    action_doc = user_doc.collection("pending_action").document("current").get()

    if not action_doc.exists:
        return

    data = action_doc.to_dict()
    try:
        index = int(update.message.text.strip()) - 1
        goals = data.get("goals", [])
        if index < 0 or index >= len(goals):
            await update.message.reply_text("⚠️ Invalid selection.")
            return

        selected_goal = goals[index]
        goal_id = selected_goal["id"]
        goal_text = selected_goal["goal"]
        action = data.get("action")

        if action == "remove":
            user_doc.collection("goals").document(goal_id).delete()
            await update.message.reply_text(f"🗑️ Removed goal: {goal_text}")

        elif action == "complete":
            user_doc.collection("goals").document(goal_id).update({"status": "completed"})
            await update.message.reply_text(f"🎯 Marked as completed: {goal_text}")

        user_doc.collection("pending_action").document("current").delete()

    except ValueError:
        await update.message.reply_text("⚠️ Please reply with a number.")

async def get_today_summary_text(user_id: str) -> str:
    # Fetches today’s goals for user_id and returns a formatted summary string.
    today = date.today()
    start_dt = datetime.combine(today, time(0,0))
    end_dt = start_dt + timedelta(days=1)

    goals_ref = db.collection("users").document(user_id).collection("goals")
    docs = goals_ref.where("created_at", ">=", start_dt).where("created_at", "<", end_dt).stream()

    lines = []
    for doc in docs:
        data = doc.to_dict()
        status_emoji = "✅" if data.get("status") == "completed" else "❌"
        lines.append(f"{data.get('goal')} at {data.get('time')} {status_emoji}")

    header = f"📅 Summary for {today.isoformat()}\n"
    if not lines:
        return header + "No goals recorded today."
    return header + "\n".join(f"{i+1}. {line}"
                              for i, line in enumerate(lines))

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Handler for /summary — sends today’s goal summary on demand.
    user_id = str(update.effective_user.id)
    text = await get_today_summary_text(user_id)
    await update.message.reply_text(text)
