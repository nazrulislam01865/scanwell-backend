class AppException(Exception):
    code = "APPLICATION_ERROR"
    message = "The request could not be completed."
    status_code = 400

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
