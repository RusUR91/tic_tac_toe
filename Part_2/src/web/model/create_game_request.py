class CreateGameRequest:
    def __init__(self, mode: str = 'with_computer'):
        self.mode = mode