from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QMessageBox
)
from ...uow import UnitOfWork
from ...services.settings import SettingService
from ...utils import hash_password
from .dialogs import MessageBox
from config import PASSWORD_KEY




class PasswordWidget(QWidget):
    def __init__(self, uow: UnitOfWork):
        super().__init__()
        self.service = SettingService(uow)
        layout = QHBoxLayout()
        label = QLabel()
        label.setText("Пароль для входа в приложение")

        layout.addWidget(label)

        self.field = QLineEdit()
        self.field.setText("")
        layout.addWidget(self.field)

        save_btn = QPushButton()
        save_btn.clicked.connect(self.save)
        save_btn.setText("Сохранить")

        layout.addWidget(save_btn)
        self.setLayout(layout)

    def save(self):
        value = hash_password(self.field.text())
        try:
            self.service.set_setting(PASSWORD_KEY, value)
            MessageBox.information(self, "Успешно", "Успешно сохранено")
        except Exception as e:
            MessageBox.critical(self, "Ошибка", str(e))
