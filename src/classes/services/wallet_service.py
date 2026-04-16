from classes.uow import UnitOfWork
from classes.models.wallet import mWallet, mTransaction, mTransactionCategory, mTransfer
from classes.schemas.wallet import (
    Direction,
    TransactionAdd,
    TransactionTotalsResultItem,
)

from sqlalchemy import select, func
import datetime


class WalletService:
    """Сервис кошелька. Объединяет кошельки, транзакции, их категории"""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_wallets(self, filters={}):
        """Получает список кошельков"""
        results = []
        with self.uow.start():
            wallet_repo = self.uow.repo("wallet")
            results = wallet_repo.list(filters)

        return results
    
    def delete_wallet(self, wallet_id: int):
        """Удаляет кошелек и связанные с ним транзакции"""
        with self.uow.start():
            wallet_repo = self.uow.repo("wallet")
            
            wallet = wallet_repo.get_by_id(wallet_id)
            if wallet is None:
                raise ValueError("Кошелек не существует")

            wallet_repo.delete(wallet)

        return
    
    def update_wallet(self, wallet_id: int, data: dict):
        """Обновляет кошелек"""
        with self.uow.start():
            wallet_repo = self.uow.repo("wallet")
            
            wallet = wallet_repo.get_by_id(wallet_id)
            if wallet is None:
                raise ValueError("Кошелек не существует")

            result = wallet_repo.update(wallet_id, data)

        return result
    
    def create_wallet(self, name, balance=0):
        """Создает кошелек"""
        with self.uow.start():
            wallet = self.uow.repo("wallet").add(mWallet(name=name, balance=balance))

        return wallet

    def get_wallet(self, wallet_id: int):
        """Получает кошелек"""
        with self.uow.start():
            wallet = self.uow.repo("wallet").get_by_id(wallet_id)

        return wallet

    def delete_transaction(self, _id):
        """Удаляет транзакцию и изменяет баланс кошелька"""

        with self.uow.start():
            repo = self.uow.repo("transactions")
            wallets_repo = self.uow.repo("wallet")
            transaction = repo.get_by_id(_id)
            if transaction is None:
                raise ValueError("Транзакция не существует")

            linked_wallet = wallets_repo.get_by_id(transaction.wallet_id)

            if linked_wallet is None:
                raise ValueError("Кошелек не существует")

            new_balance = linked_wallet.balance
            if transaction.direction == Direction.INCOME:
                new_balance -= transaction.amount
            else:
                new_balance += transaction.amount

            wallets_repo.update(linked_wallet.id, {"balance": new_balance})
            repo.delete(transaction)

    def get_transaction(self, _id):
        """Получает транзакцию по id"""
        with self.uow.start():
            repo = self.uow.repo("transactions")

            transaction = repo.get_by_id(_id)

        return transaction

    def get_transaction_report(self, filters):
        result = []
        with self.uow.start():
            categories_repo = self.uow.repo("transaction_category")
            categories = {}
            for cat in categories_repo.list():
                categories[cat.id] = cat.name
            stmt = (
                select(
                    mTransaction.category_id,
                    mTransaction.direction,
                    func.sum(mTransaction.amount),
                )
                .filter(filters)
                .group_by(mTransaction.category_id, mTransaction.direction)
                .order_by(mTransaction.direction)
            )

            rows = self.uow.session.execute(stmt).fetchall()
            for row in rows:
                result.append(
                    TransactionTotalsResultItem(
                        category=categories.get(row[0], "Переводы между счетами"),
                        direction=row[1],
                        amount=row[2],
                    )
                )

        return result

    def get_transactions(self, page=0, limit=10, filters=None):
        """Получает список транзакций"""
        results = []
        with self.uow.start():

            stmt = (
                select(mTransaction)
                .order_by(mTransaction.timestamp.desc(), mTransaction.id.desc())
                .filter(filters)
            )

            if page:
                stmt = stmt.offset(page * limit)

            if limit:
                stmt = stmt.limit(limit)

            results = self.uow.session.execute(stmt).scalars().all()

        return results

    

    def get_balance(self, wallet_id: int):
        """Возвращает баланс кошелька"""
        with self.uow.start():
            wallet_repo = self.uow.repo("wallet")
            wallet = wallet_repo.get_by_id(wallet_id)

            if wallet is None:
                raise ValueError(f"Кошелька с ID {wallet_id} не существует")

        return round(wallet.balance / 100, 2)

    def create_category(self, name: str, direction: Direction, is_transfer_category=False):
        """Создает категорию"""
        with self.uow.start():
            category_repo = self.uow.repo("transaction_category")
            category = category_repo.add(
                mTransactionCategory(name=name, direction=direction, is_transfer=is_transfer_category)
            )

        return category
    
    def get_categories(self, direction: Direction | None = None):
        """Получает список категорий"""
        results = []
        with self.uow.start():
            stmt = select(mTransactionCategory)

            if direction:
                stmt = stmt.filter(mTransactionCategory.direction == direction)

            stmt = stmt.order_by(mTransactionCategory.id)
            results = self.uow.session.execute(stmt).scalars().all()

        return results

    def delete_category(self, id_) -> None:
        """Удаляет категорию"""
        with self.uow.start():
            category_repo = self.uow.repo("transaction_category")
            category = category_repo.get_by_id(id_)
            if category is None:
                raise ValueError("Категория не существует")

            category_repo.delete(category)

        return
    
    def update_category(self, category_id: int, data: dict):
        """Обновляет категорию"""
        with self.uow.start():
            category_repo = self.uow.repo("transaction_category")
            category = category_repo.get_by_id(category_id)
            if category is None:
                raise ValueError("Категория не существует")

            result = category_repo.update(category_id, data)

        return result

    def transfer_to_wallet(
        self, sender_wallet_id: int, reciever_wallet_id: int, amount: int
    ) -> bool:
        """Переводит на другой кошелек"""
        if amount <= 0:
            raise ValueError("Сумма должна быть больше 0")

        if sender_wallet_id == reciever_wallet_id:
            raise ValueError("Отправитель не может быть получателем")

        with self.uow.start():

            wallet_repo = self.uow.repo("wallet")
            transfer_repo = self.uow.repo("transfer")
            transtaction_repo = self.uow.repo("transactions")
            categories_repo = self.uow.repo("transaction_category")
            sender_wallet = wallet_repo.get_by_id(sender_wallet_id)
            reciever_wallet = wallet_repo.get_by_id(reciever_wallet_id)

            transfer_categories = categories_repo.list({'is_transfer': True})

            category_id = 0

            if transfer_categories:
                category_id = transfer_categories[0].id

            if sender_wallet is None or reciever_wallet is None:
                raise ValueError("Указанный кошелек отсутствует")
            

            if sender_wallet.balance - amount < 0:
                raise ValueError("Недостаточно средств для перевода")

            operation_time = datetime.datetime.now()

            transfer = mTransfer(
                timestamp=operation_time,
                sender_id=sender_wallet_id,
                reciever_id=reciever_wallet_id,
                amount=amount,
            )
            transfer_repo.add(transfer)

            outcome_operation = TransactionAdd(
                timestamp=operation_time,
                wallet_id=sender_wallet_id,
                direction=Direction.OUTCOME,
                amount=amount,
                transfer_id=transfer.id,
                category_id=category_id,
            )
            outcome = mTransaction(**outcome_operation.model_dump())

            transtaction_repo.add(outcome)
            income_operation = TransactionAdd(
                timestamp=operation_time,
                wallet_id=reciever_wallet_id,
                direction=Direction.INCOME,
                amount=amount,
                transfer_id=transfer.id,
                category_id=category_id,
            )
            income = mTransaction(**income_operation.model_dump())
            transtaction_repo.add(income)

            sender_wallet.balance -= amount
            reciever_wallet.balance += amount

        return True

    def add_transaction(
        self, data: TransactionAdd, balance_control=True
    ) -> mTransaction:
        """Создает новую транзакцию"""
        transaction = None
        with self.uow.start():

            wallet_repo = self.uow.repo("wallet")
            category_repo = self.uow.repo("transaction_category")
            transtaction_repo = self.uow.repo("transactions")

            wallet = wallet_repo.get_by_id(data.wallet_id)

            if wallet is None:
                raise ValueError("Указанный кошелек отсутствует")

            category = category_repo.get_by_id(data.category_id)

            if category is None:
                raise ValueError("Указанная категория отсутствует")
            
            if data.amount <= 0:
                raise ValueError("Сумма операции не может быть отрицательна, или равна 0")

            value_with_direction = (
                data.amount if data.direction == Direction.INCOME else -data.amount
            )
            if (wallet.balance + value_with_direction < 0) and balance_control:
                raise ValueError("Недостаточно средств")

            transaction = transtaction_repo.add(mTransaction(**data.model_dump()))
            new_balance = wallet.balance + value_with_direction
            wallet.balance = new_balance

        return transaction
