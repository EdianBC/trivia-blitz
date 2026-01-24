from telegram import ReplyKeyboardMarkup, KeyboardButton
import state_machine as sm
import random

user_state = {}
game_names = []


def start_state_machine():
    sm.add_state("TEST", test_entry, test_core, test_transition)
    sm.add_state("START", start_entry, start_core, start_transition)
    sm.add_state("MAIN", main_entry, main_core, main_transition)
    sm.add_state("CREATE", create_entry, create_core, create_transition)
    sm.add_state("JOIN", join_entry, join_core, join_transition)
    sm.add_state("SETTINGS", settings_entry, settings_core, settings_transition)
    sm.add_state("WAITROOM", waitroom_entry, waitroom_core, waitroom_transition)


def run_state_machine_step(user_id: int, data: dict) -> list:
    
    if user_id not in user_state:
        user_state[user_id] = "START"

    state = user_state[user_id]

    next_state, protocol_outputs = sm.run_state(state, data)

    user_state[user_id] = next_state

    return protocol_outputs




#region Protocols

# Protocols must receive a dict with data like {message:"hi"} and return a list of pairs (type, content)
# Transitions must receive a dict with data and return a tuple (next_state_name, list of pairs (type, content))

def test_entry(data):
    keyboard = [KeyboardButton(text="Option 1"), KeyboardButton(text="Option 2")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    return [("text", "You are in test state now"), ("keyboard", reply_markup)]

def test_core(data):
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

    return [("quiz", quiz)]

def test_transition(data):
    return "MAIN", []




def start_entry(data):
    return []

def start_protocol(data):
    return [("text", "Welcome to the game!")]

def start_core(data):
    return []

def start_transition(data):
    return "MAIN", []



def main_entry(data):
    keyboard = [KeyboardButton(text="Host a game"), KeyboardButton(text="Join a game"), KeyboardButton(text="Settings")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    return [("text", "Welcome to the main menu!"), ("keyboard", reply_markup)]

def main_core(data):
    return []

def main_transition(data):
    message = data.get("message")

    if message == "Host a game":
        return "CREATE", []
    
    elif message == "Join a game":
        return "JOIN", []
    
    elif message == "Settings":
        return "SETTINGS", []
    
    elif message == "TEST":
        return "TEST", []
    
    else:
        return "MAIN", [("text", "Invalid option. Please choose again.")]



def create_entry(data):
    return [("text", "You have chosen to create a game. Please enter the game name:")]

def create_core(data):
    #TASK Create hash generation for game codes
    return []

def create_transition(data):
    message = data.get("message")
    game_name = message.strip()

    if game_name in game_names:
        return "CREATE", [("text", "A game with this name already exists. Please choose a different name")]
    else:
        game_names.append(game_name)
        return "WAITROOM", [("text", f"You have successfully created the game: {game_name}")]
    


def join_entry(data):
    return [("text", "You have chosen to join a game. Please enter the game code:")]

def join_core(data):
    return []

def join_transition(data):
    message = data.get("message")
    game_code = message.strip()

    if game_code in game_names:
        return "WAITROOM", [("text", f"You have successfully joined the game: {game_code}")]
    else:
        return "JOIN", [("text", "Invalid game code. Please try again")]
    


def settings_entry(data):
    return [("text", "Settings are not implemented yet.")]

def settings_core(data):
    return []

def settings_transition(data):
    return "MAIN", []



def waitroom_entry(data):
    keyboard = [KeyboardButton(text="Leave Game")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    return [("text", "You are now in the wait room. Please wait for the game to start"), ("keyboard", reply_markup)]

def waitroom_core(data):
    return []

def waitroom_transition(data):
    message = data.get("message")

    if message == "Leave Game":
        return "MAIN", [("text", "You have left the game")]
    else:
        return "WAITROOM", [("text", "Waiting for the game to start...")]