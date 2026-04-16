from .wallet import rTransaction, rWallet, rTransactionCategory, rTransfer
from .setting import rSetting

REPO_REGISTRY = {
    "transactions": rTransaction,
    "transaction_category": rTransactionCategory,
    "wallet": rWallet,
    "setting": rSetting,
    "transfer": rTransfer
}