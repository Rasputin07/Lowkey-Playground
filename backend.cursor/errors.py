"""One error type + one JSON shape for every failure: {"error": {"code", "message"}}."""


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details

    def to_response(self):
        body = {"error": {"code": self.code, "message": self.message}}
        if self.details:
            body["error"]["details"] = self.details
        return body, self.status


def bad_request(message, details=None):
    return AppError(400, "bad_request", message, details)


def forbidden(message="You do not have access to this resource."):
    return AppError(403, "forbidden", message)


def not_found(message="Resource not found."):
    return AppError(404, "not_found", message)
