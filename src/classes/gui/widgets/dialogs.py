from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QDateTimeEdit,
)
from PySide6.QtCore import Signal, QDateTime
from PySide6.QtGui import QRegularExpressionValidator
from ...schemas.wallet import Direction, TransactionAdd, TransactionTotalsResultItem
from ...services.wallet_service import WalletService
from .statistics import StatisticsItem, StatisticsItemTotal


from datetime import datetime


class OperationDialog(QDialog):
    operation_created = Signal()
    wallet_service: WalletService

    def __init__(
        self,
        parent,
        wallet_service: WalletService,
        wallet_id: int,
        direction: Direction,
    ):
        super().__init__(parent)
        self.wallet_service = wallet_service
        self.wallet_id = wallet_id
        self.direction = direction

        match self.direction:
            case Direction.INCOME:
                title = "Новый приход"
            case Direction.OUTCOME:
                title = "Новый расход"

        self.setWindowTitle(title)

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close
        )
        buttonbox = QDialogButtonBox(buttons)

        buttonbox.accepted.connect(self._create_transaction)
        buttonbox.rejected.connect(self.close)

        buttonbox.button(QDialogButtonBox.StandardButton.Ok).setText("ОК")
        buttonbox.button(QDialogButtonBox.StandardButton.Close).setText("Закрыть")
        layout = QVBoxLayout()

        category_group = QWidget()
        category_group_layout = QHBoxLayout()
        category_group.setLayout(category_group_layout)

        category_label = QLabel()
        category_label.setText("Выберите категорию:")
        self.category_combobox = QComboBox()
        categories = self.wallet_service.get_categories(self.direction)
        for category in categories:
            self.category_combobox.addItem(category.name, category)
        category_group_layout.addWidget(category_label)
        category_group_layout.addWidget(self.category_combobox)

        amount_group = QWidget()
        amount_group_layout = QHBoxLayout()
        amount_group.setLayout(amount_group_layout)

        amount_label = QLabel()
        amount_label.setText("Введите сумму:")
        self.amount_input = QLineEdit()
        validator = QRegularExpressionValidator(regularExpression=r"[0-9]{1,}.[0-9]{2}")
        self.amount_input.setValidator(validator)
        amount_group_layout.addWidget(amount_label)
        amount_group_layout.addWidget(self.amount_input)

        datetime_group = QWidget()
        datetime_group_layout = QHBoxLayout()
        datetime_group.setLayout(datetime_group_layout)

        datetime_label = QLabel()
        datetime_label.setText("Дата операции:")
        self.datetime_input = QDateTimeEdit(calendarPopup=True)

        datetime_group_layout.addWidget(datetime_label)
        datetime_group_layout.addWidget(self.datetime_input)

        layout.addWidget(category_group)
        layout.addWidget(amount_group)
        layout.addWidget(datetime_group)

        layout.addWidget(buttonbox)
        self.setLayout(layout)

    def show(self):
        current_datetime = QDateTime()
        current_datetime.setMSecsSinceEpoch(int(datetime.now().timestamp() * 1000))
        self.datetime_input.setDateTime(current_datetime)
        return super().show()

    def _create_transaction(self):
        try:
            amount = int(float(self.amount_input.text()) * 100)
            category = self.category_combobox.currentData()
            timestamp = self.datetime_input.dateTime().toPython()
            transaction_data = TransactionAdd(
                timestamp=timestamp,
                wallet_id=self.wallet_id,
                direction=self.direction,
                amount=amount,
                category_id=category.id,
            )
            transaction = self.wallet_service.add_transaction(transaction_data)
            self.operation_created.emit()
            self.close()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))

        return super().accept()


