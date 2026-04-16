from PySide6.QtWidgets import QMainWindow, QToolBar
from PySide6.QtGui import QAction

from .frames import (
    HomeFrame,
    WalletsFrame,
    CategoriesFrame,
    SettingsFrame,
    AuthFrame,
    ImportFrame,
)
from .widgets.dialogs import MessageBox
from ..services.auth import AuthService
from ..uow import UnitOfWork
from config import APP_NAME


class MainWindow(QMainWindow):

    _uow: UnitOfWork

    def __init__(self, uow: UnitOfWork):
        super().__init__()
        self.setWindowTitle(f"Учет финансов - {APP_NAME}")

        self._uow = uow
        self.auth_service = AuthService(uow)
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        auth_frame = AuthFrame(self, self.auth_service)

        # словарь фреймов
        self.frames = {
            "home": (HomeFrame, [self._uow]),
            "wallets": (WalletsFrame, [self._uow]),
            "import": (ImportFrame, [self._uow]),
            "categories": (CategoriesFrame, [self._uow]),
            "settings": (SettingsFrame, [self._uow]),
        }

        # предопределяем страницы
        actions = [
            ("Главная", "Кошельки и их транзакции", lambda: self._change_frame("home")),
            (
                "Категории",
                "Управление категориями",
                lambda: self._change_frame("categories"),
            ),
            (
                "Кошельки",
                "Управление кошельками",
                lambda: self._change_frame("wallets"),
            ),
            (
                "Импорт",
                "Импорт в формате CSV",
                lambda: self._change_frame("import"),
            ),
            (
                "Настройки",
                "Настройки приложения",
                lambda: self._change_frame("settings"),
            ),
        ]

        # заполнение тулбара
        for i, action_data in enumerate(actions):
            action = QAction(action_data[0], self)
            action.setStatusTip(action_data[1])
            if action_data[2]:
                action.triggered.connect(action_data[2])
            toolbar.addAction(action)
        auth_frame.on_after_success_auth.connect(self.on_after_auth)
        self.setCentralWidget(auth_frame)

    def on_after_auth(self):
        self._change_frame("home")

    def _change_frame(self, target_frame):
        if target_frame != "auth":
            if not self.auth_service.is_logged():
                MessageBox.warning(
                    self, "Внимание", "Для работы в приложении требуется авторизоваться"
                )
                return

        frame_class = self.frames.get(target_frame)
        if frame_class:
            frame = frame_class[0](self, *frame_class[1])
            self.setCentralWidget(frame)
