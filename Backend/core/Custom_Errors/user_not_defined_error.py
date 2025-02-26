
class UserNotDefinedError(Exception):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field

    def __str__(self):
        return f"User Not Defined Error : {self.args[0]}"