import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==============================
# CONFIG
# ==============================

BOT_TOKEN = "8770195835:AAFlZVpZpTAtJl5NCnJg-DaK2Nk6tQxqG0E"

ADMIN_USERNAME = "Westpablo1"
ADMIN_PASSWORD = "@Weatpablo"

CHANNEL_USERNAME = "@SwiftMintHub"
CHANNEL_LINK = "https://t.me/+xHw5c6X5rWdjZjBk"

TASK_REWARD = 5
REFERRAL_REWARD = 10
DAILY_BONUS = 5
MIN_WITHDRAW = 50
DAILY_TASK_LIMIT = 5

# ==============================
# DATABASE
# ==============================

conn = sqlite3.connect("swiftmint.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
balance INTEGER DEFAULT 0,
referrals INTEGER DEFAULT 0,
tasks INTEGER DEFAULT 0,
daily_tasks INTEGER DEFAULT 0,
last_bonus TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
wallet TEXT,
status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
link TEXT,
reward INTEGER,
status TEXT
)
""")

conn.commit()

# ==============================
# DATABASE FUNCTIONS
# ==============================

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users(id) VALUES(?)",(user_id,))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id=?",(user_id,))
    return cursor.fetchone()

def add_balance(user_id,amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?",(amount,user_id))
    conn.commit()

def remove_balance(user_id,amount):
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?",(amount,user_id))
    conn.commit()

def add_referral(user_id):
    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE id=?",(user_id,))
    conn.commit()

def add_task_count(user_id):
    cursor.execute("""
    UPDATE users
    SET tasks = tasks + 1,
    daily_tasks = daily_tasks + 1
    WHERE id=?
    """,(user_id,))
    conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE id=?",(user_id,))
    r = cursor.fetchone()
    return r[0] if r else 0

# ==============================
# ADMIN CHECK
# ==============================

def is_admin(update):
    return update.effective_user.username == ADMIN_USERNAME

# ==============================
# CHANNEL CHECK
# ==============================

async def check_channel(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME,user_id)
        if member.status in ["member","administrator","creator"]:
            return True
    except:
        pass
    return False

# ==============================
# MENUS
# ==============================

def main_menu():

    keyboard = [
        ["💰 Earn","📋 Tasks"],
        ["👥 Referral","💸 Withdraw"],
        ["👤 Profile","🏆 Leaderboard"],
        ["🎁 Daily Bonus","📞 Support"]
    ]

    return ReplyKeyboardMarkup(keyboard,resize_keyboard=True)


def admin_menu():

    keyboard = [
        ["📊 Bot Stats","📋 Manage Tasks"],
        ["💸 Withdraw Requests","📢 Broadcast"],
        ["⚙ Settings"]
    ]

    return ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

# ==============================
# START
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    add_user(user)

    joined = await check_channel(user,context.bot)

    if not joined:
        await update.message.reply_text(
            f"⚠️ You must join our channel first\n\n{CHANNEL_LINK}"
        )
        return

    if context.args:
        ref = int(context.args[0])
        if ref != user:
            add_balance(ref,REFERRAL_REWARD)
            add_referral(ref)

    await update.message.reply_text(
        "🚀 Welcome to SwiftMint Hub\nStart earning coins!",
        reply_markup=main_menu()
    )

# ==============================
# EARN
# ==============================

async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = f"""
💰 Ways To Earn

📋 Complete Tasks
👥 Invite Friends
🎁 Daily Bonus

Task Reward: {TASK_REWARD}
Referral Reward: {REFERRAL_REWARD}
"""

    await update.message.reply_text(msg)

# ==============================
# TASKS
# ==============================

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("SELECT * FROM tasks WHERE status='active'")
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("No available tasks.")
        return

    text = "📋 Available Tasks\n\n"

    for t in tasks:
        text += f"""
ID: {t[0]}
Title: {t[1]}
Reward: {t[3]}
Link: {t[2]}

"""

    await update.message.reply_text(text)

# ==============================
# DAILY BONUS
# ==============================

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    data = get_user(user)

    today = str(datetime.now().date())

    if data[5] == today:
        await update.message.reply_text("❌ You already claimed today's bonus")
        return

    add_balance(user,DAILY_BONUS)

    cursor.execute(
        "UPDATE users SET last_bonus=? WHERE id=?",
        (today,user)
    )

    conn.commit()

    await update.message.reply_text(f"🎁 Daily bonus claimed +{DAILY_BONUS}")

# ==============================
# REFERRAL
# ==============================

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    link = f"https://t.me/SwiftMint_Hub_Bot?start={user}"

    msg = f"""
👥 Referral Program

Earn {REFERRAL_REWARD} coins per invite

Your link:
{link}
"""

    await update.message.reply_text(msg)

# ==============================
# PROFILE
# ==============================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    data = get_user(user)

    msg = f"""
👤 Profile

