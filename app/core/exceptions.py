class AppException(Exception):
    """Exceção base da aplicação."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseConnectionError(AppException):
    """Erro de conexão com o banco de dados."""

    def __init__(self, message: str = "Erro ao conectar com o banco de dados.") -> None:
        super().__init__(message=message, status_code=503)


class NotFoundException(AppException):
    """Recurso não encontrado."""

    def __init__(self, message: str = "Recurso não encontrado.") -> None:
        super().__init__(message=message, status_code=404)
