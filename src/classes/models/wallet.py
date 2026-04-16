from classes.models.base_model import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
import datetime
from classes.schemas.wallet import Direction


class mWallet(BaseModel):
    __tablename__ = "wallet"
    name: Mapped[str]
    balance: Mapped[int]  ## баланс в копейках
    transactions: Mapped["mTransaction"] = relationship(
        "mTransaction",
        back_populates="wallet",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def getBalance(self):
        """Баланс в рублях"""
        return round(self.balance / 100, 2)


class mTransfer(BaseModel):
    __tablename__ = "transfers"
    timestamp: Mapped[datetime.datetime]
    sender_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    reciever_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    transactions: Mapped["mTransaction"] = relationship(
        "mTransaction", back_populates="transfer", uselist=True, cascade="delete"
    )
    amount: Mapped[int]
    sender: Mapped["mWallet"] = relationship(
        "mWallet", lazy="joined", uselist=False, foreign_keys=[sender_id]
    )
    reciever: Mapped["mWallet"] = relationship(
        "mWallet", lazy="joined", uselist=False, foreign_keys=[reciever_id]
    )


class mTransaction(BaseModel):
    __tablename__ = "transactions"
    timestamp: Mapped[datetime.datetime]
    direction: Mapped[Direction]
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    amount: Mapped[int]
    transfer_id: Mapped[bool] = mapped_column(
        ForeignKey("transfers.id", ondelete="CASCADE"), nullable=True
    )
    transfer: Mapped["mTransfer"] = relationship(
        "mTransfer",
        back_populates="transactions",
        lazy="joined",
        uselist=False,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_category.id", ondelete="CASCADE"), nullable=True
    )
    category: Mapped["mTransactionCategory"] = relationship(
        "mTransactionCategory",
        back_populates="transactions",
        lazy="joined",
        uselist=False,
    )
    wallet: Mapped["mWallet"] = relationship(
        "mWallet", back_populates="transactions", lazy="joined", uselist=False
    )

    def getAmount(self):
        """Сумма транзакции в рублях"""
        return round(self.amount / 100, 2)


class mTransactionCategory(BaseModel):
    __tablename__ = "transaction_category"
    direction: Mapped[Direction] = mapped_column(nullable=True)
    name: Mapped[str]
    is_transfer: Mapped[bool] = mapped_column(default=False)
    transactions: Mapped["mTransaction"] = relationship(
        "mTransaction",
        back_populates="category",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
