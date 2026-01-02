import os
from dotenv import load_dotenv
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN") 


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Bieeeeeeeeenvenidos al Himalaya')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text    
    await update.message.reply_text(text)


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    print("El bot ha iniciado. Presiona Ctrl+C para detenerlo.")
    application.run_polling(poll_interval=1.0)


if __name__ == "__main__":
    main()