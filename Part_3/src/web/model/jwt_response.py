class JwtResponse:
    def __init__(self, token_type: str, access_token: str, refresh_token: str):
        self.token_type = token_type
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def to_dict(self):
        return {
            'token_type': self.token_type,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token
        }