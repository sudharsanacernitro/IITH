
class UserNotFoundError(Exception):
    def __init__(self, message, user_name=None):
        super().__init__(message)
        self.field = user_name

    def __str__(self):
        return f"User Not Found on DataBase Error : {self.field}"