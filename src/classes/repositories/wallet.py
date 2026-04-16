from classes.repositories.base_repository import BaseRepo
from classes.models.wallet import mWallet, mTransaction, mTransactionCategory, mTransfer

class rWallet(BaseRepo):
    """Репозиторий кошельков"""
    def __init__(self, session):
        super().__init__(mWallet, session)


class rTransaction(BaseRepo):
    """Репозиторий транзакций"""
    def __init__(self, session):
        super().__init__(mTransaction, session)


class rTransactionCategory(BaseRepo):
    """Репозиторий категорий транзакций"""
    def __init__(self, session):
        super().__init__(mTransactionCategory, session)


class rTransfer(BaseRepo):
    """Репозиторий переводов"""
    def __init__(self, session):
        super().__init__(mTransfer, session)