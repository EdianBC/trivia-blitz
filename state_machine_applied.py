from telegram import ReplyKeyboardMarkup, KeyboardButton
import asyncio
import random
import game_manager as gm
import state_machine as sm


task_queue = asyncio.Queue()
user_state = {}
user_vault = {}


# async def games_monitor():
#     while True:
#         print(f"Games running now: {list(gm.game_rooms.keys())}")
#         await asyncio.sleep(3)


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
    await sm.add_state("PRIVACY", None, None, privacy_transition)
    await sm.add_state("JOIN", join_entry, None, join_transition)
    await sm.add_state("USERNAMEJOIN", None, None, usernamejoin_transition)
    await sm.add_state("SEARCH", search_entry, None, search_transition)
    await sm.add_state("SETTINGS", settings_entry, None, settings_transition)
    await sm.add_state("WAITROOM", waitroom_entry, None, waitroom_transition)
    await sm.add_state("ADMWAITROOM", admin_waitroom_entry, None, admin_waitroom_transition)
    await sm.add_state("ANNOUNCEMENT", None, None, announcement_transition)
    await sm.add_state("GAME", None, None, game_transition)
    
    # asyncio.create_task(games_monitor())
    asyncio.create_task(public_game_rooms_updater())

async def run_state_machine_step(data: dict) -> list:
    user_id = data.get("id")
    if user_id not in user_state:
        user_state[user_id] = "START"
        user_vault[user_id] = {}

    state = user_state[user_id]
    next_state = await sm.run_state(state, data)
    user_state[user_id] = next_state

searching_users = []
async def public_game_rooms_updater():
    while True:
        if not searching_users:
            await asyncio.sleep(1)
            continue
        public_games_text = "🌐 *Public Games:*\n\n"
        public_games = await gm.get_public_games_info()
        
        if public_games:
            for game in public_games:
                room_id = game["room_id"]
                num_of_players = game["num_of_players"]
                admin = game["admin"]
                public_games_text += f"📺 Room: `{room_id}` | 👑 Host: *{admin}* | 👥 Players: *{num_of_players}* | ⚡️ Join: /join\\_{room_id}\n"
        
        else:
            public_games_text += "🌀 No public games available at the moment. Check back later! 🕒"

        # Update all users in the SEARCH state
        for user_id, state in user_state.items():
            if state == "SEARCH":
                await task_queue.put((user_id, ("edittext", public_games_text)))

        await asyncio.sleep(1)


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
    id = data["id"]
    if id in searching_users:
        searching_users.remove(id)
    username = user_vault[data["id"]].setdefault('username', f'Player{random.randint(1000,9999)}')
    room_id = user_vault[data["id"]].get('game_room_id', None)
    if room_id:
        await gm.remove_player_from_room(username, room_id)
    await task_queue.put((data["id"], ("text", f"Welcome to the game, *{user_vault[data["id"]]["username"]}*!")))
    # await task_queue.put((data["id"], ("run", data)))

async def start_transition(data):
    return "MAIN"


#region MAIN MENU
async def main_entry(data):
    user_vault[data["id"]].setdefault('username', f'Player{random.randint(1000, 9999)}')
    keyboard = [[KeyboardButton(text="🎮 Host a Game"), KeyboardButton(text="🕹️ Join a Game")],
                [KeyboardButton(text="🔍 Search for Games"), KeyboardButton(text="⚙️ Game Settings")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "🌟 Welcome to the *Main Menu*! 🌟", reply_markup)))

async def main_transition(data):
    message = data.get("message")

    if message == "🎮 Host a Game":
        return "CREATE"
    elif message == "🕹️ Join a Game":
        return "JOIN"
    elif message == "⚙️ Game Settings":
        return "SETTINGS"
    elif message == "🔍 Search for Games":
        return "SEARCH"
    elif message == "TEST":
        return "TEST"
    else:
        await task_queue.put((data["id"], ("text", "Invalid option")))
        return "MAIN"


