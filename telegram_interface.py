import os
from dotenv import load_dotenv
import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import state_machine_applied as sma

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

user_state = {}


async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.effective_user.id  # investigar tipo
    sma.user_state[user_id] = "START"
    await answer_to_user(update, context, sma.run_state_machine_step(user_id, None))
    


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    text = update.message.text
    data = {"message": text}
    # The idea here is to call this on a thread or a process
    actions = sma.run_state_machine_step(update.effective_user.id, data)
    await answer_to_user(update, context, actions)


async def answer_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, actions) -> None:
    for action in actions:
        if action[0] == "text":
            await update.message.reply_text(action[1])
        elif action[0] == "keyboard":
            await update.message.reply_text("...", reply_markup=action[1])
        elif action[0] == "quiz":
            await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=action[1]["question"],
                options=action[1]["options"],
                type="quiz",
                correct_option_id=action[1]["correct_option_id"],
                is_anonymous=action[1]["is_anonymous"],
                open_period=action[1].get("open_period")
            )
        else:
            await update.message.reply_text(f"IDK how to handle this action: {action}")


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, message_handler))
    
    sma.start_state_machine()

    print("El bot ha iniciado. Presiona Ctrl+C para detenerlo.")
    application.run_polling(poll_interval=0.5)


if __name__ == "__main__":
    main()
