from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QHBoxLayout,
)

from ...schemas.wallet import TransactionTotalsResultItem, Direction
from ...utils import format_money


class StatisticsItem(QWidget):
    def __init__(self, item: TransactionTotalsResultItem):
        super().__init__()
        layout = QHBoxLayout()

        self.category_label = QLabel()
        self.category_label.setStyleSheet("""
            font-weight: bold;
        """)
        self.category_label.setText(f"{item.category}:")


        self.amount_label = QLabel()
        
        value = item.amount / 100

        if item.direction == Direction.INCOME:
            color = "green"
        else:
            value *= -1
            color = "red"

        self.amount_label.setStyleSheet(f"""
            font-weight: bold;
            color: {color};
        """)


        self.amount_label.setText(f"{format_money(value)} ₽")

        for label in [self.category_label,  self.amount_label]:
            layout.addWidget(label)

        self.setLayout(layout)


class StatisticsItemTotal(StatisticsItem):
    def __init__(self, item):
        super().__init__(item)
        self.category_label.setStyleSheet("""
        font-weight: bold;
        font-size: 18px;                     
        """)

        if item.direction == Direction.INCOME:
            color = "green"
        else:
            color = "red"

        self.amount_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 18px;                              
            color: {color};
        """)
        