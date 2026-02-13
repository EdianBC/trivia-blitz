import trivia
import asyncio
import random
from telegram import ReplyKeyboardMarkup, KeyboardButton
import state_machine_applied as sma
import re
import unicodedata
import jellyfish


class game_room:
    def __init__(self):
        self.players = {}
        self.admin = None
        self.game_on = False
        self.game_cancelled = False
        self.results = {}
        self.submissions = {}

    async def start_game(self):
        self.game_on = True

    async def add_player(self, player_name, player_id):
        self.players[player_name] = player_id

    async def set_admin(self, player_name):
        self.admin = player_name

    async def remove_player(self, player_name):
        if player_name in self.players:
            self.players.pop(player_name)

    async def submit_answer(self, player_name, answer):
        self.submissions[player_name] = answer
    
    async def clear_submissions(self):
        self.submissions = {}
    

game_rooms = {}
public_game_rooms = []


#TASK Agregar manejo de errores por si la API no responde
async def fetch_categories(trivia_database):
    return await trivia.fetch_categories_async(trivia_database=trivia_database)

async def fetch_questions(trivia_database, amount=10, category=None, difficulty=None, qtype=None):
    return await trivia.fetch_questions_async(trivia_database=trivia_database, amount=amount, category=category, difficulty=difficulty, qtype=qtype)

async def get_public_games_info():
    info = []
    for room_id in public_game_rooms:
        room = game_rooms.get(room_id)
        if room:
            info.append({"room_id": room_id, "num_of_players": len(room.players), "admin": room.admin})
    return info

async def add_player_to_room(player_name, player_id, room_id):
    print(f"Adding player {player_name} to room {room_id}")#p
    room = game_rooms.get(room_id)
    if room:
        await room.add_player(player_name, player_id)
        print(f"Current players in room {room_id}: {room.players}")#p

async def set_admin_in_room(player_name, player_id, room_id):
    room = game_rooms.get(room_id)
    if room:
        await room.set_admin(player_name)
        await room.add_player(player_name, player_id)
    
async def remove_player_from_room(player_name, room_id):
    room = game_rooms.get(room_id)
    if room:
        await room.remove_player(player_name)

async def submit_answer_in_room(player_name, room_id, answer):
    room = game_rooms.get(room_id)
    if room:
        await room.submit_answer(player_name, answer)

async def set_game_cancelled(room_id):
    room = game_rooms.get(room_id)
    if room:
        room.game_cancelled = True

async def create_game_room(room_id, num_of_questions=10, difficulty=None, time_to_answer=15, privacy=False, clues=True, categories=None):
    game_rooms[room_id] = game_room()
    if privacy == "Public":
        public_game_rooms.append(room_id)
    asyncio.create_task(game_master(room_id, num_of_questions, difficulty, time_to_answer, clues, categories))

async def game_room_exists(room_id):
    return room_id in game_rooms

async def start_game_in_room(room_id):
    room = game_rooms.get(room_id)
    if room:
        await room.start_game()

async def can_player_join(room_id, username):
    room = game_rooms.get(room_id)
    if room:
        if room.game_on:
            return "ONGOING"
        if username in room.players:
            return "TAKEN"
        return "OK"
    return "NOEXIST"    