ID: {data[0]}
Balance: {data[1]} coins
Referrals: {data[2]}
Tasks Completed: {data[3]}
"""

    await update.message.reply_text(msg)

# ==============================
# LEADERBOARD
# ==============================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cursor.execute("SELECT id,balance FROM users ORDER BY balance DESC LIMIT 10")
    users = cursor.fetchall()

    text = "🏆 Top Earners\n\n"

    rank = 1
    for u in users:
        text += f"{rank}. {u[0]} — {u[1]} coins\n"
        rank += 1

    await update.message.reply_text(text)

# ==============================
# WITHDRAW
# ==============================

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    balance = get_balance(user)

    if balance < MIN_WITHDRAW:
        await update.message.reply_text(f"❌ Minimum withdraw is {MIN_WITHDRAW} coins")
        return

    await update.message.reply_text(
        "Send withdrawal request:\n\nExample:\n100 TRC20_ADDRESS"
    )

# ==============================
# HANDLE WITHDRAW
# ==============================

async def handle_withdraw(update: Update):

    text = update.message.text
    user = update.effective_user.id

    if " " not in text:
        return

    try:

        amount = int(text.split()[0])
        wallet = text.split()[1]

        balance = get_balance(user)

        if amount > balance:
            await update.message.reply_text("❌ Not enough balance")
            return

        remove_balance(user,amount)

        cursor.execute("""
        INSERT INTO withdrawals(user_id,amount,wallet,status)
        VALUES(?,?,?,?)
        """,(user,amount,wallet,"pending"))

        conn.commit()

        await update.message.reply_text("✅ Withdrawal request submitted")

    except:
        pass

# ==============================
# SUPPORT
# ==============================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📞 Support\nAdmin: @Westpablo1"
    )

# ==============================
# ADMIN DASHBOARD
# ==============================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    await update.message.reply_text(
        "⚙ SwiftMint Admin Dashboard",
        reply_markup=admin_menu()
    )

# ==============================
# BOT STATS
# ==============================

async def bot_stats(update):

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM users")
    coins = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")
    withdraws = cursor.fetchone()[0]

    text = f"""
📊 Bot Statistics

Users: {users}
Total Coins: {coins}
Pending Withdrawals: {withdraws}
"""

    await update.message.reply_text(text)

# ==============================
# ADD TASK (ADMIN)
# ==============================

async def add_task_admin(update, context):

    if not is_admin(update):
        return

    try:

        text = " ".join(context.args)

        title = text.split("|")[0]
        link = text.split("|")[1]
        reward = int(text.split("|")[2])

        cursor.execute("""
        INSERT INTO tasks(title,link,reward,status)
        VALUES(?,?,?,?)
        """,(title,link,reward,"active"))

        conn.commit()

        await update.message.reply_text("✅ Task Added")

    except:
        await update.message.reply_text("Usage:\n/addtask Title|Link|Reward")

# ==============================
# VIEW TASKS (ADMIN)
# ==============================

async def view_tasks(update, context):

    if not is_admin(update):
        return

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("No tasks found")
        return

    text = "📋 Task List\n\n"

    for t in tasks:
        text += f"ID:{t[0]} | {t[1]} | Reward:{t[3]}\n"

    await update.message.reply_text(text)

# ==============================
# APPROVE WITHDRAW
# ==============================

async def approve_withdraw(update, context):

    if not is_admin(update):
        return

    try:

        wid = int(context.args[0])

        cursor.execute("""
        UPDATE withdrawals
        SET status='approved'
        WHERE id=?
        """,(wid,))

        conn.commit()

        await update.message.reply_text("✅ Withdrawal Approved")

    except:
        await update.message.reply_text("Usage: /approvewithdraw ID")

# ==============================
# WITHDRAWAL LIST
# ==============================

async def withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    cursor.execute("SELECT * FROM withdrawals WHERE status='pending'")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No pending withdrawals")
        return

    text = "Pending Withdrawals\n\n"

    for r in rows:
        text += f"ID:{r[0]} User:{r[1]} Amount:{r[2]} Wallet:{r[3]}\n"

    await update.message.reply_text(text)

# ==============================
# BROADCAST
# ==============================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return

    msg = " ".join(context.args)

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            await context.bot.send_message(u[0],msg)
        except:
            pass

    await update.message.reply_text("Broadcast sent")

# ==============================
# MESSAGE HANDLER
# ==============================

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "💰 Earn":
        await earn(update,context)

    elif text == "📋 Tasks":
        await tasks(update,context)

    elif text == "👥 Referral":
        await referral(update,context)

    elif text == "💸 Withdraw":
        await withdraw(update,context)

    elif text == "👤 Profile":
        await profile(update,context)

    elif text == "🏆 Leaderboard":
        await leaderboard(update,context)

    elif text == "🎁 Daily Bonus":
        await bonus(update,context)

    elif text == "📞 Support":
        await support(update,context)

    elif text == "📊 Bot Stats":
        await bot_stats(update)

    elif text == "💸 Withdraw Requests":
        await withdrawals(update,context)

    else:
        await handle_withdraw(update)

# ==============================
# MAIN
# ==============================

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("admin",admin))
    app.add_handler(CommandHandler("broadcast",broadcast))
    app.add_handler(CommandHandler("withdrawals",withdrawals))
    app.add_handler(CommandHandler("addtask",add_task_admin))
    app.add_handler(CommandHandler("viewtasks",view_tasks))
    app.add_handler(CommandHandler("approvewithdraw",approve_withdraw))

    app.add_handler(MessageHandler(filters.TEXT,messages))

    print("SwiftMint Hub Bot Running...")

    app.run_polling()

if __name__ == "__main__":
    main()
