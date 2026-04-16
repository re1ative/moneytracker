
from classes.uow import UnitOfWork
from classes.services.wallet_service import WalletService
from classes.schemas.wallet import TransactionAdd
from classes.db import SessionLocal

import random

# Предназначен для создания демонстрационных данных

if __name__ == '__main__':
    

    uow = UnitOfWork(SessionLocal)
    service = WalletService(uow)
    
    categories = service.get_categories()
    wallets = service.get_wallets()

    for _ in range(150):
        cat = random.choice(categories)
        wallet = random.choice(wallets)
        try:
            transaction = TransactionAdd(
                wallet_id=wallet.id,
                category_id=cat.id,
                direction=cat.direction,
                amount=random.randint(1000, 1000000)
            )
        
            service.add_transaction(transaction)
        except Exception as e:
            print(e)
        

