from telegram import ReplyKeyboardMarkup, KeyboardButton
import state_machine as sm
import asyncio
import game_manager as gm
import random


task_queue = asyncio.Queue()
user_state = {}
user_vault = {}


async def games_monitor():
    while True:
        print(f"Games running now: {list(gm.game_rooms.keys())}")
        await asyncio.sleep(3)


#region State Machine Setup
async def start_state_machine():
    #          State Name   Entry Function   Core Function   Transition Function
    await sm.add_state("TEST", test_entry, test_core, test_transition)
    await sm.add_state("START", None, start_core, start_transition)
    await sm.add_state("MAIN", main_entry, None, main_transition)
    await sm.add_state("CREATE", create_entry, None, create_transition)
    await sm.add_state("NUMQUESTIONS", None, None, numquestions_transition)
    await sm.add_state("DIFFICULTY", None, None, difficulty_transition)
    await sm.add_state("TIMETOANSWER", None, None, timetoanswer_transition)
    await sm.add_state("USERNAME", None, None, username_transition)
    await sm.add_state("GAMEROOMNAME", None, None, gameroomname_transition)
    await sm.add_state("JOIN", join_entry, None, join_transition)
    await sm.add_state("SETTINGS", settings_entry, None, settings_transition)
    await sm.add_state("WAITROOM", waitroom_entry, None, waitroom_transition)
    await sm.add_state("ADMWAITROOM", admin_waitroom_entry, None, admin_waitroom_transition)
    await sm.add_state("GAME", None, None, game_transition)

    asyncio.create_task(games_monitor())

async def run_state_machine_step(data: dict) -> list:
    user_id = data.get("id")
    if user_id not in user_state:
        user_state[user_id] = "START"
        user_vault[user_id] = {}

    state = user_state[user_id]
    next_state = await sm.run_state(state, data)
    user_state[user_id] = next_state


#region Protocols

# Entries must receive a dict with data (for example {"message":"hi"}) and return a list of pairs (type, content)
# Cores must receive a dict with data and return a list of pairs (type, content)
# Transitions must receive a dict with data and return a tuple (next_state_name, list of pairs (type, content))

# TEST
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



# START
async def start_core(data):
    await task_queue.put((data["id"], ("text", "Welcome to the game!")))
    # await task_queue.put((data["id"], ("run", data)))

async def start_transition(data):
    return "MAIN"


#region MAIN MENU
async def main_entry(data):
    keyboard = [KeyboardButton(text="Host a game"), KeyboardButton(text="Join a game"), KeyboardButton(text="Settings")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "You are on the main menu!", reply_markup)))

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
        await task_queue.put((data["id"], ("text", "Invalid option")))
        return "MAIN"


#region CREATION MENU
async def create_entry(data):
    keyboard = [[KeyboardButton(text="Create game"), KeyboardButton(text="Game room name")],
                [KeyboardButton(text="Number of questions"), KeyboardButton(text="Difficulty")], 
                [KeyboardButton(text="Time to answer"), KeyboardButton(text="Username")],
                [KeyboardButton(text="Back")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "This is the game creation menu", reply_markup)))

    game_room_name = user_vault[data["id"]].setdefault('game_room_id', f'MyGameRoom{random.randint(1000,9999)}')
    number_of_questions = user_vault[data["id"]].setdefault('number_of_questions', 20)
    difficulty = user_vault[data["id"]].setdefault('difficulty', 'Easy')
    time_to_answer = user_vault[data["id"]].setdefault('time_to_answer', 20)
    username = user_vault[data["id"]].setdefault('username', f'Player{random.randint(1000,9999)}')
    current_settings = (
    f"🎮 Current Game Settings 🎮\n\n"
    f"🏷️ Name: {game_room_name}\n"
    f"❓ Number of Questions: {number_of_questions}\n"
    f"🎯 Difficulty: {difficulty}\n"
    f"⏱️ Time to Answer: {time_to_answer} seconds\n"
    f"👤 Username: {username}\n"
    )
    await task_queue.put((data["id"], ("text", current_settings)))

async def create_transition(data):
    message = data.get("message")

    if message == "Back":
        return "MAIN"
    elif message == "Number of questions":
        await task_queue.put((data["id"], ("textnokeyboard", "Please enter the number of questions for the game:")))
        return "NUMQUESTIONS"
    elif message == "Difficulty":
        #Maybe put a keyboard with options here
        await task_queue.put((data["id"], ("textnokeyboard", "Please enter the difficulty level (Easy, Medium, Hard):")))
        return "DIFFICULTY"
    elif message == "Time to answer":
        await task_queue.put((data["id"], ("textnokeyboard", "Please enter the time to answer each question (in seconds):")))
        return "TIMETOANSWER"
    elif message == "Username":
        await task_queue.put((data["id"], ("textnokeyboard", "Please enter your username:")))
        return "USERNAME"
    elif message == "Game room name":
        await task_queue.put((data["id"], ("textnokeyboard", "Please enter the desired game room name:")))
        return "GAMEROOMNAME"
    elif message == "Create game":
        game_room_id = user_vault[data["id"]].get('game_room_id')
        if await gm.game_room_exists(game_room_id):
            await task_queue.put((data["id"], ("text", f"A game with the name '{game_room_id}' already exists")))
            return "CREATE"
        else:
            # FIX: Revisar esto bien luego porque no me gusta eso de crear la sala asi
            num_of_questions = user_vault[data["id"]].get('number_of_questions')
            difficulty = user_vault[data["id"]].get('difficulty')
            time_to_answer = user_vault[data["id"]].get('time_to_answer')
            await gm.create_game_room(game_room_id, num_of_questions, difficulty, time_to_answer)
            await gm.set_admin_in_room(user_vault[data["id"]]['username'], data["id"], game_room_id)
            await task_queue.put((data["id"], ("text", f"Game {game_room_id} created successfully.")))
            return "ADMWAITROOM"

