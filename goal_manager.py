from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from firebase_init import db
from datetime import datetime, time, timedelta
from pytz import timezone


IST = timezone("Asia/Kolkata")

## Handler for /start command: sends a welcome message and instructions to the user.
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
## Handler for /addgoal command: adds a new goal to the user's Firestore collection.
async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Combine command arguments to form the goal text.
    goal_text = " ".join(context.args)

    if not goal_text:
        await update.message.reply_text("⚠️ Usage: /addgoal <goal>")
        return
    
    db.collection("users").document(user_id).collection("goals").add({
        "goal": goal_text,
        "status": "pending",
        "created_at": datetime.now(IST)
    })

    await update.message.reply_text(f"✅ Goal added: {goal_text}")


# === Remove Goal (Step 1) ===
## Handler for /removegoal command: lists pending goals for removal.
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
## Handler for /markcompleted command: lists pending goals to be marked as completed.
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
## Processes the user's numeric selection for goal removal or completion.
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


## Generates today's summary text including goals and habit tracker responses.
async def get_today_summary_text(user_id: str) -> str:
    now = datetime.now(IST)
    today = now.date()
    start_dt = datetime.combine(today, time(0, 0, tzinfo=IST))
    end_dt = start_dt + timedelta(days=1)
    today_str = today.isoformat()

    goals_ref = db.collection("users").document(user_id).collection("goals")
    docs = list(goals_ref.where("created_at", ">=", start_dt).where("created_at", "<", end_dt).stream())

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
            status_emoji = "✅" if response == 'Yes' else "❌"
            tracker_lines.append(f"{habit_name}: {status_emoji}")
        else:
            tracker_lines.append(f"{habit_name}: ❓ Not answered")

    if tracker_lines:
        summary += "\n\n🧠 Habit Tracker:\n" + "\n".join(tracker_lines)

    return summary

## Generates a detailed midnight summary including goal completion percentages and habit tracking.
async def get_detailed_midnight_summary(user_id: str) -> str:
    now = datetime.now(IST)
    today = now.date()
    start_dt = datetime.combine(today, time(0, 0, tzinfo=IST))
    end_dt = start_dt + timedelta(days=1)
    today_str = today.isoformat()

    summary_lines = [f"📅 Summary for {today_str}"]

    # === GOALS ===
    goals_ref = db.collection("users").document(user_id).collection("goals")
    goal_docs = list(goals_ref.where("created_at", ">=", start_dt).where("created_at", "<", end_dt).stream())

    if goal_docs:
        completed = [doc for doc in goal_docs if doc.to_dict().get("status") == "completed"]
        pending = [doc for doc in goal_docs if doc.to_dict().get("status") != "completed"]
        total = len(goal_docs)
        percent = (len(completed) / total) * 100 if total else 0

        summary_lines.append("\n🎯 GOALS:")
        summary_lines.append(f"Percentage of goals completed: {percent:.0f}%")

        if completed:
            summary_lines.append("\n✅ Completed:")
            for doc in completed:
                summary_lines.append(f"- {doc.to_dict().get('goal')}")

        if pending:
            summary_lines.append("\n❌ Missed:")
            for doc in pending:
                summary_lines.append(f"- {doc.to_dict().get('goal')}")
    else:
        summary_lines.append("\n🎯 GOALS:\nNo goals set for today.")

    # === HABITS ===
    summary_lines.append("\n🧠 HABITS:")
    habits_ref = list(db.collection("users").document(user_id).collection("trackers").list_documents())

    if habits_ref:
        for habit_doc in habits_ref:
            habit_name = habit_doc.id
            entries_ref = habit_doc.collection("entries").stream()
            yes_count, total_entries = 0, 0
            for entry in entries_ref:
                resp = entry.to_dict().get("response", "").lower()
                if resp:
                    total_entries += 1
                    if resp == "yes":
                        yes_count += 1
            percent = (yes_count / total_entries) * 100 if total_entries else 0
            summary_lines.append(f"- {habit_name}: {percent:.0f}%")
    else:
        summary_lines.append("No habits tracking for this month.")

    return "\n".join(summary_lines)


## Handler for /summary command: sends today's goal and habit summary to the user.
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Handler for /summary — sends today’s goal summary on demand.
    user_id = str(update.effective_user.id)
    text = await get_today_summary_text(user_id)
    await update.message.reply_text(text)

## Handler for /monthlytrackers command: prompts the user to answer daily habit tracking questions.
async def monthly_trackers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today_str = datetime.now(IST).date().isoformat()

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


## Processes the user's response for habit tracking and schedules the next tracker if available.
async def handle_tracker_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    response = update.message.text.strip().lower()
    today_str = datetime.now(IST).date().isoformat()

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
## Handler for /addhabit command: adds a new habit to track in Firestore.
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
## Handler for /removehabit command: lists habits available for removal.
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
## Processes the user's numeric selection to remove a habit from tracking.
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
        habit_doc.delete()

        await update.message.reply_text(f"🗑️ Removed habit: {habit_doc.id}")
        context.user_data.pop("habit_removal_list")

    except ValueError:
        await update.message.reply_text("⚠️ Please reply with a number.")