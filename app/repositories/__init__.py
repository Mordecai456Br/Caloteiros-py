from app.repositories.installment_repository import InstallmentRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.loan_request_repository import LoanRequestRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
    "LoanRequestRepository",
    "LoanRepository",
    "InstallmentRepository",
    "PaymentRepository",
]