#region CREATION MENU
async def create_entry(data):
    keyboard = [[KeyboardButton(text="🎮 Create Game"), KeyboardButton(text="🏷️ Change Room Name")],
                [KeyboardButton(text="❓ Set Number of Questions"), KeyboardButton(text="🎯 Adjust Difficulty")],
                [KeyboardButton(text="⏱️ Set Time to Answer"), KeyboardButton(text="👤 Update Username")],
                [KeyboardButton(text="🔒 Set Room Privacy"), KeyboardButton(text="🔙 Back to Main Menu")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "🎉 Welcome to the *Game Creation Menu*! 🎉", reply_markup)))

    game_room_name = user_vault[data["id"]].setdefault('game_room_id', f'MyGameRoom{random.randint(1000,9999)}')
    number_of_questions = user_vault[data["id"]].setdefault('number_of_questions', 20)
    difficulty = user_vault[data["id"]].setdefault('difficulty', 'Easy')
    clues = user_vault[data["id"]].setdefault('clues', True)
    time_to_answer = user_vault[data["id"]].setdefault('time_to_answer', 20)
    username = user_vault[data["id"]].setdefault('username', f'Player{random.randint(1000,9999)}')#Actually all that random thing could be removed
    privacy = user_vault[data["id"]].setdefault('privacy', 'Public')
    current_settings = (
    f"🎮 *Current Game Settings* 🎮\n\n"
    f"🏷️ *Name:* {game_room_name}\n"
    f"❓ *Number of Questions:* {number_of_questions}\n"
    f"🎯 *Difficulty:* {difficulty}{" (with clues)" if clues else " (without clues)"}\n"
    f"⏱️ *Time to Answer:* {time_to_answer} seconds\n"
    f"🔒 *Privacy:* {privacy}\n"
    f"👤 *Username:* {username}\n"
    )
    await task_queue.put((data["id"], ("text", current_settings)))

async def create_transition(data):
    message = data.get("message")

    if message == "🔙 Back to Main Menu":
        return "MAIN"
    elif message == "❓ Set Number of Questions":
        await task_queue.put((data["id"], ("textnokeyboard", "📝 How many questions do you want in your game?")))
        return "NUMQUESTIONS"
    elif message == "🎯 Adjust Difficulty":
        difficulty_keyboard = [[KeyboardButton(text="Easy 🟢"), KeyboardButton(text="Medium 🟡"), KeyboardButton(text="Hard 🔴")],
                               [KeyboardButton(text="Easy (without clues) 🟢"), KeyboardButton(text="Medium (without clues) 🟡"), KeyboardButton(text="Hard (without clues) 🔴")]]
        reply_markup = ReplyKeyboardMarkup(difficulty_keyboard, resize_keyboard=True)
        text = "🎯 Choose Your Difficulty Level!\n\n🟢 *Easy*: For a relaxed experience.\n🟡 *Medium*: A balanced challenge.\n🔴 *Hard*: Only for the brave!\n\n"
        await task_queue.put((data["id"], ("textkeyboard", text, reply_markup)))
        return "DIFFICULTY"
    elif message == "⏱️ Set Time to Answer":
        await task_queue.put((data["id"], ("textnokeyboard", "⏱️ How many seconds do you need?")))
        return "TIMETOANSWER"
    elif message == "👤 Update Username":
        await task_queue.put((data["id"], ("textnokeyboard", "👤 What should I call you?")))
        return "USERNAME"
    elif message == "🏷️ Change Room Name":
        await task_queue.put((data["id"], ("textnokeyboard", "🏷️ What will be the name of your game room?")))
        return "GAMEROOMNAME"
    elif message == "🔒 Set Room Privacy":
        privacy_keyboard = [[KeyboardButton(text="Public 🌐"), KeyboardButton(text="Private 🔐")]]
        reply_markup = ReplyKeyboardMarkup(privacy_keyboard, resize_keyboard=True)
        await task_queue.put((data["id"], ("textkeyboard", "🔒 Would you like your game room to be *Public* (anyone can join) or *Private* (only invited players can join)?", reply_markup)))
        return "PRIVACY"
    elif message == "🎮 Create Game":
        game_room_id = user_vault[data["id"]].get('game_room_id')
        if await gm.game_room_exists(game_room_id):
            await task_queue.put((data["id"], ("text", f"⚠️ *Oops!* A game with the name '{game_room_id}' already exists")))
            return "CREATE"
        else:
            num_of_questions = user_vault[data["id"]].get('number_of_questions')
            difficulty = user_vault[data["id"]].get('difficulty')
            clues = user_vault[data["id"]].get('clues', True)
            time_to_answer = user_vault[data["id"]].get('time_to_answer')
            privacy = user_vault[data["id"]].get('privacy', 'Public')
            await gm.create_game_room(game_room_id, num_of_questions, difficulty, time_to_answer, privacy, clues)
            await gm.set_admin_in_room(user_vault[data["id"]]['username'], data["id"], game_room_id)
            await task_queue.put((data["id"], ("text", f"🎉 *Success!* Your game room has been created\n\n`{game_room_id}`\n\nInvite your friends and get ready to play! 🚀")))
            return "ADMWAITROOM"
    else:
        await task_queue.put((data["id"], ("text", "❌ Invalid option")))
        return "CREATE"

