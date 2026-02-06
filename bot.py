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

# ====== Инициализация базы данных ======
init_db()

# ====== Клавиатура ======
KEYBOARD = ReplyKeyboardMarkup(
    [
        ["✍️ Отправить историю"],
        ["🙂 Happy истории", "☹️ Sad истории"],
    ],
    resize_keyboard=True,
)

# ====== Стартовое сообщение ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👋\n\n"
        "Спасибо, что заглянул в наш маленький эксперимент — "
        "анонимный дневник историй.\n\n"
        "Здесь можно оставить свою историю или прочитать чужие. "
        "Мы стараемся сохранить пространство безопасным и обезличенным, "
        "поэтому просьба не использовать имена людей и названия городов.\n\n"
        "Если вдруг в тексте проскочит имя или город — не переживай, "
        "они будут заменены на *ИМЯ* и *ГОРОД* автоматически.\n\n"
        "Имей в виду: твоя история может быть прочитана другими пользователями, "
        "но никто не узнает, кто её написал.\n\n"
        "Пиши, если готов. Или просто читай.",
        reply_markup=KEYBOARD,
    )

# ====== Обработка сообщений ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # 1. Пользователь хочет написать историю
    if text == "✍️ Отправить историю":
        context.user_data["awaiting_story"] = True
        await update.message.reply_text("Напиши свою историю:")
        return

    # 2. Пользователь хочет почитать истории по настроению
    if text in ["🙂 Happy истории", "☹️ Sad истории"]:
        sentiment = "happy" if "Happy" in text else "sad"
        stories = get_entries_by_sentiment(sentiment)
        await send_stories(update, stories)
        return

    # 3. Пользователь прислал историю
    if context.user_data.get("awaiting_story"):
        context.user_data["awaiting_story"] = False

        # Сначала анализ настроения
        sentiment = analyze_sentiment(text)

        # Анонимизация текста
        anonymized = anonymize_text(text)

        # Сохраняем в базу
        add_entry(user_id, text, anonymized, sentiment)

        await update.message.reply_text(
            f"История сохранена ✨\n"
            f"Настроение: {sentiment}\n\n"
            f"Анонимная версия:\n{anonymized}",
            reply_markup=KEYBOARD,
        )
        return

    # 4. Любое другое сообщение — показываем выбор
    await update.message.reply_text("Выбери действие 👇", reply_markup=KEYBOARD)

# ====== Отправка историй ======
async def send_stories(update: Update, stories: list[str]):
    if not stories:
        await update.message.reply_text("Пока историй нет 😕")
        return

    # Отправляем только первые 5 историй за раз
    for story in stories[:5]:
        # Telegram может блокировать слишком длинные сообщения, делим по 4000 символов
        for i in range(0, len(story), 4000):
            await update.message.reply_text(story[i:i + 4000])

# ====== Основная функция ======
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
