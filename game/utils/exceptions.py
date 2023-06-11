class CustomBaseException(Exception):
    default_message: str = ""

    def __init__(self, custom_msg: str = ""):
        super().__init__(self.default_message or custom_msg)


class ImproperlyConfigured(CustomBaseException):
    pass


class ShouldBeCalledOnInstanceException(CustomBaseException):
    default_message = "This method should be called on instance of class"


class NoGameFoundException(CustomBaseException):
    default_message = "No game found in DB"