class TransferDialog(QDialog):
    operation_created = Signal()
    wallet_service: WalletService

    def __init__(self, parent, wallet_service: WalletService, wallet_id: int):
        super().__init__(parent)
        self.wallet_service = wallet_service
        self.wallet_id = wallet_id

        self.setWindowTitle("Перевод на кошелек")

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close
        )
        buttonbox = QDialogButtonBox(buttons)
        buttonbox.button(QDialogButtonBox.StandardButton.Ok).setText("ОК")
        buttonbox.button(QDialogButtonBox.StandardButton.Close).setText("Закрыть")
        buttonbox.accepted.connect(self._create_transfer)
        buttonbox.rejected.connect(self.close)
        layout = QVBoxLayout()

        wallet_group = QWidget()
        wallet_group_layout = QHBoxLayout()
        wallet_group.setLayout(wallet_group_layout)

        wallet_label = QLabel()
        wallet_label.setText("Выберите кошелек:")
        self.wallet_combobox = QComboBox()
        wallets = self.wallet_service.get_wallets()
        for wallet in wallets:
            if wallet.id == self.wallet_id:
                continue

            self.wallet_combobox.addItem(wallet.name, wallet.id)

        wallet_group_layout.addWidget(wallet_label)
        wallet_group_layout.addWidget(self.wallet_combobox)

        amount_group = QWidget()
        amount_group_layout = QHBoxLayout()
        amount_group.setLayout(amount_group_layout)

        amount_label = QLabel()
        amount_label.setText("Введите сумму:")
        self.amount_input = QLineEdit()
        validator = QRegularExpressionValidator(regularExpression=r"[0-9]{1,}.[0-9]{2}")
        self.amount_input.setValidator(validator)
        amount_group_layout.addWidget(amount_label)
        amount_group_layout.addWidget(self.amount_input)

        layout.addWidget(wallet_group)
        layout.addWidget(amount_group)

        layout.addWidget(buttonbox)
        self.setLayout(layout)

    def _create_transfer(self):
        try:
            amount = int(float(self.amount_input.text()) * 100)

            transfered = self.wallet_service.transfer_to_wallet(
                self.wallet_id, self.wallet_combobox.currentData(), amount
            )
            if not transfered:
                raise Exception("Не удалось перевести на другой кошелек.")
            self.operation_created.emit()
            self.close()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))

        return super().accept()


class AddCategoryDialog(QDialog):

    wallet_service: WalletService

    def __init__(self, parent, wallet_service: WalletService):
        super().__init__(parent)
        self.wallet_service = wallet_service

        self.setWindowTitle("Новая категория")

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close
        )
        self.buttonbox = QDialogButtonBox(buttons)
        self.buttonbox.button(QDialogButtonBox.StandardButton.Ok).setText("Сохранить")
        self.buttonbox.button(QDialogButtonBox.StandardButton.Close).setText("Закрыть")
        self.buttonbox.accepted.connect(self._create_category)
        self.buttonbox.rejected.connect(self.close)

        layout = QVBoxLayout()

        name_label = QLabel()
        name_label.setText("Название категории")
        self.name_input = QLineEdit()
        validator = QRegularExpressionValidator(regularExpression=r".{1,}")
        self.name_input.setValidator(validator)

        self.direction_input = QComboBox()
        for d in [(Direction.INCOME, "Поступления"), (Direction.OUTCOME, "Расходы")]:
            self.direction_input.addItem(d[1], d[0])

        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.direction_input)

        layout.addWidget(self.buttonbox)
        self.setLayout(layout)

    def _create_category(self):
        try:
            name = self.name_input.text()
            direction = self.direction_input.currentData()

            category = self.wallet_service.create_category(name, direction)
            self.close()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))

        return super().accept()


class EditCategoryDialog(AddCategoryDialog):

    def __init__(self, parent, wallet_service, category):
        super().__init__(parent, wallet_service)
        self.category = category
        self.name_input.setText(category.name)

        for i in range(self.direction_input.count()):
            if self.category.direction == self.direction_input.itemData(i):
                self.direction_input.setCurrentIndex(i)
        self.buttonbox.accepted.disconnect(self._create_category)
        self.buttonbox.accepted.connect(self._save)

    def _save(self):
        try:
            name = self.name_input.text()
            direction = self.direction_input.currentData()
            self.wallet_service.update_category(
                self.category.id, {"name": name, "direction": direction}
            )

            self.close()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))

        return super().accept()


