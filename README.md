# 📅 Telegram Goal Tracker Bot

Boost your productivity with this personal Telegram bot designed to help you plan, track, and reflect on your daily goals and habits. Stay consistent, monitor your performance, and receive automated summaries every night — all via Telegram.

👉 Try it now: [@goal_tracker23_bot](https://t.me/goal_tracker23_bot)

---

## ✨ Features

### 🎯 Daily Goals
- `/addgoal <goal>` – Add a new goal for today (e.g. `/addgoal Gym`)
- `/removegoal` – Shows a numbered list of today’s goals to remove
- `/markcompleted` – Mark a goal as completed by selecting its number
- `/summary` – View a summary of today’s goals with ✅ / ❌ status
- 🕛 **Automatic Daily Summary** – Sent every night at 00:00 IST using APScheduler

### 🧠 Habit Tracking
- `/addhabit <habit>` – Add a new monthly habit to track (e.g. `/addhabit Sleep Early`)
- `/removehabit` – Remove a habit from the tracking list
- `/monthlytrackers` – Log your habits for the day with Yes / No / Later options
- ❌ If not filled by 00:00, unanswered habits are marked "no" automatically

### 📄 Coming Soon
- 📈 Monthly PDF reports summarizing your goal and habit progress

---

## 🛠️ Tech Stack

- **Python**
- **python-telegram-bot v20+**
- **Firebase Firestore** (`firebase-admin`)
- **APScheduler** – For job scheduling (e.g. 00:00 summaries)
- **Railway** – Deployment platform
- **python-dotenv** – Manages environment variables

---

## 🚀 Installation

```bash
git clone https://github.com/kraditya23/goal-tracker-bot.git
cd goal-tracker-bot
python3 -m venv venv
source venv/bin/activate  # Use 'venv\Scripts\activate' on Windows
pip install -r requirements.txt
```

### 🔐 Setup

1. Create a `.env` file in the root directory and add your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

2. Add your Firebase service account file as `serviceAccountKey.json` in the root directory.

You're ready to run the bot with:
```bash
python main.py
```

---