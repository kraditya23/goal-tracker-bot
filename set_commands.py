# set_commands.py
from telegram import Bot, BotCommand
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

## Sets Telegram bot commands to enhance user interaction.
async def force_set_commands():
    bot = Bot(token=TOKEN)
    commands = [
        BotCommand("start", "Welcome & list features"),
        BotCommand("addgoal", "Add a new goal for today"),
        BotCommand("removegoal", "Remove a pending goal"),
        BotCommand("markcompleted", "Mark a goal as completed"),
        BotCommand("summary", "Show today's goal + habit summary"),
        BotCommand("addhabit", "Start tracking a new habit"),
        BotCommand("removehabit", "Remove an existing habit"),
        BotCommand("monthlytrackers", "Answer daily habit questions"),
    ]
    await bot.set_my_commands(commands)
    print("✅ Commands successfully registered.")

asyncio.run(force_set_commands())