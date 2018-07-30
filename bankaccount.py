from fundtransfer import FundTransfer
from fundtransfer import TransferType

class BankAccount(object):
    """A BankAccount captures the account information, balance and transaction history for a single account"""

    def __init__(self, account_id, bank_id, currency, balance, transaction_queue):
        self.account_id = account_id
        self.bank_id = bank_id
        self.currency = currency
        self.balance = balance
        self.transaction_queue = transaction_queue
        self.transaction_history = []

    def create_fund_transfer(self, transfer_id, amount, to_bank, to_account):
        """create_fund_transfer is used by the account to place outgoing (debit) transactions in the transaction queue"""
        transfer = FundTransfer(
            transfer_id,
            amount,
            self.currency,
            to_bank,
            to_account,
            self.bank_id,
            self.account_id,
            TransferType.DEBIT
        )
        self.transaction_queue.put(transfer)
        #print("txqueue count: {}".format(self.transaction_queue.qsize()))
        self.transaction_history.append(transfer)
        print('-----------------------------------')
        print(self.transaction_history)
        print('-----------------------------------')

    def get_transaction_history(self):
        return self.transaction_history

    def apply_credit_transfer(self, transfer):
        self.transaction_history.append(transfer)
