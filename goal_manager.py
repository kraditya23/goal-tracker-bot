from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from firebase_init import db
from datetime import datetime, date, time, timedelta


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Goal Tracker Bot*! I'm here to help you stay productive and build habits.\n\n"
        "Here's what I can do for you:\n"
        "📌 *Daily Goals*\n"
        "• /addgoal <goal> - Add a goal for today\n"
        "• /removegoal - Remove a pending goal\n"
        "• /markcompleted - Mark a goal as completed\n"
        "• /summary - View today's progress and habit status\n\n"
        "🧠 *Monthly Habit Tracking*\n"
        "• /addhabit <habit> - Start tracking a new habit\n"
        "• /removehabit - Remove a habit\n"
        "• /monthlytrackers - Log your habits for today (Yes/No/Later)\n\n"
        "🕛 Every night at *00:00 IST*, I'll send you a summary of your goals and habit tracking.\n\n"
        "📆 At the end of the month, you'll receive a full *PDF report* of your progress (coming soon!)\n\n"
        "Let's get started — type /addgoal or /addhabit to begin!",
        parse_mode="Markdown"
    )


# === Add Goal ===
async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        goal_text = " ".join(context.args)
        db.collection("users").document(user_id).collection("goals").add({
            "goal": goal_text,
            "status": "pending",
            "created_at": datetime.now()
        })
        await update.message.reply_text(f"✅ Goal added: {goal_text}")
    except Exception as e:
        await update.message.reply_text("⚠️ Usage: /addgoal <goal>")


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
    today = date.today()
    start_dt = datetime.combine(today, time(0, 0))
    end_dt = start_dt + timedelta(days=1)
    today_str = today.isoformat()

    goals_ref = db.collection("users").document(user_id).collection("goals")
    docs = goals_ref.where("created_at", ">=", start_dt).where("created_at", "<", end_dt).stream()

    lines = []
    for doc in docs:
        data = doc.to_dict()
        status_emoji = "✅" if data.get("status") == "completed" else "❌"
        lines.append(f"{data.get('goal')} {status_emoji}")

    header = f"📅 Summary for {today.isoformat()}\n"
    summary = header + ("\n".join(f"{i+1}. {line}" for i, line in enumerate(lines)) if lines else "No goals recorded today.")

    # Fetch habit tracker responses
    habits_ref = db.collection("users").document(user_id).collection("trackers").list_documents()
    tracker_lines = []
    for habit_doc in habits_ref:
        habit_name = habit_doc.id
        entry_ref = habit_doc.collection("entries").document(today_str)
        entry_doc = entry_ref.get()
        if entry_doc.exists:
            response = entry_doc.to_dict().get("response", "N/A").capitalize()
            tracker_lines.append(f"{habit_name}: {response}")
        else:
            tracker_lines.append(f"{habit_name}: ❓ Not answered")

    if tracker_lines:
        summary += "\n\n🧠 Habit Tracker:\n" + "\n".join(tracker_lines)

    return summary


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Handler for /summary — sends today’s goal summary on demand.
    user_id = str(update.effective_user.id)
    text = await get_today_summary_text(user_id)
    await update.message.reply_text(text)

async def monthly_trackers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today_str = date.today().isoformat()

    # Dynamically load user's habits
    habit_docs = db.collection("users").document(user_id).collection("trackers").list_documents()
    user_habits = [doc.id for doc in habit_docs]

    for habit in user_habits:
        doc_ref = db.collection("users").document(user_id)\
                    .collection("trackers").document(habit)\
                    .collection("entries").document(today_str)
        if doc_ref.get().exists:
            continue  # already answered today

        context.user_data["current_tracker_habit"] = habit

        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("Yes"), KeyboardButton("No"), KeyboardButton("Later")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )

        await update.message.reply_text(f"Did you perform the habit: *{habit}* today?",
                                        parse_mode="Markdown",
                                        reply_markup=reply_markup)
        return  # wait for response before moving to next

    await update.message.reply_text("✅ All trackers already recorded for today.")


async def handle_tracker_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    response = update.message.text.strip().lower()
    today_str = date.today().isoformat()

    if "current_tracker_habit" not in context.user_data:
        return

    habit = context.user_data["current_tracker_habit"]

    if response in ["yes", "no"]:
        # store response
        doc_ref = db.collection("users").document(user_id)\
                    .collection("trackers").document(habit)\
                    .collection("entries").document(today_str)
        doc_ref.set({"response": response})
    elif response == "will enter later":
        # do not store — so we ask it again later
        await update.message.reply_text(f"🕒 Skipped for now: {habit}")
    else:
        await update.message.reply_text("⚠️ Invalid response. Please choose from the options.")
        return  # don't continue if response is invalid

    context.user_data.pop("current_tracker_habit")

    # Ask next habit
    await monthly_trackers(update, context)

# === Add Habit ===
async def add_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    habit_text = " ".join(context.args).strip()

    if not habit_text:
        await update.message.reply_text("⚠️ Usage: /addhabit <habit name>")
        return

    db.collection("users").document(user_id)\
        .collection("trackers").document(habit_text).set({})
    
    await update.message.reply_text(f"✅ Habit added: {habit_text}")

# === Remove Habit ===
async def remove_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Get list of habits
    habits = list(db.collection("users").document(user_id).collection("trackers").list_documents())
    if not habits:
        await update.message.reply_text("No habits found.")
        return

    context.user_data["habit_removal_list"] = habits
    habit_names = [doc.id for doc in habits]
    habit_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(habit_names)])
    await update.message.reply_text(f"Select the habit to remove by sending a number:\n{habit_list}")

# === Handle Habit Removal Selection ===
async def handle_habit_removal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if "habit_removal_list" not in context.user_data:
        return

    try:
        index = int(update.message.text.strip()) - 1
        habit_docs = context.user_data["habit_removal_list"]

        if index < 0 or index >= len(habit_docs):
            await update.message.reply_text("⚠️ Invalid selection.")
            return

        habit_doc = habit_docs[index]
        habit_doc.reference.delete()

        await update.message.reply_text(f"🗑️ Removed habit: {habit_doc.id}")
        context.user_data.pop("habit_removal_list")

    except ValueError:
        await update.message.reply_text("⚠️ Please reply with a number.")