async def numquestions_transition(data):
    message = data.get("message")
    if message.isdigit() and int(message) > 0:
        user_vault[data["id"]]['number_of_questions'] = int(message)
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "Enter a valid positive integer for the number of questions")))
        return "NUMQUESTIONS"
    
async def difficulty_transition(data):
    message = data.get("message")
    if message in ["Easy", "Medium", "Hard"]:
        user_vault[data["id"]]['difficulty'] = message
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "Enter a valid difficulty level: Easy, Medium, or Hard")))
        return "DIFFICULTY"
    
async def timetoanswer_transition(data):
    message = data.get("message")
    if message.isdigit() and int(message) > 0:
        user_vault[data["id"]]['time_to_answer'] = int(message)
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "Enter a valid positive integer for the time to answer")))
        return "TIMETOANSWER"
    
async def username_transition(data):
    message = data.get("message")
    if message:
        user_vault[data["id"]]['username'] = message
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "Username cannot be empty. Please enter a valid username.")))
        return "USERNAME"
    
async def gameroomname_transition(data):
    message = data.get("message")
    if message:
        user_vault[data["id"]]['game_room_id'] = message
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "Game room name cannot be empty. Please enter a valid name.")))
        return "GAMEROOMNAME"
    
    


#region JOIN MENU
async def join_entry(data):
    keyboard = [KeyboardButton(text="Change username"), KeyboardButton(text="Back")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)

    username = user_vault[data["id"]].setdefault('username', f'Player{random.randint(1000,9999)}')
    await task_queue.put((data["id"], ("textkeyboard", f"You are currently loged in as '{username}'\nIf you want to change it do it, if not then just type the name of the game room you want to join", reply_markup)))

async def join_transition(data):
    message = data.get("message")

    if message == "Back":
        return "MAIN"
    elif message == "Change username":
        await task_queue.put((data["id"], ("textnokeyboard", "Please enter your desired username:")))
        return "USERNAME"
    else:
        game_room_id = message.strip()
        if await gm.game_room_exists(game_room_id):
            await gm.add_player_to_room(user_vault[data["id"]]['username'], data["id"], game_room_id) #FIX: podria estar repetido el nombre
            await task_queue.put((data["id"], ("text", f"You have successfully joined the game: {game_room_id}")))
            user_vault[data["id"]]['game_room_id'] = game_room_id
            return "WAITROOM"
        else:
            await task_queue.put((data["id"], ("text", "That game room does not exist mate, get real")))
            return "JOIN"

    

# SETTINGS
async def settings_entry(data):
    await task_queue.put((data["id"], ("textnokeyboard", "Settings are not implemented yet.")))
    await task_queue.put((data["id"], ("run", data)))

async def settings_transition(data):
    return "MAIN"


#region WAITING ROOM AND GAME
async def waitroom_entry(data):
    keyboard = [KeyboardButton(text="Leave Game")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "You are now in the waiting room. Please wait for the game to start", reply_markup)))

async def waitroom_transition(data):
    if data.get("move_on", False):
        keyboard = [KeyboardButton(text="Abandon Game")]
        reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
        await task_queue.put((data["id"], ("textkeyboard", "The game is starting...", reply_markup)))
        return "GAME"
    if data.get("game_cancelled", False):
        await task_queue.put((data["id"], ("text", "The game has been cancelled by the host")))
        return "MAIN"
    
    message = data.get("message")

    if message == "Leave Game":
        await gm.remove_player_from_room(data["id"], user_vault[data["id"]]['game_room_id'])
        await task_queue.put((data["id"], ("text", "You have left the game")))
        return "MAIN"
    else:
        await task_queue.put((data["id"], ("text", "Waiting for the game to start...")))
        return "WAITROOM"
    

# ADMWAITROOM
async def admin_waitroom_entry(data):
    keyboard = [KeyboardButton(text="Start Game"), KeyboardButton(text="Leave Game")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "You are now in the waiting room as admin. Start the game when you are ready", reply_markup)))

async def admin_waitroom_transition(data):
    message = data.get("message")

    if message == "Start Game":
        keyboard = [KeyboardButton(text="Abandon Game")]
        reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
        await task_queue.put((data["id"], ("textkeyboard", "The game is starting...", reply_markup)))
        await gm.start_game_in_room(user_vault[data["id"]]['game_room_id'])
        return "GAME"
    elif message == "Leave Game":
        await gm.set_game_cancelled(user_vault[data["id"]]['game_room_id'])
        await task_queue.put((data["id"], ("text", "You have cancelled the game")))
        return "MAIN"
    else:
        await task_queue.put((data["id"], ("text", "Waiting for the game to start...")))
        return "ADMWAITROOM"



# GAME
async def game_transition(data):
    if data.get("game_over", False):
        return "MAIN"
    
    message = data.get("message")
    if message == "Abandon Game":
        await gm.remove_player_from_room(user_vault[data["id"]]['username'], user_vault[data["id"]]['game_room_id'])
        await task_queue.put((data["id"], ("text", "You have abandoned the game")))
        return "MAIN"
    else:
        await gm.submit_answer_in_room(user_vault[data["id"]]['username'], user_vault[data["id"]]['game_room_id'], message)
    return "GAME"

#endregion