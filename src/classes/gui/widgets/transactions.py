from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QMenu,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from ...models.wallet import mTransaction
from ...schemas.wallet import Direction, TransactionTotalsResultItem
from ...services.wallet_service import WalletService
from ...uow import UnitOfWork
from ...utils import format_money
from .inputs import CategoryFilterWidget, InputDateWidget
from .dialogs import StatisticsDialog, MessageBox
from config import PAGE_LIMIT
from datetime import datetime, timedelta


class TransactionWidget(QWidget):
    """Виджет транзакции"""

    TRANSACTION_COLOR = {Direction.INCOME: "green", Direction.OUTCOME: "red"}

    on_delete_transaction = Signal(int)
    on_update_transaction = Signal(int)

    def __init__(self, transaction: mTransaction):
        super().__init__()

        main_layout = QHBoxLayout()
        self.transaction_id = transaction.id

        info_widget = QWidget()
        info_layout = QVBoxLayout()

        info_widget.setLayout(info_layout)
        info_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        category_label = QLabel()
        category_label_text = ""

        if not transaction.transfer:
            category_label_text = transaction.category.name
        else:
            if transaction.direction == Direction.INCOME:
                category_label_text = f"Пополнение с кошелька"
            else:
                category_label_text = f"Перевод на другой кошелек"

        category_label.setText(category_label_text)
        category_label.setStyleSheet(
            """
            font-size: 18px;
            font-weight: bold;                            
            
        """
        )

        info_layout.addWidget(category_label)
        if transaction.transfer:
            detail_label = QLabel()
            if transaction.direction == Direction.INCOME:
                detail_label_text = transaction.transfer.sender.name
            else:
                detail_label_text = transaction.transfer.reciever.name
            detail_label.setText(detail_label_text)
            info_layout.addWidget(detail_label)

        transaction_date_label = QLabel()
        transaction_date_label.setText(
            transaction.timestamp.strftime("%d.%m.%Y %H:%M:%S")
        )
        transaction_date_label.setStyleSheet(
            """
            font-size: 18px;
        """
        )
        info_layout.addWidget(transaction_date_label)
        info_layout.setStretch(0, 0)

        main_layout.addWidget(info_widget)

        color = self.TRANSACTION_COLOR.get(transaction.direction, "#ffffff")

        sum_label = QLabel()
        sum_label.setText(f"{format_money(transaction.getAmount())} ₽")
        sum_label.setStyleSheet(
            f"""
        font-size: 24px;
        font-weight: bold;         
        color: {color}                
        """
        )
        main_layout.addWidget(sum_label)
        self.setLayout(main_layout)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = QAction("Удалить", self)
        delete_action.triggered.connect(self.delete_transaction)
        actions = [delete_action]
        menu.addActions(actions)
        menu.exec(event.globalPos())

    def delete_transaction(self):
        reply = MessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить транзакцию #{self.transaction_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.on_delete_transaction.emit(self.transaction_id)


class TransactionListWidget(QWidget):
    """Виджет списка транзакций"""

    transactions_changed = Signal()
    transactions_items: list[TransactionWidget]

    def __init__(self, uow: UnitOfWork, wallet_id: int = None):
        super().__init__()
        self.uow = uow
        self.wallet_service = WalletService(uow)
        self._wallet_id = wallet_id

        default_period_from = datetime.now() - timedelta(31)
        default_period_to = datetime.now().replace(hour=23, minute=59, second=59)
        self.filters = {
            "categories": [],
            "period_from": default_period_from,
            "period_to": default_period_to,
        }

        self.transactions_items = []
        root_layout = QHBoxLayout()

        filters = QFrame()
        filters_layout = QVBoxLayout()
        filters_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        filters.setLayout(filters_layout)

        self.period_from = InputDateWidget(default_period_from)
        self.period_from.setText("Начало периода:")
        filters_layout.addWidget(self.period_from)

        self.period_to = InputDateWidget(default_period_to)
        self.period_to.setText("Конец периода:")
        filters_layout.addWidget(self.period_to)

        categories = self.wallet_service.get_categories()
        self.categories_widget = CategoryFilterWidget(categories)
        filters_layout.addWidget(self.categories_widget)

        filters_submit_btn = QPushButton()
        filters_submit_btn.setText("Применить")
        filters_submit_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(filters_submit_btn)

        stat_btn = QPushButton()
        stat_btn.setText("Показать статистику")
        stat_btn.clicked.connect(self.show_statistics)
        filters_layout.addWidget(stat_btn)

        

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scrolled_frame = QFrame(self.scroll_area)
        self.scroll_area.setWidget(scrolled_frame)

        self.list_layout = QVBoxLayout()
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(30)

        scrolled_frame.setLayout(self.list_layout)

        self.current_page = 0

        bar = self.scroll_area.verticalScrollBar()
        bar.valueChanged.connect(self._on_range_changed)

        root_layout.addWidget(self.scroll_area)
        root_layout.addWidget(filters)
        self.setLayout(root_layout)
        if self._wallet_id:
            self.refresh()

    def set_wallet_id(self, wallet_id: int):
        self._wallet_id = wallet_id

    def _clear(self):
        for widget in self.transactions_items:
            self.list_layout.removeWidget(widget)
            widget.deleteLater()
        self.transactions_items = []
        self.list_layout.update()
        self.update()

    def apply_filters(self):
        self.filters["categories"] = self.categories_widget.get_value()
        self.filters["period_from"] = self.period_from.get_value()
        self.filters["period_to"] = self.period_to.get_value()

        self.refresh()

    def refresh(self):
        self._clear()    
        self.load_transactions(0)

    def show_statistics(self):
        items = self.wallet_service.get_transaction_report(self.get_filters())
        dialog = StatisticsDialog(self, items)
        dialog.show()

    def _on_range_changed(self, height):
        maximum = self.scroll_area.verticalScrollBar().maximum()
        if (maximum - height) == 0:
            self.load_transactions(self.current_page + 1)

    def get_filters(self):
        filters = mTransaction.wallet_id.in_([self._wallet_id])
        checked_categories = self.filters.get("categories")
        period_from = self.filters.get("period_from")
        period_to = self.filters.get("period_to")
        if checked_categories:
            filters = filters.__and__(mTransaction.category_id.in_(checked_categories))

        if period_from and period_to:
            btw_stmt = mTransaction.timestamp.between(
                period_from, period_to + timedelta(1)
            )
            filters = filters.__and__(btw_stmt)

        return filters

    def load_transactions(self, page: int):

        if not self._wallet_id:
            return

        filters = self.get_filters()

        transactions = self.wallet_service.get_transactions(page, PAGE_LIMIT, filters)

        for transaction in transactions:
            widget = TransactionWidget(transaction)
            widget.on_delete_transaction.connect(self.delete_transaction)
            self.list_layout.addWidget(widget)
            self.transactions_items.append(widget)

        self.list_layout.update()
        self.update()
        self.current_page = page

    def delete_transaction(self, transaction_id):
        try:
            self.wallet_service.delete_transaction(transaction_id)
            self.refresh()
            self.transactions_changed.emit()
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))



        

