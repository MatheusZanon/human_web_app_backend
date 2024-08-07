class ESocialError(Exception):
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class ESocialConnectionError(ESocialError):
    pass

class ESocialValidationError(ESocialError):
    pass