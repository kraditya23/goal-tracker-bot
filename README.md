# 📅 Telegram Goal Tracker Bot

A personal productivity Telegram bot to help you plan, track, and reflect on your daily goals and habits. Add goals, track habits daily, mark tasks complete, and receive daily summaries automatically at midnight IST.

👉 Try it now: [@goal_tracker23_bot](https://t.me/goal_tracker23_bot)

---

## ✨ Features

### 📌 Daily Goals
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

### 🧾 Coming Soon
- 📈 Monthly PDF summary of goals and habit completion rates

---

## 🛠️ Tech Stack

- **Python**
- **python-telegram-bot v20+**
- **Firebase Firestore** (via `firebase-admin`)
- **APScheduler** – for daily job scheduling
- **Render** – for cloud deployment
- **dotenv** – for environment variable management

---

## 📦 Installation

```bash
git clone https://github.com/kraditya23/goal-tracker-bot.git
cd goal-tracker-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt