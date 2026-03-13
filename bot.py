import re
import os
import json
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------

TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDENTIALS")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set")

if not GOOGLE_CREDS:
    raise ValueError("GOOGLE_CREDENTIALS not set")

if not SHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID not set")


# ------------------------------------------------
# GOOGLE SHEETS CONNECTION
# ------------------------------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(GOOGLE_CREDS)

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID).sheet1


# ------------------------------------------------
# CATEGORY CLASSIFICATION
# ------------------------------------------------

def categorize(item):

    item = item.lower()

    dairy = ["milk","curd","butter","cheese"]
    vegetables = ["tomato","onion","potato","carrot","beans"]
    fruits = ["apple","banana","mango","orange"]
    transport = ["petrol","diesel","uber","fuel"]

    if item in dairy:
        return "Dairy"

    if item in vegetables:
        return "Vegetables"

    if item in fruits:
        return "Fruits"

    if item in transport:
        return "Transport"

    return "Groceries"


# ------------------------------------------------
# SAVE EXPENSE
# ------------------------------------------------

def save_expense(item, amount):

    category = categorize(item)

    sheet.append_row([
        str(datetime.now()),
        item,
        category,
        amount,
        "Telegram"
    ])

    return category


# ------------------------------------------------
# EXTRACT EXPENSE FROM TEXT
# ------------------------------------------------

def extract_expense(text):

    pattern = r'([a-zA-Z]+).*?(\d+)'

    matches = re.findall(pattern, text)

    expenses = []

    for item, amount in matches:
        expenses.append((item, int(amount)))

    return expenses


# ------------------------------------------------
# MONTHLY SUMMARY
# ------------------------------------------------

def monthly_summary():

    records = sheet.get_all_records()

    totals = {}

    for row in records:

        category = row["Category"]
        amount = int(row["Amount"])

        totals[category] = totals.get(category,0) + amount

    text = "📊 Monthly Expense Summary\n\n"

    total = 0

    for k,v in totals.items():

        text += f"{k}: ₹{v}\n"

        total += v

    text += f"\nTotal: ₹{total}"

    return text


# ------------------------------------------------
# TELEGRAM MESSAGE HANDLER
# ------------------------------------------------

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if not msg:
        return

    if msg.text:

        text = msg.text.strip()

        # summary command
        if text.lower() == "summary":

            await msg.reply_text(monthly_summary())

            return

        # extract expenses
        expenses = extract_expense(text)

        saved = []

        for item, amount in expenses:

            category = save_expense(item, amount)

            saved.append(f"{item} ₹{amount} ({category})")

        if saved:

            response = "✅ Saved Expenses\n\n"

            response += "\n".join(saved)

            await msg.reply_text(response)

        else:

            await msg.reply_text(
                "Example:\nMilk 40\nBought apples for 120\nPetrol 500"
            )


# ------------------------------------------------
# BOT START
# ------------------------------------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.ALL, handle))

print("Bot Running...")

app.run_polling(drop_pending_updates=True)