async def numquestions_transition(data):
    message = data.get("message")
    if message.isdigit() and int(message) > 0:
        user_vault[data["id"]]['number_of_questions'] = int(message)
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "❌ *Oops!* That doesn't look like a valid number")))
        return "NUMQUESTIONS"
    
async def difficulty_transition(data):
    message = data.get("message")
    if message in ["Easy 🟢", "Medium 🟡", "Hard 🔴"]:
        # Extract the difficulty level without the emoji
        user_vault[data["id"]]['difficulty'] = message.split()[0]
        return "CREATE"
    elif message in ["Easy (without clues) 🟢", "Medium (without clues) 🟡", "Hard (without clues) 🔴"]:
        user_vault[data["id"]]['difficulty'] = message.split()[0]
        user_vault[data["id"]]['clues'] = False
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "❌ Invalid choice!")))
        return "DIFFICULTY"
    
async def timetoanswer_transition(data):
    message = data.get("message")
    if message.isdigit() and int(message) > 0:
        user_vault[data["id"]]['time_to_answer'] = int(message)
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "❌ *Oops!* That doesn't look like a valid time")))
        return "TIMETOANSWER"
    
async def username_transition(data):
    message = data.get("message")
    if message:
        user_vault[data["id"]]['username'] = message
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "❌ *Oops!* That doesn't look like a valid username")))
        return "USERNAME"
    
async def gameroomname_transition(data):
    message = data.get("message")
    if message:
        user_vault[data["id"]]['game_room_id'] = message
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "❌ *Oops!* That doesn't look like a valid time")))
        return "GAMEROOMNAME"
    
async def privacy_transition(data):
    message = data.get("message")
    if message in ["Public 🌐", "Private 🔐"]:
        user_vault[data["id"]]['privacy'] = message.split()[0]
        return "CREATE"
    else:
        await task_queue.put((data["id"], ("text", "❌ Invalid choice!")))
        return "PRIVACY"    



#region SEARCH MENU
async def search_entry(data):
    keyboard = [KeyboardButton(text="🔙 Back to Main Menu")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "🔍 Welcome to the *Search Menu!* Here you can find public game rooms to join and compete with other players\n\nSimply *copy and paste* the name of the room you'd like to join, or tap *Back to Main Menu* to return. 🚀", reply_markup)))
    await task_queue.put((data["id"], ("editabletext", "🌐 *Public Games:*\n\n🌀 Loading available game rooms...")))
    searching_users.append(data["id"])