#region Game Master
async def game_master(room_id, num_of_questions=10, difficulty=None, time_per_question=15, use_clues=True, categories=None):
    room = game_rooms[room_id]
    last_update_time = asyncio.get_event_loop().time()
    while not room.game_on:
        # Check if the game was cancelled
        if room.game_cancelled:
            for player_username, player_id in room.players.items():
                if player_username != room.admin:
                    data = {"id": player_id, "game_cancelled": True}
                    await sma.task_queue.put((player_id, ("run", data)))
            game_rooms.pop(room_id, None)
            return
        
        # Update the waiting message every second
        if asyncio.get_event_loop().time() - last_update_time >= 1:
            text = f"🎽 *Current players ({len(room.players)})*:\n\n" + "\n".join([f"{player}" for player in room.players.keys()])
            # text_for_admin = f"🎽 *Current players ({len(room.players)})*:\n\n" + "\n".join([f"{player}" for player in room.players.keys()])
            for player_username, player_id in room.players.items():
                # if player_username == room.admin:
                #     await sma.task_queue.put((player_id, ("edittext", text_for_admin)))
                # else:
                #     await sma.task_queue.put((player_id, ("edittext", text)))
                await sma.task_queue.put((player_id, ("edittext", text)))
            last_update_time = asyncio.get_event_loop().time()
        await asyncio.sleep(0.1)

    # Send signal to all players that the game is starting (except admin who already knows)
    if room_id in public_game_rooms:
        public_game_rooms.remove(room_id)
    print(room.players)
    for player_username, player_id in room.players.items():
        if player_username != room.admin:
            data = {"id": player_id, "move_on": True}
            await sma.task_queue.put((player_id, ("run", data)))
        room.results[player_username] = 0

    # Main loop for questions
    questions = await fetch_questions("OpenTriviaQA", amount=num_of_questions, category=categories)
    await asyncio.sleep(1)

    for index, question in enumerate(questions):
        if len(room.players) == 0:
            game_rooms.pop(room_id, None)
            return

        for player_username, player_id in room.players.items():
            possible_answers = question["incorrect_answers"] + [question["correct_answer"]]
            random.shuffle(possible_answers)
            if use_clues:
                keyboard = [[KeyboardButton(text=answer)] for answer in possible_answers] + [[KeyboardButton(text=" ")], [KeyboardButton(text=" ")]] + [[KeyboardButton(text="🐔 Abandon Game")]]
            else:
                keyboard = [[KeyboardButton(text="🐔 Abandon Game")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            if "one of these" in question["question"].lower() or "three of these" in question["question"].lower() or "which of the following" in question["question"].lower():
                possibilities = ", ".join([f"{answer}" for answer in possible_answers])
                question["question"] += f" {possibilities}"
            await sma.task_queue.put((player_id, ("textkeyboard", f"❓ *QUESTION ({index+1}/{num_of_questions}):*\n\n{question["question"]}", reply_markup)))
            await sma.task_queue.put((player_id, ("editabletext", f"⏳ You have *{time_per_question} second{'' if time_per_question==1 else 's'}* left")))

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < time_per_question:
            if len(room.submissions) >= len(room.players):
                break
            for player_username, player_id in room.players.items():
                time_left = time_per_question - int(asyncio.get_event_loop().time() - start_time)
                await sma.task_queue.put((player_id, ("edittext", f"⏳ You have *{time_left} second{'' if time_left==1 else 's'}* left")))
            await asyncio.sleep(1)

        winners_of_the_round = []
        for submission in room.submissions.items():
            player, answer = submission
            player_id = room.players[player]
            if use_clues:
                if answer == question["correct_answer"]:
                    room.results[player] += 1
                    await sma.task_queue.put((player_id, ("text", "✅ *Correct answer!* 🎉")))
                    winners_of_the_round.append(player)
                else:
                    await sma.task_queue.put((player_id, ("text", f"❌ *Wrong answer* 😞")))
            else:
                if validate_answer(answer, question["correct_answer"]):
                    room.results[player] += 1
                    await sma.task_queue.put((player_id, ("text", "✅ *Correct answer!* 🎉")))
                    winners_of_the_round.append(player)
                else:
                    await sma.task_queue.put((player_id, ("text", f"❌ *Wrong answer* 😞")))

        await room.clear_submissions()

        for player_username, player_id in room.players.items():
            if player_username not in winners_of_the_round or not use_clues:
                await sma.task_queue.put((player_id, ("text", f"📢 The correct answer was: {question['correct_answer']} ✅")))
            await sma.task_queue.put((player_id, ("text", f"🏆 Winner{'s' if len(winners_of_the_round)>=2 else ''} of this round: {', '.join(winners_of_the_round) if winners_of_the_round else 'No one'}")))
        winners_of_the_round = []
        await asyncio.sleep(4)

    inform = await get_result_inform(room_id)
    for player_username, player_id in room.players.items():
        await sma.task_queue.put((player_id, ("text", inform)))

    await asyncio.sleep(3)

    for player_username, player_id in room.players.items():
        data = {"id": player_id, "game_over": True}
        await sma.task_queue.put((player_id, ("run", data)))

    game_rooms.pop(room_id, None)


async def get_result_inform(room_id):
    room = game_rooms[room_id]
    result_text = "🏆 Game Results 🏆\n\n"
    
    # Sort players by score in descending order
    sorted_results = sorted(room.results.items(), key=lambda x: x[1], reverse=True)
    
    # Add emojis for top 3 players
    medals = ["🥇", "🥈", "🥉"]
    for index, (player, score) in enumerate(sorted_results):
        medal = medals[index] if index < len(medals) else "🎮"  # Use a controller emoji for others
        result_text += f"{medal} *{player}*: {score} point{'' if score==1 else 's'}\n"
    
    return result_text



def normalize_text(text):
    # 1. Pasar a minúsculas
    text = text.lower()
    
    # 2. Eliminar acentos (NFD descompone caracteres como 'á' en 'a' + '´')
    text = "".join(c for c in unicodedata.normalize('NFD', text) 
                  if unicodedata.category(c) != 'Mn')
    
    # 3. Eliminar artículos comunes (español e inglés)
    stopwords = r'\b(el|la|los|las|un|una|unos|unas|the|a|an)\b'
    text = re.sub(stopwords, '', text)
    
    # 4. Limpiar puntuación y espacios extra
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())
    
    return text

def contains_numbers(text):
    return any(char.isdigit() for char in text)

def validate_answer(answer, ground_truth, threshold=0.85):
    # Normalizamos ambos textos
    clean_user = normalize_text(answer)
    clean_truth = normalize_text(ground_truth)
    
    # --- REGLA DE ORO: EXCEPCIÓN DE NÚMEROS ---
    # Si la respuesta correcta contiene números, buscamos coincidencia exacta de esos números
    truth_numbers = re.findall(r'\d+', ground_truth)
    if truth_numbers:
        user_numbers = re.findall(r'\d+', answer)
        if set(truth_numbers) != set(user_numbers):
            return False # Si los números no coinciden exactamente, falla
            
    # --- VALIDACIÓN 1: Coincidencia Exacta tras normalizar ---
    if clean_user == clean_truth:
        return True
    
    # --- VALIDACIÓN 2: Fonética (Metaphone) ---
    # Útil para "Burj" vs "Bursh" o errores ortográficos por sonido
    if jellyfish.metaphone(clean_user) == jellyfish.metaphone(clean_truth):
        return True
        
    # --- VALIDACIÓN 3: Similitud Jaro-Winkler o Levenshtein ---
    # Jaro-Winkler suele ser mejor para nombres cortos y typos
    similarity = jellyfish.jaro_winkler_similarity(clean_user, clean_truth)
    
    return similarity >= threshold

# --- EJEMPLOS DE USO ---
# print(validate_answer("El Burj Khalifa", "Burj Khalifa")) # True (por normalización)
# print(validate_answer("Bur Kalifa", "Burj Khalifa"))      # True (por fonética/similitud)
# print(validate_answer("En el año 1984", "1984"))          # True (contiene el número)
# print(validate_answer("En el año 1985", "1984"))          # False (número incorrecto)
# print(validate_answer("Mesi", "Messi"))                  # True (typo leve)