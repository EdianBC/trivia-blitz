import os
from dotenv import load_dotenv
import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import BotCommand
import asyncio
from datetime import datetime
import state_machine_applied as sma

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

last_message_id = {}

async def post_init(application):
    await set_bot_commands(application)
    await sma.start_state_machine()
    asyncio.create_task(task_handler(application))

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Inicia el bot"),
        BotCommand("time", "Muestra la hora actual y la actualiza durante 5 segundos"),
        BotCommand("help", "Muestra información sobre cómo usar el bot"),
    ]
    await application.bot.set_my_commands(commands)

async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id  # investigar tipo
    username = update.effective_user.username
    sma.user_state[user_id] = "START"
    sma.user_vault[user_id] = {"username": username}
    await sma.run_state_machine_step({"id": user_id})
    
async def time_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Enviar un mensaje inicial con la hora actual
    message = await update.message.reply_text(f"Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Actualizar el mensaje cada segundo durante 5 segundos
    for _ in range(5):
        await asyncio.sleep(1)  # Esperar 1 segundo
        await message.edit_text(f"Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Opcional: Agregar un mensaje final indicando que la actualización terminó
    await message.edit_text("Actualización completada.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    data = {"id": update.effective_user.id, "message": text}
    await sma.run_state_machine_step(data)
    #asyncio.create_task(sma.run_state_machine_step(data))

async def task_handler(application):
    while True:
        try:
            user_id, action = sma.task_queue.get_nowait()
            await answer_to_user(application, user_id, action)
        except asyncio.QueueEmpty:
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in task_handler: {e}\n\nAction: {action}")

async def answer_to_user(application, user_id, action) -> None:
     
    if action[0] == "text":
        message_sent = await application.bot.send_message(chat_id=user_id, text=action[1], parse_mode="Markdown")
        last_message_id[user_id] = message_sent.message_id
    elif action[0] == "keyboard":
        message_sent = await application.bot.send_message(chat_id=user_id, text="...", reply_markup=action[1], parse_mode="Markdown")  
        last_message_id[user_id] = message_sent.message_id
    elif action[0] == "textkeyboard":
        message_sent = await application.bot.send_message(chat_id=user_id, text=action[1], reply_markup=action[2], parse_mode="Markdown")
        last_message_id[user_id] = message_sent.message_id
    elif action[0] == "textnokeyboard":
        message_sent = await application.bot.send_message(chat_id=user_id, text=action[1], reply_markup=telegram.ReplyKeyboardRemove(), parse_mode="Markdown")
        last_message_id[user_id] = message_sent.message_id
    elif action[0] == "quiz":
        await application.bot.send_poll(
            chat_id=user_id,
            question=action[1]["question"],
            options=action[1]["options"],
            type="quiz",
            correct_option_id=action[1]["correct_option_id"],
            is_anonymous=action[1]["is_anonymous"],
            open_period=action[1].get("open_period")
        )
    elif action[0] == "run":
        data = action[1]
        await sma.run_state_machine_step(data)
        #asyncio.create_task(sma.run_state_machine_step(data))
    elif action[0] == "edittext":
        if user_id in last_message_id:
            try:
                await application.bot.edit_message_text(chat_id=user_id, message_id=last_message_id[user_id], text=action[1], parse_mode="Markdown")
            except telegram.error.TelegramError as e:
                print(f"Failed to edit message for user {user_id}: {e}")
        else:
            message_sent = await application.bot.send_message(chat_id=user_id, text=action[1], parse_mode="Markdown")
            last_message_id[user_id] = message_sent.message_id
    elif action[0] == "textnoedit":
        message_sent = await application.bot.send_message(chat_id=user_id, text=action[1], parse_mode="Markdown")
    else:
        message_sent = await application.bot.send_message(chat_id=user_id, text= f"Mmm... Thinking... Brrrr Bipp Bopp... System Overload... Error 404... Just kidding!")
        last_message_id[user_id] = message_sent.message_id
        print(f"Unknown action type: {action[0]}")



def main() -> None:
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start_command_handler))
    application.add_handler(CommandHandler("time", time_command_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("El bot ha iniciado. Presiona Ctrl+C para detenerlo.")
    application.run_polling(poll_interval=0.5)


if __name__ == "__main__":
    main()
