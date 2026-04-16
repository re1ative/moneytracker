from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QDateEdit,
    QCheckBox,
)
from PySide6.QtCore import QDate
from ...models.wallet import mTransactionCategory


from datetime import datetime


class CategoryFilterWidget(QWidget):
    categories_checkboxes: dict[int, QCheckBox]

    def __init__(self, categories: list[mTransactionCategory]):
        super().__init__()
        self.categories_checkboxes = {}
        layout = QGridLayout()
        for category in categories:
            checkbox = QCheckBox()
            checkbox.setText(category.name)
            layout.addWidget(checkbox)
            self.categories_checkboxes[category.id] = checkbox
        self.setLayout(layout)

    def get_value(self) -> list[int]:
        selected = []
        for key in self.categories_checkboxes:
            if self.categories_checkboxes[key].isChecked():
                selected.append(key)

        return selected


class InputDateWidget(QWidget):
    input: QDateEdit

    def __init__(self, value: datetime = datetime.now()):
        super().__init__()
        period_layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setText("Дата:")
        period_layout.addWidget(self.label)
        default_value = QDate()
        default_value.setDate(value.year, value.month, value.day)
        self.input = QDateEdit(default_value)

        period_layout.addWidget(self.input)
        self.setLayout(period_layout)

    def setText(self, value):
        self.label.setText(value)

    def get_value(self) -> datetime:
        return self.input.date().toPython()
