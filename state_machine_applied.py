from telegram import ReplyKeyboardMarkup, KeyboardButton

user_state = {}
game_names = []
state_machine = {}




def start_state_machine():
    pass


def run_state_machine_step(user_id: int, message: str) -> list:
    
    if user_id not in user_state:
        user_state[user_id] = "MAIN"
        return ["Welcome to the game! Choose an option: Create a game, Join a game, Settings"]
    
    outputs = []
    state = user_state[user_id]

    if state == "MAIN":
        if message == "Create a game":
            user_state[user_id] = "CREATE"
            outputs.append("You have chosen to create a game. Please enter the game name:")
        elif message == "Join a game":
            user_state[user_id] = "JOIN"
            outputs.append("You have chosen to join a game. Please enter the game code:")
        elif message == "Settings":
            outputs.append("I owe you this feature, brother")
        elif message == "Test":
            user_state[user_id] = "TEST"
            outputs.append("You are in test state now")

    elif state == "CREATE":
        game_name = message.strip()
        if game_name in game_names:
            #The idea is to genererate a unique key for the game here but thats for later. We are using name as key for now
            outputs.append("A game with this name already exists. Please choose a different name")
        else:
            game_names.append(game_name)
            outputs.append(f"You have successfully created the game: {game_name}")
            user_state[user_id] = "MAIN"
            keyboard = [KeyboardButton(text="Create a game"), KeyboardButton(text="Join a game"), KeyboardButton(text="Settings")]
            outputs.append(ReplyKeyboardMarkup([keyboard], resize_keyboard=True))

    elif state == "JOIN":
        game_code = message.strip()
        if game_code in game_names:
            outputs.append(f"You have successfully joined the game: {game_code}")
            user_state[user_id] = "MAIN"
            keyboard = [KeyboardButton(text="Create a game"), KeyboardButton(text="Join a game"), KeyboardButton(text="Settings")]
            outputs.append(ReplyKeyboardMarkup([keyboard], resize_keyboard=True))
        else:
            outputs.append("Invalid game code. Please try again")

    elif state == "TEST":
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
        
        outputs.append(quiz) 
         
    else:
        outputs.append("Looks like you fucked up. Please try to write a valid command")

    return outputs

