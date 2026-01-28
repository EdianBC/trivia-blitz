class game_room:
    def __init__(self):
        self.players = []

    def add_player(self, player_name):
        if player_name not in self.players:
            self.players.append(player_name)
            return True
        return False

    def remove_player(self, player_name):
        if player_name in self.players:
            self.players.remove(player_name)
            return True
        return False

    def list_players(self):
        return self.players
    
game_rooms = {}