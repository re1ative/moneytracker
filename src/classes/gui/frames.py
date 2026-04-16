from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QFileDialog,
    QLabel,
    QMessageBox,
    QLineEdit,
)
from PySide6.QtCore import Signal, Qt

from abc import abstractmethod
from ..utils import DataImport
from ..schemas.wallet import Direction
from ..services.wallet_service import WalletService
from ..services.settings import SettingService
from ..services.auth import AuthService

from .widgets.wallet import Wallets, WalletList
from .widgets.transactions import TransactionListWidget
from .widgets.dialogs import (
    TransferDialog,
    AddWalletDialog,
    OperationDialog,
    AddCategoryDialog,
    MessageBox,
)
from .widgets.categories import CategoriesList
from .widgets.settings import PasswordWidget
from config import APP_NAME


class AbstractFrame(QFrame):
    @abstractmethod
    def refresh():
        pass


class ImportFrame(AbstractFrame):
    def __init__(self, parent, uow):
        super().__init__(parent)
        self.uow = uow

        layout = QVBoxLayout()
        label = QLabel()
        label.setText("Выберите файл с данными в формате CSV")
        download_btn = QPushButton()
        download_btn.setText("Выбрать файл")
        download_btn.clicked.connect(self._file_request)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(download_btn)
        self.setLayout(layout)

        self.file_dialog = QFileDialog(self)
        self.file_dialog.setNameFilter("CSV (*.csv)")

    def _file_request(self):
        filepath, _ = self.file_dialog.getOpenFileName()

        if not filepath:
            return

        dataimport = DataImport(self.uow)
        msgbox = QMessageBox(self)

        try:
            result = dataimport.import_data(filepath)
            msgbox.setWindowTitle("Успех")
            msgbox.setText(
                f"""
                Добавлено {len(result)} записей!
            """
            )
        except Exception as e:
            msgbox.setWindowTitle("Ошибка!")
            msgbox.setText(
                f"""
                Данные не были добавлены: {str(e)}
            """
            )

        msgbox.show()


class AuthFrame(AbstractFrame):
    on_after_success_auth = Signal()

    def __init__(self, parent, service: AuthService):
        super().__init__(parent)
        self.service = service
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel()
        label.setText("Пожалуйста, введите пароль")
        layout.addWidget(label)
        self.pwd_field = QLineEdit()
        self.pwd_field.setMaximumWidth(150)
        layout.addWidget(self.pwd_field)

        submit_btn = QPushButton()
        submit_btn.setMaximumWidth(150)
        submit_btn.setText("Вход")
        submit_btn.clicked.connect(self.auth)
        layout.addWidget(submit_btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def auth(self):
        value = self.pwd_field.text()
        self.service.authorize(value)

        if self.service.is_logged():
            MessageBox.information(self, "Успешно!", f"Вы авторизовались в {APP_NAME}")
            self.on_after_success_auth.emit()
        else:
            MessageBox.critical(self, "Ошибка!", f"Неправильный пароль")

    def refresh():
        pass


class HomeFrame(AbstractFrame):
    def __init__(self, parent, uow):
        super().__init__(parent)

        self.uow = uow
        self.wallet_service = WalletService(self.uow)

        layout = QVBoxLayout(self)

        self.wallets = Wallets(self.wallet_service)
        self.current_wallet_id = self.wallets.get_current_wallet_id()
        self.wallets.wallet_selected.connect(self.on_wallet_selected)

        layout.addWidget(self.wallets)

        self.transactions_list = TransactionListWidget(self.uow, self.current_wallet_id)
        self.transactions_list.transactions_changed.connect(self.refresh)
        layout.addWidget(self.transactions_list)

        transaction_buttons = QWidget()
        transaction_buttons_layout = QHBoxLayout()
        transaction_buttons.setLayout(transaction_buttons_layout)

        income_button = QPushButton()
        income_button.setText("Приход")
        income_button.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            background: green;
        """
        )
        income_button.pressed.connect(
            lambda: self.on_click_operation_button(Direction.INCOME)
        )
        transaction_buttons_layout.addWidget(income_button)

        outcome_button = QPushButton()
        outcome_button.setText("Расход")
        outcome_button.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;
            background: red;
        """
        )
        outcome_button.pressed.connect(
            lambda: self.on_click_operation_button(Direction.OUTCOME)
        )
        transaction_buttons_layout.addWidget(outcome_button)

        transfer_btn = QPushButton()
        transfer_btn.setText("Перевод")
        transfer_btn.clicked.connect(self.on_click_transfer)

        layout.addWidget(transaction_buttons)
        layout.addWidget(transfer_btn)

        self.setLayout(layout)

    def refresh(self):
        self.transactions_list.refresh()
        self.wallets.refresh_balance()

    def on_wallet_selected(self, wallet_id):
        self.current_wallet_id = wallet_id
        self.transactions_list.set_wallet_id(wallet_id)
        self.transactions_list.refresh()

    def on_click_transfer(self):
        if not self.current_wallet_id:

            msgbox = QMessageBox(self)
            msgbox.setText("Не выбран кошелек")
            msgbox.show()
            return

        dialog = TransferDialog(self, self.wallet_service, self.current_wallet_id)
        dialog.operation_created.connect(self.refresh)
        dialog.show()

    def on_click_operation_button(self, direction: Direction):

        if not self.current_wallet_id:

            msgbox = QMessageBox(self)
            msgbox.setText("Не выбран кошелек")
            msgbox.show()
            return

        dialog = OperationDialog(
            self, self.wallet_service, self.current_wallet_id, direction
        )
        dialog.operation_created.connect(self.refresh)
        dialog.show()


class WalletsFrame(AbstractFrame):
    def __init__(self, parent, uow):
        super().__init__(parent)

        self.uow = uow
        self.wallet_service = WalletService(self.uow)

        layout = QVBoxLayout(self)

        self.wallets = WalletList(self.wallet_service)
        layout.addWidget(self.wallets)

        create_btn = QPushButton()
        create_btn.setText("Новый кошелек")
        create_btn.clicked.connect(self._show_add_dialog)
        layout.addWidget(create_btn)

        self.setLayout(layout)

    def _show_add_dialog(self):
        dialog = AddWalletDialog(self, self.wallet_service)
        dialog.accepted.connect(self.refresh)
        dialog.show()

    def refresh(self):

        self.wallets.refresh_list()


class CategoriesFrame(AbstractFrame):
    def __init__(self, parent, uow):
        super().__init__(parent)

        self.uow = uow
        self.wallet_service = WalletService(self.uow)

        layout = QVBoxLayout(self)

        self.categories = CategoriesList(self.wallet_service)

        layout.addWidget(self.categories)

        create_btn = QPushButton()
        create_btn.setText("Создать категорию")
        create_btn.clicked.connect(self._show_add_dialog)
        layout.addWidget(create_btn)

        self.setLayout(layout)

    def _show_add_dialog(self):
        dialog = AddCategoryDialog(self, self.wallet_service)
        dialog.accepted.connect(self.refresh)
        dialog.show()

    def refresh(self):

        self.categories.refresh_list()


class SettingsFrame(AbstractFrame):
    def __init__(self, parent, uow):
        super().__init__(parent)

        self.uow = uow
        self.service = SettingService(self.uow)

        layout = QVBoxLayout(self)
        pwd_widget = PasswordWidget(self.uow)
        layout.addWidget(pwd_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def refresh(self):

        pass
