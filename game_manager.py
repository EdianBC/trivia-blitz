import trivia
import asyncio
import state_machine_applied as sma

class game_room:
    def __init__(self):
        self.players = []
        self.game_on = False
        self.results = {}
        self.submissions = {}

    async def start_game(self):
        self.game_on = True

    async def add_player(self, player_name):
        if player_name not in self.players:
            self.players.append(player_name)

    async def remove_player(self, player_name):
        if player_name in self.players:
            self.players.remove(player_name)

    async def submit_answer(self, player_name, answer):
        self.submissions[player_name] = answer
    
    async def clear_submissions(self):
        self.submissions = {}

    async def list_players(self):
        return self.players
    

game_rooms = {}


async def fetch_categories(trivia_database):
    return await trivia.fetch_categories_async(trivia_database=trivia_database)

async def fetch_questions(trivia_database, amount=10, category=None, difficulty=None, qtype=None):
    return await trivia.fetch_questions_async(trivia_database=trivia_database, amount=amount, category=category, difficulty=difficulty, qtype=qtype)

async def add_player_to_room(player_name, room_id):
    print(f"Adding player {player_name} to room {room_id}")#p
    room = game_rooms.get(room_id)
    if room:
        await room.add_player(player_name)
        print(f"Current players in room {room_id}: {room.players}")#p
    
async def remove_player_from_room(player_name, room_id):
    room = game_rooms.get(room_id)
    if room:
        await room.remove_player(player_name)

async def submit_answer_in_room(player_name, room_id, answer):
    room = game_rooms.get(room_id)
    if room:
        await room.submit_answer(player_name, answer)

async def game_master(room_id):
    
    room = game_rooms[room_id]

    while not room.game_on:
        #TASK actualizar estado de la sala
        await asyncio.sleep(0.1)

    print(room.players)
    for player in room.players:
        room.results[player] = 0
        data = {"id": player, "move_on": True}
        await sma.task_queue.put((player, ("run", data)))

    questions = await fetch_questions("OpenTDB", amount=10, category=None, difficulty=None, qtype=None)

    for question in questions:
        for player in room.players:
            await sma.task_queue.put((player, ("text", question["question"])))
        await asyncio.sleep(5)
        for submission in room.submissions.items():
            player, answer = submission
            if answer == question["correct_answer"]:
                room.results[player] += 1
        await room.clear_submissions()
    
    inform = await get_result_inform(room_id)
    for player in room.players:
        await sma.task_queue.put((player, ("text", inform)))

    for player in room.players:
        data = {"id": player, "game_over": True}
        await sma.task_queue.put((player, ("run", data)))


async def game_room_exists(room_id):
    return room_id in game_rooms

async def start_game_in_room(room_id):
    room = game_rooms.get(room_id)
    if room:
        await room.start_game()

async def get_result_inform(room_id):
    room = game_rooms[room_id]
    result_text = "🏆 Game Results 🏆\n\n"
    
    # Sort players by score in descending order
    sorted_results = sorted(room.results.items(), key=lambda x: x[1], reverse=True)
    
    # Add emojis for top 3 players
    medals = ["🥇", "🥈", "🥉"]
    for index, (player, score) in enumerate(sorted_results):
        medal = medals[index] if index < len(medals) else "🎮"  # Use a controller emoji for others
        result_text += f"{medal} {player}: {score} points\n"
    
    return result_text


