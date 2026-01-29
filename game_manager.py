import trivia
import asyncio
import state_machine_applied as sma

class game_room:
    def __init__(self):
        self.players = {}
        self.game_on = False
        self.game_cancelled = False
        self.results = {}
        self.submissions = {}

    async def start_game(self):
        self.game_on = True

    async def add_player(self, player_name, player_id):
        self.players[player_name] = player_id

    async def remove_player(self, player_name):
        if player_name in self.players:
            del self.players[player_name]

    async def submit_answer(self, player_name, answer):
        self.submissions[player_name] = answer
    
    async def clear_submissions(self):
        self.submissions = {}
    

game_rooms = {}


async def fetch_categories(trivia_database):
    return await trivia.fetch_categories_async(trivia_database=trivia_database)

async def fetch_questions(trivia_database, amount=10, category=None, difficulty=None, qtype=None):
    return await trivia.fetch_questions_async(trivia_database=trivia_database, amount=amount, category=category, difficulty=difficulty, qtype=qtype)

async def add_player_to_room(player_name, player_id, room_id):
    print(f"Adding player {player_name} to room {room_id}")#p
    room = game_rooms.get(room_id)
    if room:
        await room.add_player(player_name, player_id)
        print(f"Current players in room {room_id}: {room.players}")#p
    
async def remove_player_from_room(player_name, room_id):
    room = game_rooms.get(room_id)
    if room:
        await room.remove_player(player_name)

async def submit_answer_in_room(player_name, room_id, answer):
    room = game_rooms.get(room_id)
    if room:
        await room.submit_answer(player_name, answer)


async def game_master(room_id, num_of_questions=10, difficulty=None, time_per_question=15):
    room = game_rooms[room_id]

    while not room.game_on:
        #TASK actualizar estado de la sala
        if room.game_cancelled:
            for player_username, player_id in room.players.items():
                data = {"id": player_id, "game_cancelled": True}
                await sma.task_queue.put((player, ("run", data)))
                game_rooms.pop(room_id, None)
            return
        await asyncio.sleep(0.1)

    print(room.players)
    for player_username, player_id in room.players.items():
        room.results[player_username] = 0
        data = {"id": player_id, "move_on": True}
        await sma.task_queue.put((player_id, ("run", data)))

    questions = await fetch_questions("OpenTDB", amount=num_of_questions, category=None, difficulty=difficulty.lower(), qtype=None)

    for question in questions:
        for player_username, player_id in room.players.items():
            await sma.task_queue.put((player_id, ("text", question["question"])))
        await asyncio.sleep(time_per_question)
        for submission in room.submissions.items():
            player, answer = submission
            player_id = room.players[player]
            winners_of_the_round = []
            if answer == question["correct_answer"]:
                room.results[player] += 1
                await sma.task_queue.put((player_id, ("text", "✅ Correct answer! 🎉")))
                winners_of_the_round.append(player)
            else:
                await sma.task_queue.put((player_id, ("text", "❌ Wrong answer 😞")))

        await room.clear_submissions()

        for player_username, player_id in room.players.items():
            if player_username not in winners_of_the_round:
                await sma.task_queue.put((player_id, ("text", f"The correct answer was: {question['correct_answer']}")))
            await sma.task_queue.put((player_id, ("text", f"Winners of this round: {', '.join(winners_of_the_round) if winners_of_the_round else 'No one'}")))
        winners_of_the_round = []
        await asyncio.sleep(2)

    inform = await get_result_inform(room_id)
    for player_username, player_id in room.players.items():
        await sma.task_queue.put((player_id, ("text", inform)))

    await asyncio.sleep(3)

    for player_username, player_id in room.players.items():
        data = {"id": player_id, "game_over": True}
        await sma.task_queue.put((player_id, ("run", data)))

    game_rooms.pop(room_id, None)


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


