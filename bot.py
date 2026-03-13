import re
import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# GOOGLE SHEETS CONNECTION
# -----------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

'''creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)'''

#---------------------------------------
#Added the line for variables
#------------------------------
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open("ExpenseBot").sheet1


# -----------------------------
# CATEGORY CLASSIFICATION
# -----------------------------

def categorize(item):

    item = item.lower()

    if item in ["milk","curd","butter"]:
        return "Dairy"

    if item in ["tomato","onion","potato","carrot"]:
        return "Vegetables"

    if item in ["apple","banana","mango"]:
        return "Fruits"

    if item in ["petrol","diesel","uber"]:
        return "Transport"

    return "Groceries"


# -----------------------------
# SAVE EXPENSE
# -----------------------------

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


# -----------------------------
# EXTRACT EXPENSE FROM TEXT
# -----------------------------

def extract_expense(text):

    pattern = r'([a-zA-Z]+).*?(\d+)'

    matches = re.findall(pattern, text)

    expenses = []

    for item, amount in matches:
        expenses.append((item, int(amount)))

    return expenses


# -----------------------------
# MONTHLY SUMMARY
# -----------------------------

def monthly_summary():

    records = sheet.get_all_records()

    totals = {}

    for row in records:

        cat = row["Category"]
        amt = int(row["Amount"])

        totals[cat] = totals.get(cat,0) + amt

    text = "Monthly Expense Summary\n\n"

    total = 0

    for k,v in totals.items():
        text += f"{k}: ₹{v}\n"
        total += v

    text += f"\nTotal: ₹{total}"

    return text


# -----------------------------
# TELEGRAM HANDLER
# -----------------------------

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    if msg.text:

        text = msg.text.strip()

        if text.lower() == "summary":
            await msg.reply_text(monthly_summary())
            return

        expenses = extract_expense(text)

        saved = []

        for item, amount in expenses:

            category = save_expense(item, amount)

            saved.append(f"{item} ₹{amount} ({category})")

        if saved:

            response = "Saved Expenses\n\n"
            response += "\n".join(saved)

            await msg.reply_text(response)

        else:

            await msg.reply_text(
                "Example:\nMilk 40\nBought apples for 120\nPetrol 500"
            )


# -----------------------------
# TELEGRAM BOT START
# -----------------------------

'''TOKEN = "8620766224:AAH50ZgFDdAFI5JtyoKYtUvRBvoadPILDLM"'''

TOKEN = os.getenv("TELEGRAM_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.ALL, handle))

print("Bot Running...")

app.run_polling(drop_pending_updates=True)