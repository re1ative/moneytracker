
from .db import create_tables
from hashlib import md5
from .db import SessionLocal
from .uow import UnitOfWork
from .services.wallet_service import WalletService
from .services.settings import SettingService
from .schemas.wallet import Direction, TransactionAdd
import datetime
import csv
import os
from config import DBFILENAME, DEFAULT_PWD, PASSWORD_KEY

def need_install():
    return not os.path.exists(f'{os.getcwd()}\\{DBFILENAME}')

def install():
     
    create_tables()

    
    uow = UnitOfWork(SessionLocal)
    service = WalletService(uow)
    settings_service = SettingService(uow)

    # Установка пароля по умолчанию
    initial_password = hash_password(DEFAULT_PWD)
    settings_service.set_setting(PASSWORD_KEY, initial_password)
    
    start_wallets = [
        "Наличные",
        "Кубышка",
        "Банковская карта"
     ]
    start_categories = [
        ("Переводы", None, True), # категория для переводов
        ("ЖКУ", Direction.OUTCOME, False),
        ("Транспорт", Direction.OUTCOME, False),
        ("Развлечения", Direction.OUTCOME, False),
        ("Зарплата", Direction.INCOME, False),
        ("Прочие доходы", Direction.INCOME, False)
    ]

    #создание категорий
    for cat in start_categories:
        service.create_category(cat[0], cat[1], cat[2])
            
    # создание кошельков с балансов = 0
    for w in start_wallets:
        service.create_wallet(w, 0)

def format_money(value: int | float) -> str:
    return '{0:,.2f}'.format(value).replace(',', ' ')

def hash_password(value: str):
    return md5(value.encode("utf8")).hexdigest()


class DataImport:

    TIMESTAMP_FIELD = "timestamp"
    WALLET_FIELD = "wallet"
    CATEGORY_FIELD = "category"
    AMOUNT_FIELD = "amount"
    DIRECTION_FIELD = "direction"

    def __init__(self, uow):
        self.service = WalletService(uow)

        self.wallets = {}
        self.categories = {}
    
    def import_data(self, filepath) -> True:
        wallets = {}
        categories = {}

        exists_wallets = self.service.get_wallets()

        for w in exists_wallets:
            wallets[w.name] = w.id

        exists_categories = self.service.get_categories()

        added_transactions = []

        for c in exists_categories:
            categories[c.name] = c.id

        try:
            with open(filepath, 'r', encoding='utf8') as f:
                csv_reader = csv.DictReader(f)

                for row in csv_reader:

                    wallet_name = row[self.WALLET_FIELD]
                    
                    timestamp = datetime.datetime.strptime(row[self.TIMESTAMP_FIELD], '%d.%m.%Y %H:%M:%S')
                    category_name = row[self.CATEGORY_FIELD]
                    amount = int(float(row[self.AMOUNT_FIELD]) * 100)

                    if int(row[self.DIRECTION_FIELD]) == 1:
                        direction = Direction.OUTCOME
                    else:
                        direction = Direction.INCOME

                    wallet_id = wallets.get(wallet_name)
                    if wallet_id is None:
                        wallet = self.service.create_wallet(wallet_name)
                        wallet_id = wallet.id
                        wallets[wallet_name] = wallet_id

                    category_id = categories.get(category_name)
                    if category_id is None:
                        category = self.service.create_category(category_name, direction)
                        category_id = category.id
                        categories[category_name] = category_id

                    transaction = TransactionAdd(
                        timestamp=timestamp,
                        wallet_id = wallet_id,
                        category_id=category_id,
                        direction=direction,
                        amount=amount

                    )

                    transaction = self.service.add_transaction(transaction, False)
                    added_transactions.append(transaction.id)

        except ValueError as e:
            for id in added_transactions:
                self.service.delete_transaction(id)
            raise Exception(f"Данные не соответствуют формату. Подробнее: {str(e)}")
        
        except KeyError as e:
            raise ValueError(f"В файле импорта отсутствует колонка {str(e)}")

        except Exception as e:
            for id in added_transactions:
                self.service.delete_transaction(id)
            
            raise e
        

        return added_transactions

                
