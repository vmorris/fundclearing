from enum import Enum
from datetime import datetime

class State(Enum):
    CREATED = 1
    SUBMITTED = 2
    PAID_IN_PRINCIPAL = 3
    PAID = 4

class TransferType(Enum):
    DEBIT = 1
    CREDIT = 2

class FundTransfer(object):

    def __init__(self, transfer_id, amount, currency, to_bank, to_account, from_bank, from_account, transfer_type):
        self.transfer_id = transfer_id
        self.amount = amount
        self.currency = currency
        self.to_bank = to_bank
        self.to_account = to_account
        self.from_bank = from_bank
        self.from_account = from_account
        self.transfer_type = transfer_type
        self.state = State.CREATED
        self.created_timestamp = datetime.utcnow()
        self.submitted_timestamp = None
        self.paid_in_principle_timestamp = None
        self.paid_timestamp = None
        
    def markSubmitted(self):
        self.state = State.SUBMITTED
        self.submitted_timestamp = datetime.utcnow()
    
    def markPaidInPriciple(self):
        self.state = State.PAID_IN_PRINCIPAL
        self.paid_in_principle_timestamp = datetime.utcnow()

    def markPaid(self):
        self.state = State.PAID
        self.paid_timestamp = datetime.utcnow()