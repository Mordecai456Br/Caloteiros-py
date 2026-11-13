from typing import Any


class AppException(Exception):
    """Exceção base da aplicação no padrão de erro HTTP estruturado."""

    def __init__(
        self,
        message: str,
        code: str = "BAD_REQUEST",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ValidationException(AppException):
    """Dados inválidos enviados pelo cliente (422)."""

    def __init__(
        self,
        message: str = "Dados inválidos.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class BusinessRuleException(AppException):
    """Regra de negócio violada (422)."""

    def __init__(
        self,
        message: str = "Regra de negócio violada.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            status_code=422,
            details=details,
        )


class NotFoundException(AppException):
    """Recurso não encontrado (404)."""

    def __init__(
        self,
        message: str = "Recurso não encontrado.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictException(AppException):
    """Conflito de dados (409)."""

    def __init__(
        self,
        message: str = "Conflito de dados.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            status_code=409,
            details=details,
        )


class UnauthorizedException(AppException):
    """Não autenticado (401)."""

    def __init__(
        self,
        message: str = "Não autenticado.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details,
        )


class ForbiddenException(AppException):
    """Sem permissão (403)."""

    def __init__(
        self,
        message: str = "Sem permissão para executar esta ação.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class DatabaseConnectionError(AppException):
    """Banco de dados indisponível (503)."""

    def __init__(
        self,
        message: str = "Banco de dados indisponível no momento.",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=503,
            details=details,
        )
