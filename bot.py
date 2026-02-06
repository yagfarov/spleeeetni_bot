from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from db import init_db, add_entry, get_entries_by_sentiment
from nlp_processing import analyze_sentiment, anonymize_text
from config import TELEGRAM_TOKEN

init_db()

KEYBOARD = ReplyKeyboardMarkup(
    [
        ["✍️ Отправить историю"],
        ["🙂 Happy истории", "☹️ Sad истории"],
    ],
    resize_keyboard=True,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет.\n\n"
        "Спасибо, что заглянул в этот маленький эксперимент. "
        "Перед тобой — анонимный дневник историй.\n\n"
        "Здесь можно оставить свою историю или прочитать чужие. "
        "Мы стараемся сохранить пространство безопасным и обезличенным, "
        "поэтому просьба не использовать имена людей и названия городов.\n\n"
        "Если вдруг в тексте проскочит имя или город — не переживай, "
        "они будут автоматически заменены на *ИМЯ* и *ГОРОД*.\n\n"
        "Имей в виду: твоя история может быть прочитана другими пользователями. "
        "Но никто и никогда не узнает, кто её написал.\n\n"
        "Пиши, если готов. Или просто читай.",
        reply_markup=KEYBOARD,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "✍️ Отправить историю":
        context.user_data["awaiting_story"] = True
        await update.message.reply_text("Напиши свою историю:")
        return

    if text == "🙂 Happy истории":
        stories = get_entries_by_sentiment("happy")
        await send_stories(update, stories)
        return

    if text == "☹️ Sad истории":
        stories = get_entries_by_sentiment("sad")
        await send_stories(update, stories)
        return

    # Пользователь пишет историю
    if context.user_data.get("awaiting_story"):
        sentiment = analyze_sentiment(text)
        anonymized = anonymize_text(text)
        add_entry(user_id, text, anonymized, sentiment)

        context.user_data["awaiting_story"] = False
        await update.message.reply_text(
            f"История сохранена ✨\n"
            f"Настроение: {sentiment}\n\n"
            f"Анонимная версия:\n{anonymized}",
            reply_markup=KEYBOARD,
        )
        return

    await update.message.reply_text("Выбери действие 👇", reply_markup=KEYBOARD)

async def send_stories(update: Update, stories: list[str]):
    if not stories:
        await update.message.reply_text("Пока историй нет 😕")
        return

    for story in stories[:5]:
        await update.message.reply_text(story)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
