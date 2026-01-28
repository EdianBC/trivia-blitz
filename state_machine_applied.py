from telegram import ReplyKeyboardMarkup, KeyboardButton
import state_machine as sm
import asyncio

task_queue = asyncio.Queue()
user_state = {}
user_vault = {}
game_names = []


async def start_state_machine():
    await sm.add_state("TEST", test_entry, test_core, test_transition)
    await sm.add_state("START", start_entry, start_core, start_transition)
    await sm.add_state("MAIN", main_entry, main_core, main_transition)
    await sm.add_state("CREATE", create_entry, create_core, create_transition)
    await sm.add_state("JOIN", join_entry, join_core, join_transition)
    await sm.add_state("SETTINGS", settings_entry, settings_core, settings_transition)
    await sm.add_state("WAITROOM", waitroom_entry, waitroom_core, waitroom_transition)
    await sm.add_state("ADMWAITROOM", admin_waitroom_entry, admin_waitroom_core, admin_waitroom_transition)

async def run_state_machine_step(data: dict) -> list:
    user_id = data.get("id")
    if user_id not in user_state:
        user_state[user_id] = "START"

    state = user_state[user_id]
    next_state = await sm.run_state(state, data)
    user_state[user_id] = next_state


#region Protocols

# Entries must receive a dict with data (for example {"message":"hi"}) and return a list of pairs (type, content)
# Cores must receive a dict with data and return a list of pairs (type, content)
# Transitions must receive a dict with data and return a tuple (next_state_name, list of pairs (type, content))

async def test_entry(data):
    keyboard = [KeyboardButton(text="Option 1"), KeyboardButton(text="Option 2")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "You are in test state now", reply_markup)))

async def test_core(data):
    question = "What is the capital of France?"
    options = ["Paris", "Berlin", "Madrid", "Rome"]
    correct_option_id = 0  # Índice de la respuesta correcta ("Paris")
    
    # Crear un diccionario con los datos del cuestionario
    quiz = {
        "type": "quiz",
        "question": question,
        "options": options,
        "correct_option_id": correct_option_id,
        "is_anonymous": False,  # Para que no sea anónimo
        "open_period": 30  # Duración de la encuesta en segundos
    }

    await task_queue.put((data["id"], ("quiz", quiz)))

async def test_transition(data):
    return "MAIN"




async def start_entry(data):
    pass

async def start_protocol(data):
    await task_queue.put((data["id"], ("text", "Welcome to the game!")))

async def start_core(data):
    pass

async def start_transition(data):
    return "MAIN"



async def main_entry(data):
    keyboard = [KeyboardButton(text="Host a game"), KeyboardButton(text="Join a game"), KeyboardButton(text="Settings")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    # return [("textkeyboard", ("Welcome to the main menu!", reply_markup))]
    await task_queue.put((data["id"], ("textkeyboard", "Welcome to the main menu!", reply_markup)))

async def main_core(data):
    pass

async def main_transition(data):
    message = data.get("message")

    if message == "Host a game":
        return "CREATE"
    
    elif message == "Join a game":
        return "JOIN"
    
    elif message == "Settings":
        return "SETTINGS"
    
    elif message == "TEST":
        return "TEST"
    
    else:
        await task_queue.put((data["id"], ("text", "Invalid option. Please choose again.")))
        return "MAIN"



async def create_entry(data):
    keyboard = [KeyboardButton(text="Back")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "Please enter the game name:", reply_markup)))

async def create_core(data):
    #TASK Create hash generation for game codes
    pass

async def create_transition(data):
    message = data.get("message")
    game_name = message.strip()

    if message == "Back":
        return "MAIN"
    
    if game_name in game_names:
        await task_queue.put((data["id"], ("text", "A game with this name already exists")))
        return "CREATE"
    else:
        game_names.append(game_name)
        await task_queue.put((data["id"], ("text", f"Game {game_name} created successfully.")))
        return "ADMWAITROOM"
    


async def join_entry(data):
    keyboard = [KeyboardButton(text="Back")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "Please enter the game code:", reply_markup)))

async def join_core(data):
    pass

async def join_transition(data):
    message = data.get("message")
    game_code = message.strip()

    if message == "Back":
        return "MAIN"
    
    if game_code in game_names:
        await task_queue.put((data["id"], ("text", f"You have successfully joined the game: {game_code}")))
        return "WAITROOM"
    else:
        await task_queue.put((data["id"], ("text", "Invalid game code")))
        return "JOIN"
    


async def settings_entry(data):
    await task_queue.put((data["id"], ("textnokeyboard", "Settings are not implemented yet.")))
    await task_queue.put((data["id"], ("run", data)))

async def settings_core(data):
    pass

async def settings_transition(data):
    return "MAIN"



async def waitroom_entry(data):
    keyboard = [KeyboardButton(text="Leave Game")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "You are now in the waiting room. Please wait for the game to start", reply_markup)))

async def waitroom_core(data):
    pass

async def waitroom_transition(data):
    message = data.get("message")

    if message == "Leave Game":
        await task_queue.put((data["id"], ("text", "You have left the game")))
        return "MAIN"
    else:
        await task_queue.put((data["id"], ("text", "Waiting for the game to start...")))
        return "WAITROOM"
    


async def admin_waitroom_entry(data):
    keyboard = [KeyboardButton(text="Start Game"), KeyboardButton(text="Leave Game")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "You are now in the waiting room as admin. You can start the game or leave.", reply_markup)))

async def admin_waitroom_core(data):
    pass

async def admin_waitroom_transition(data):
    message = data.get("message")

    if message == "Start Game":
        await task_queue.put((data["id"], ("text", "The game is starting...")))
        return "MAIN"
    elif message == "Leave Game":
        await task_queue.put((data["id"], ("text", "You have left the game")))
        return "MAIN"
    else:
        await task_queue.put((data["id"], ("text", "Waiting for the game to start...")))
        return "ADMWAITROOM"

#endregion