from PySide6.QtWidgets import QApplication
from classes.gui.windows import MainWindow
from classes.uow import UnitOfWork
from classes.db import SessionLocal
from classes.utils import install, need_install


if __name__ == '__main__':

    if need_install():
        install()

    app = QApplication([])

    uow = UnitOfWork(SessionLocal)
    
    main_window = MainWindow(uow)
    main_window.show()
    
    app.exec() 