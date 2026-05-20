# =========================================
# Ai Coconuts Telegram Bot
# =========================================

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os

# =========================================
# API VARIABLES
# =========================================

# Telegram Bot Token
APITG = os.getenv("APITG")

# OpenRouter API Key
APIAI = os.getenv("APIAI")

# =========================================
# SETTINGS
# =========================================

BOT_NAME = "Ai Coconuts"
MODEL = "openai/gpt-4.1-mini"

# =========================================
# MEMORY
# =========================================

current_branch = {}
memory = {}

# =========================================
# AI REQUEST
# =========================================

def ask_ai(messages):
    headers = {
        "Authorization": f"Bearer {APIAI}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": BOT_NAME,
    }

    data = {
        "model": MODEL,
        "messages": messages,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=120,
    )

    result = response.json()

    try:
        return result["choices"][0]["message"]["content"]
    except Exception:
        return str(result)

# =========================================
# HELPERS
# =========================================

def get_branch(user_id):
    if user_id not in current_branch:
        current_branch[user_id] = "main"

    return current_branch[user_id]

def get_memory(user_id):
    if user_id not in memory:
        memory[user_id] = {
            "main": []
        }

    return memory[user_id]

def get_messages(user_id):
    branch = get_branch(user_id)
    mem = get_memory(user_id)

    if branch not in mem:
        mem[branch] = []

    return mem[branch]

# =========================================
# COMMANDS
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    get_memory(user_id)

    await update.message.reply_text(
        f"""
🤖 {BOT_NAME}

Commands:

/start - Start the bot and initialize your profile
/reset - Clear memory for your current session
/branches - Show dialog branches
/branch <name> - Switch/create branch
"""
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    branch = get_branch(user_id)

    memory[user_id][branch] = []

    await update.message.reply_text(
        f"🧠 Memory cleared for: {branch}"
    )

async def branches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    mem = get_memory(user_id)
    current = get_branch(user_id)

    text = "🌴 Branches:\n\n"

    for branch in mem:
        if branch == current:
            text += f"➡️ {branch} (current)\n"
        else:
            text += f"• {branch}\n"

    text += "\nUse:\n/branch coding"

    await update.message.reply_text(text)

async def branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/branch <name>"
        )
        return

    branch_name = " ".join(context.args)

    mem = get_memory(user_id)

    if branch_name not in mem:
        mem[branch_name] = []

    current_branch[user_id] = branch_name

    await update.message.reply_text(
        f"🌴 Switched to: {branch_name}"
    )

# =========================================
# CHAT
# =========================================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    msgs = get_messages(user_id)

    system_prompt = {
        "role": "system",
        "content": (
            "You are Ai Coconuts. "
            "A powerful AI assistant for coding, Linux, Minecraft, Rust and Python."
        )
    }

    full_messages = [system_prompt] + msgs

    full_messages.append({
        "role": "user",
        "content": text
    })

    await update.message.reply_text("🧠 Thinking...")

    answer = ask_ai(full_messages)

    msgs.append({
        "role": "user",
        "content": text
    })

    msgs.append({
        "role": "assistant",
        "content": answer
    })

    if len(msgs) > 30:
        msgs[:] = msgs[-30:]

    if len(answer) > 4000:
        answer = answer[:4000]

    await update.message.reply_text(answer)

# =========================================
# MAIN
# =========================================

def main():
    print(f"{BOT_NAME} starting...")

    app = ApplicationBuilder().token(APITG).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("branches", branches))
    app.add_handler(CommandHandler("branch", branch))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )

    print("Bot online.")

    app.run_polling()

if __name__ == "__main__":
    main()
