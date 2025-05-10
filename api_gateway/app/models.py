class CurrentUser:
    def __init__(self, identity=None):
        self.identity = identity
        self.is_authenticated = identity is not None

    def __repr__(self):
        return f"<CurrentUser {self.identity}>"
    
    def __str__(self):
        return f"{self.identity}"