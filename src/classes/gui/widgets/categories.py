from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt
from ...services.wallet_service import WalletService
from ...schemas.wallet import Direction
from .general import AbstractEntitiesList, EntitiesListItem
from .dialogs import EditCategoryDialog


class CategoriesListItem(EntitiesListItem):
    def setup(self):

        self._layout = QHBoxLayout()
        self._layout.setAlignment(Qt.AlignmentFlag.AlignBaseline)
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_widget.setLayout(info_layout)
        label = QLabel()
        label.setText(self.model.name)
        label.setStyleSheet(
            """
        font-size: 18px;
        font-weight: bold;
                            """
        )
        info_layout.addWidget(label)

        direction_label = QLabel()
        direction_title = None

        match self.model.direction:
            case Direction.INCOME:
                direction_title = "Поступления"
            case Direction.OUTCOME:
                direction_title = "Расходы"

        direction_label.setText(direction_title)
        info_layout.addWidget(direction_label)

        self._layout.addWidget(info_widget)

        self.setLayout(self._layout)

    def _setup_controls(self):
        if self.model.is_transfer:
            return
        return super()._setup_controls()


class CategoriesList(AbstractEntitiesList):
    service: WalletService

    def refresh_list(self):
        self._clear()
        categories = self.service.get_categories()
        for cat in categories:
            widget = CategoriesListItem(cat)
            widget.on_request_delete.connect(self.delete_category)
            widget.on_request_update.connect(self.show_update_dialog)
            self._layout.addWidget(widget)
            self.items.append(widget)

        self._layout.update()
        self.update()

    def show_update_dialog(self, wallet):
        dialog = EditCategoryDialog(self, self.service, wallet)
        dialog.show()
        dialog.accepted.connect(self.refresh_list)

    def delete_category(self, category_id: int):
        try:
            self.service.delete_category(category_id)
            self.refresh_list()
        except Exception as e:
            msgbox = QMessageBox()
            msgbox.setWindowTitle("Ошибка!")
            msgbox.setText(str(e))
