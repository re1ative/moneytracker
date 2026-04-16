from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from abc import abstractmethod
from ...models.base_model import BaseModel
from .dialogs import MessageBox

class EntitiesListItem(QWidget):
    on_request_delete = Signal(int)
    on_request_update = Signal(BaseModel)
    model: BaseModel

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setup()
        self._setup_controls()

    def setup(self):

        self._layout = QHBoxLayout()

        label = QLabel()
        label.setText(self.model.name)
        label.setStyleSheet("""
        font-size: 18px;
        font-weight: bold;
        """)
        self._layout.addWidget(label)

        self.setLayout(self._layout)

    def _setup_controls(self):

        buttongroup = QWidget()
        layout = QHBoxLayout(buttongroup)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        button_edit = QPushButton()
        button_edit.setText("Изменить")
        button_edit.setFixedWidth(70)
        button_edit.setStyleSheet("""
        background-color: green;
        """)
        button_edit.clicked.connect(lambda x: self.on_request_update.emit(self.model))
        layout.addWidget(button_edit)

        button_delete = QPushButton()
        button_delete.clicked.connect(self.delete)
        button_delete.setStyleSheet("""
        background-color: red;
        """)
        button_delete.setFixedWidth(70)
        button_delete.setText("Удалить")
        layout.addWidget(button_delete)
        self._layout.addWidget(buttongroup)
        

    def delete(self):
        reply = MessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить элемент?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.on_request_delete.emit(self.model.id)


class AbstractEntitiesList(QScrollArea):
    item_widget: EntitiesListItem = EntitiesListItem
    items: list[EntitiesListItem]

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.items = []
        root = QFrame(self)
        self._layout = QVBoxLayout()
        self._layout.setSpacing(30)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidgetResizable(True)
        root.setLayout(self._layout)

        self.setWidget(root)
        self.refresh_list()

    def _clear(self):
        for widget in self.items:
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._layout.update()
        self.update()
        self.items = []

    @abstractmethod
    def refresh_list(self):
        pass