class AddWalletDialog(QDialog):
    wallet_service: WalletService

    def __init__(self, parent, wallet_service: WalletService):
        super().__init__(parent)
        self.wallet_service = wallet_service

        self.setWindowTitle("Новый кошелек")

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close
        )
        self.buttonbox = QDialogButtonBox(buttons)

        self.buttonbox.button(QDialogButtonBox.StandardButton.Ok).setText("Сохранить")
        self.buttonbox.button(QDialogButtonBox.StandardButton.Close).setText("Закрыть")
        self.buttonbox.accepted.connect(self._create_wallet)
        self.buttonbox.rejected.connect(self.close)
        layout = QVBoxLayout()

        name_label = QLabel()
        name_label.setText("Название кошелька")
        self.name_input = QLineEdit()
        validator = QRegularExpressionValidator(regularExpression=r".{1,}")
        self.name_input.setValidator(validator)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.buttonbox)
        self.setLayout(layout)

    def _create_wallet(self):
        try:
            name = self.name_input.text()

            self.wallet_service.create_wallet(name)
            self.close()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))

        return super().accept()


class EditWalletDialog(AddWalletDialog):

    def __init__(self, parent, wallet_service, wallet):
        super().__init__(parent, wallet_service)
        self.wallet = wallet
        self.name_input.setText(wallet.name)
        self.buttonbox.accepted.disconnect(self._create_wallet)
        self.buttonbox.accepted.connect(self._save)

    def _save(self):
        try:
            name = self.name_input.text()

            self.wallet_service.update_wallet(self.wallet.id, {"name": name})

            self.close()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))

        return super().accept()


class StatisticsDialog(QDialog):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.setWindowTitle("Статистика приходов/расходов")
        layout = QVBoxLayout(self)
        total_income = 0
        total_outcome = 0
        for item in items:
            widget = StatisticsItem(item)
            if item.direction == Direction.INCOME:
                total_income += item.amount
            else:
                total_outcome += item.amount
            layout.addWidget(widget)

        total_income_item = TransactionTotalsResultItem(
            category="Всего пришло", direction=Direction.INCOME, amount=total_income
        )
        total_outcome_item = TransactionTotalsResultItem(
            category="Всего потрачено",
            direction=Direction.OUTCOME,
            amount=total_outcome,
        )

        total_income_widget = StatisticsItemTotal(total_income_item)
        total_outcome_widget = StatisticsItemTotal(total_outcome_item)

        for widget in [total_income_widget, total_outcome_widget]:
            layout.addWidget(widget)


class MessageBox(QMessageBox):

    BUTTONS_TRANSLATE = {
        QMessageBox.StandardButton.Ok: "ОК",
        QMessageBox.StandardButton.Cancel: "Отмена",
        QMessageBox.StandardButton.Yes: "Да",
        QMessageBox.StandardButton.No: "Нет",
        QMessageBox.StandardButton.Save: "Сохранить",
        QMessageBox.StandardButton.Discard: "Не сохранять",
        QMessageBox.StandardButton.Open: "Открыть",
        QMessageBox.StandardButton.Close: "Закрыть",
    }

    @staticmethod
    def question(parent, title, text, /, buttons=..., defaultButton=...):
        messagebox = MessageBox(parent=parent)
        messagebox.setIcon(QMessageBox.Icon.Question)
        messagebox.setWindowTitle(title)
        messagebox.setText(text)
        messagebox.setStandardButtons(buttons)
        messagebox.setDefaultButton(defaultButton)
        messagebox._localize()
        return messagebox.exec()
    
    def _localize(self):
        for btn in self.BUTTONS_TRANSLATE:
            button = self.button(btn)
            if button:
                button.setText(self.BUTTONS_TRANSLATE[btn])
