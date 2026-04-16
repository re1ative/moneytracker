from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout
)
from PySide6.QtCore import Signal, Qt

from ...services.wallet_service import WalletService
from ...utils import format_money
from .general import AbstractEntitiesList, EntitiesListItem
from .dialogs import EditWalletDialog, MessageBox   



class Balance(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setText("Остаток: ")
        self.title_label.setStyleSheet(
            """

        font-size: 18px;
        
        """
        )
        layout.addWidget(self.title_label)

        self.amount_label = QLabel()
        self.amount_label.setStyleSheet(
            """

        font-size: 18px;
        font-weight: bold;
        """
        )
        layout.addWidget(self.amount_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)

    def set_balance(self, amount):
        text = f"{format_money(amount)} ₽"
        self.amount_label.setText(text)


class Wallets(QWidget):
    wallet_selected = Signal(int)
    _current_wallet_id: int | None

    def __init__(self, wallet_service: WalletService):
        super().__init__()
        self._current_wallet_id = None
        self.wallet_service = wallet_service

        layout = QVBoxLayout()

        self.combobox = QComboBox()
        self.combobox.currentIndexChanged.connect(self._on_combobox_item_selected)
        layout.addWidget(self.combobox)

        self.balance = Balance()
        layout.addWidget(self.balance)

        self.setLayout(layout)
        self.refresh_wallets()
        self.refresh_balance()

    def _on_combobox_item_selected(self, index):
        self._current_wallet_id = self.combobox.currentData()
        self.refresh_balance()
        self.wallet_selected.emit(self._current_wallet_id)

    def refresh_wallets(self):
        self.combobox.clear()
        wallets = self.wallet_service.get_wallets()
        for wallet in wallets:
            self.combobox.addItem(wallet.name, wallet.id)

    def get_current_wallet_id(self):
        return self._current_wallet_id

    def refresh_balance(self):
        if not self._current_wallet_id:
            return

        wallet = self.wallet_service.get_wallet(self._current_wallet_id)

        if not wallet:
            balance = 0.00
        else:
            balance = wallet.getBalance()

        self.balance.set_balance(balance)

class WalletList(AbstractEntitiesList):
    service: WalletService
    def refresh_list(self):
        self._clear()
        wallets = self.service.get_wallets()
        for wallet in wallets:
            widget = EntitiesListItem(wallet)
            widget.on_request_delete.connect(self.delete_wallet)
            widget.on_request_update.connect(self.show_update_dialog)
            self._layout.addWidget(widget)
            self.items.append(widget)
        self._layout.update()
        self.update()

    def show_update_dialog(self, wallet):
        dialog = EditWalletDialog(self, self.service, wallet)
        dialog.accepted.connect(self.refresh_list)
        dialog.show()

    def delete_wallet(self, wallet_id: int):
        try:
            self.service.delete_wallet(wallet_id)
            self.refresh_list()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))