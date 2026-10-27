"""Gestion centralisée des erreurs de l'application."""


class APIError(Exception):
    """Erreur metier / technique portée par l'API REST."""

    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


def api_error(status_code: int, error_code: str, message: str) -> APIError:
    return APIError(status_code=status_code, error_code=error_code, message=message)


def not_found(error_code: str, message: str) -> APIError:
    return APIError(status_code=404, error_code=error_code, message=message)


def forbidden(error_code: str, message: str) -> APIError:
    return APIError(status_code=403, error_code=error_code, message=message)


def unauthenticated(error_code: str = "UNAUTHENTICATED", message: str = "Authentification requise.") -> APIError:
    return APIError(status_code=401, error_code=error_code, message=message)


def conflict(error_code: str, message: str) -> APIError:
    return APIError(status_code=409, error_code=error_code, message=message)


def bad_request(error_code: str, message: str) -> APIError:
    return APIError(status_code=400, error_code=error_code, message=message)


def service_unavailable(error_code: str, message: str) -> APIError:
    return APIError(status_code=503, error_code=error_code, message=message)