async def search_transition(data):
    message = data.get("message")

    if message == "🔙 Back to Main Menu":
        searching_users.remove(data["id"])
        return "MAIN"
    else:
        room_name = message.strip()
        can_join = await gm.can_player_join(room_name, user_vault[data["id"]]['username'])
        if can_join == "OK":
            await gm.add_player_to_room(user_vault[data["id"]]['username'], data["id"], room_name)
            user_vault[data["id"]]['game_room_id'] = room_name
            await task_queue.put((data["id"], ("text", f"🎉 *Success!* You've joined the game room: *{room_name}*")))
            return "WAITROOM"




#region JOIN MENU
async def join_entry(data):
    keyboard = [KeyboardButton(text="👤 Change Username"), KeyboardButton(text="🔙 Back to Main Menu")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)

    username = user_vault[data["id"]].setdefault('username', f'Player{random.randint(1000,9999)}') #Actually all that random thing could be removed
    text = f"👋 Welcome to the *Join Menu*!\n\n✨ You are currently logged in as: *'{username}'*\n\nIf you'd like to change your username, tap *Change Username* below. Otherwise, type the name of the game room you want to join and let's get started! 🚀" 
    await task_queue.put((data["id"], ("textkeyboard", text, reply_markup)))

async def join_transition(data):
    message = data.get("message")

    if message == "🔙 Back to Main Menu":
        return "MAIN"
    elif message == "👤 Change Username":
        await task_queue.put((data["id"], ("textnokeyboard", "👤 What should I call you?")))
        return "USERNAMEJOIN"
    else:
        game_room_id = message.strip()
        can_join = await gm.can_player_join(game_room_id, user_vault[data["id"]]['username']) #"Hey bro, room id and username are swapped" Yeah right get lost punk
        if can_join == "OK":
            await gm.add_player_to_room(user_vault[data["id"]]['username'], data["id"], game_room_id)
            user_vault[data["id"]]['game_room_id'] = game_room_id
            await task_queue.put((data["id"], ("text", f"🎉 *Success!* You've joined the game room: *{game_room_id}*")))
            return "WAITROOM"
        elif can_join == "NOEXIST":
            await task_queue.put((data["id"], ("text", "❌ That game room does not exist mate, get real!")))
            return "JOIN"
        elif can_join == "TAKEN":
            await task_queue.put((data["id"], ("text", "❌ That username is already taken in this room, choose another one!")))
            return "JOIN"
        elif can_join == "ONGOING":
            await task_queue.put((data["id"], ("text", "❌ The game in that room is already ongoing, you can't join now!")))
            return "JOIN"
        else:
            await task_queue.put((data["id"], ("text", "❌ Unable to join the game room due to an unknown error")))
            return "JOIN"

async def usernamejoin_transition(data):
    message = data.get("message")
    if message:
        user_vault[data["id"]]['username'] = message
        return "JOIN"
    else:
        await task_queue.put((data["id"], ("text", "❌ *Oops!* That doesn't look like a valid username")))
        return "USERNAME"
    

# SETTINGS
async def settings_entry(data):
    await task_queue.put((data["id"], ("textnokeyboard", "👨‍💻 Settings are not implemented yet 🛠")))
    await task_queue.put((data["id"], ("run", data)))

async def settings_transition(data):
    return "MAIN"


#region WAITING ROOM AND GAME
async def waitroom_entry(data):
    keyboard = [KeyboardButton(text="🐔 Leave Game")]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
    await task_queue.put((data["id"], ("textkeyboard", "⏳ Welcome to the *Waiting Room*! ⏳\n\nPlease wait for the host to start the game 🎮", reply_markup)))
    await task_queue.put((data["id"], ("editabletext", "🌀 Loading players...")))

