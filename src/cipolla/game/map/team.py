class Team(object):
    def __init__(self, team_id: int, name: str) -> None:
        self.id = team_id
        self.name = name
        
        self.score = 0
        self.oflags = 0
        self.frags = 0
