import os
import requests
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# ENV VARIABLES
# =========================

APITG = os.getenv("APITG")
APIAI = os.getenv("APIAI")

BOT_NAME = "Ai Coconuts"
MODEL = "openai/gpt-4.1-mini"

# =========================
# MEMORY
# =========================

memory = {}
current_branch = {}
user_lang = {}

LANGUAGES = [
    "Ukrainian",
    "English",
    "Russian",
    "German",
    "French",
    "Japanese",
    "Chinese",
]

# =========================
# HELPERS
# =========================

def get_memory(user_id):
    if user_id not in memory:
        memory[user_id] = {"main": []}
    return memory[user_id]

def get_branch(user_id):
    if user_id not in current_branch:
        current_branch[user_id] = "main"
    return current_branch[user_id]

def get_lang(user_id):
    if user_id not in user_lang:
        user_lang[user_id] = "Ukrainian"
    return user_lang[user_id]

def get_messages(user_id):
    mem = get_memory(user_id)
    branch = get_branch(user_id)

    if branch not in mem:
        mem[branch] = []

    return mem[branch]

# =========================
# OPENROUTER
# =========================

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

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=120,
    )

    try:
        return r.json()["choices"][0]["message"]["content"]
    except:
        return str(r.json())

# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_memory(user_id)

    await update.message.reply_text(
        f"""
🤖 {BOT_NAME}

Команди:

/start - Запустити бота
/reset - Очистити памʼять
/branches - Гілки діалогу
/branch <назва> - Перемкнути гілку
/language - Змінити мову

Просто напиши повідомлення 👇
"""
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    branch = get_branch(user_id)

    memory[user_id][branch] = []

    await update.message.reply_text(
        f"🧠 Памʼять очищено: {branch}"
    )

async def branches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    mem = get_memory(user_id)
    current = get_branch(user_id)

    text = "🌴 Гілки діалогу:\n\n"

    for b in mem:
        if b == current:
            text += f"➡️ {b} (поточна)\n"
        else:
            text += f"• {b}\n"

    text += "\nВикористання: /branch coding"

    await update.message.reply_text(text)

async def branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Використання: /branch <назва>")
        return

    name = " ".join(context.args)

    mem = get_memory(user_id)

    if name not in mem:
        mem[name] = []

    current_branch[user_id] = name

    await update.message.reply_text(
        f"🌴 Перемкнуто на гілку: {name}"
    )

# =========================
# LANGUAGE UI
# =========================

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for lang in LANGUAGES:
        keyboard.append([
            InlineKeyboardButton(lang, callback_data=f"lang_{lang}")
        ])

    await update.message.reply_text(
        "🌍 Обери мову:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def language_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang = query.data.replace("lang_", "")

    user_lang[user_id] = lang

    await query.edit_message_text(
        f"🌍 Мову змінено на: {lang}"
    )

# =========================
# CHAT
# =========================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    msgs = get_messages(user_id)
    lang = get_lang(user_id)

    system_prompt = {
        "role": "system",
        "content": (
            f"You are Ai Coconuts. "
            f"You are a powerful AI assistant. "
            f"Always respond in {lang}. "
            f"If user writes another language, translate automatically."
        )
    }

    full = [system_prompt] + msgs
    full.append({"role": "user", "content": text})

    await update.message.reply_text("🧠 Думаю...")

    answer = ask_ai(full)

    msgs.append({"role": "user", "content": text})
    msgs.append({"role": "assistant", "content": answer})

    if len(msgs) > 30:
        msgs[:] = msgs[-30:]

    await update.message.reply_text(answer)

# =========================
# MAIN
# =========================

def main():
    print(f"{BOT_NAME} starting...")

    app = ApplicationBuilder().token(APITG).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("branches", branches))
    app.add_handler(CommandHandler("branch", branch))
    app.add_handler(CommandHandler("language", language))

    app.add_handler(CallbackQueryHandler(language_button))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot online.")

    app.run_polling()

if __name__ == "__main__":
    main()