async def waitroom_transition(data):
    if data.get("move_on", False):
        keyboard = [KeyboardButton(text="🐔 Abandon Game")]
        reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
        await task_queue.put((data["id"], ("textkeyboard", "🚀 *The game is starting!* 🚀", reply_markup)))
        return "GAME"
    if data.get("game_cancelled", False):
        await task_queue.put((data["id"], ("text", "❌ The game has been *cancelled* by the host 🤬")))
        return "MAIN"
    
    message = data.get("message")

    if message == "🐔 Leave Game":
        await gm.remove_player_from_room(user_vault[data["id"]]['username'], user_vault[data["id"]]['game_room_id'])
        await task_queue.put((data["id"], ("text", "🐔 You have left the game")))
        return "MAIN"
    else:
        await task_queue.put((data["id"], ("text", "⏳ Waiting for the game to start")))
        return "WAITROOM"
    

# ADMWAITROOM
async def admin_waitroom_entry(data):
    keyboard = [[KeyboardButton(text="🚀 Start Game"), KeyboardButton(text="📢 Make Announcement")], [KeyboardButton(text="🚪 Cancel Game")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    text = "👑 Welcome to the *Admin Waiting Room*! 👑\n\nYou are the host of this game. Once all players have joined, you can start the game by tapping *Start Game* 🎮\n\n"
    await task_queue.put((data["id"], ("textkeyboard", text, reply_markup)))
    await task_queue.put((data["id"], ("editabletext", "🌀 Loading players...")))

async def admin_waitroom_transition(data):
    message = data.get("message")

    if message == "🚀 Start Game":
        keyboard = [KeyboardButton(text="🐔 Abandon Game")]
        reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True)
        await task_queue.put((data["id"], ("textkeyboard", "🚀 *The game is starting!* 🚀", reply_markup)))
        await gm.start_game_in_room(user_vault[data["id"]]['game_room_id'])
        return "GAME"
    elif message == "🚪 Cancel Game":
        await gm.set_game_cancelled(user_vault[data["id"]]['game_room_id'])
        await task_queue.put((data["id"], ("text", "❌ You have cancelled the game")))
        return "MAIN"
    elif message == "📢 Make Announcement":
        await task_queue.put((data["id"], ("textnokeyboard", "📢 What announcement would you like to make to all players?")))
        return "ANNOUNCEMENT"
    else:
        await task_queue.put((data["id"], ("text", "⏳ Waiting for players to join...")))
        return "ADMWAITROOM"

async def announcement_transition(data):
    message = data.get("message")
    if message:
        game_room_id = user_vault[data["id"]]['game_room_id']
        room = gm.game_rooms.get(game_room_id)
        if room:
            for player_username, player_id in room.players.items():
                if player_username != user_vault[data["id"]]['username']:
                    await task_queue.put((player_id, ("text", f"📢 *Announcement from Host:* {message}")))
            await task_queue.put((data["id"], ("text", "✅ Announcement sent to all players.")))
            return "ADMWAITROOM"
        else:
            await task_queue.put((data["id"], ("text", "❌ Unable to send announcement. Game room not found.")))
            return "ADMWAITROOM"
    else:
        await task_queue.put((data["id"], ("text", "❌ *Oops!* Announcement cannot be empty.")))
        return "ANNOUNCEMENT"


# GAME
async def game_transition(data):
    if data.get("game_over", False):
        return "MAIN"
    
    message = data.get("message")
    if message == "🐔 Abandon Game":
        await gm.remove_player_from_room(user_vault[data["id"]]['username'], user_vault[data["id"]]['game_room_id'])
        await task_queue.put((data["id"], ("text", "🐔🐔🐔 You have *abandoned* the game 🐔🐔🐔")))
        return "MAIN"
    else:
        print(f"Submitting answer from {user_vault[data['id']]['username']} in room {user_vault[data['id']]['game_room_id']}: {message}\nFull data:{data}")
        if message:
            await gm.submit_answer_in_room(user_vault[data["id"]]['username'], user_vault[data["id"]]['game_room_id'], message)
    return "GAME"

#endregion