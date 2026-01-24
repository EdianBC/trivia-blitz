import os
from dotenv import load_dotenv
import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import state_machine_applied as sm

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN") 


async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_id = update.effective_user.id #investigar tipo

    keyboard = [KeyboardButton(text="Create a game"), KeyboardButton(text="Join a game"), KeyboardButton(text="Settings")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)

    if user_id not in sm.user_state.keys():
        sm.user_state[user_id] = "MAIN"
        await update.message.reply_text(f'Bieeeeeeeeenvenidos al Himalaya', reply_markup=reply_markup)
    else:
        reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
        await update.message.reply_text(f'Que tu quiere')
        

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    text = update.message.text    

    #The idea here is to call this on a thread or a process
    actions = sm.run_state_machine_step(update.effective_user.id, text)
    for action in actions:
        if isinstance(action, str):
            await update.message.reply_text(action)
        elif isinstance(action, ReplyKeyboardMarkup):
            await update.message.reply_text(".", reply_markup=action)
        elif isinstance(action, dict) and action.get("type") == "quiz":  # Si es un cuestionario
            await context.bot.send_poll(
                chat_id=update.effective_chat.id,
                question=action["question"],
                options=action["options"],
                type="quiz",
                correct_option_id=action["correct_option_id"],
                is_anonymous=action["is_anonymous"],
                open_period=action.get("open_period")  # Opcional
            )
        else:
            await update.message.reply_text(f"IDK how to handle this action: {action}")

# def state_machine(user_id: int, message: str):

#     state = user_state[user_id]

#     if state == "MAIN":
#         if message == "Create a game":
#             pass

#     return ["ZAAAAAAAMN"]

        

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("El bot ha iniciado. Presiona Ctrl+C para detenerlo.")
    application.run_polling(poll_interval=0.5)


if __name__ == "__main__":
    main()