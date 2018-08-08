'''
Copyright 2018 International Business Machines

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from time import sleep
import multiprocessing as mp
import random
import logging
from logging.config import fileConfig

fileConfig('logging_config.ini')
logger = logging.getLogger()

import bank

def make_payments(from_account, to_bank_id, to_account_id):
    try:
        while True:
            sleep(random.uniform(5,20))
            from_account.create_fund_transfer("txfer0", 10, to_bank_id, to_account_id)
    except KeyboardInterrupt:
        return
        


if __name__ == "__main__":
    bank1 = bank.Bank("bank1", "localhost:3001")
    bank2 = bank.Bank("bank2", "localhost:3002")
    acc11 = bank1.create_bank_account(11, 10000)
    acc12 = bank1.create_bank_account(12, 10000)
    acc21 = bank2.create_bank_account(21, 10000)
    acc22 = bank2.create_bank_account(22, 10000)

    '''
    acc11.create_fund_transfer("txfer1", 10, "bank2", 21)
    acc21.create_fund_transfer("txfer2", 10, "bank1", 11)
    '''
    workers = []
    workers.append(mp.Process(target=make_payments, args=(acc11, "bank2", 21,)))
    workers.append(mp.Process(target=make_payments, args=(acc11, "bank2", 22,)))
    workers.append(mp.Process(target=make_payments, args=(acc12, "bank2", 21,)))
    workers.append(mp.Process(target=make_payments, args=(acc12, "bank2", 22,)))
    workers.append(mp.Process(target=make_payments, args=(acc21, "bank1", 11,)))
    workers.append(mp.Process(target=make_payments, args=(acc21, "bank1", 12,)))
    workers.append(mp.Process(target=make_payments, args=(acc22, "bank1", 11,)))
    workers.append(mp.Process(target=make_payments, args=(acc22, "bank1", 12,)))
    for w in workers:
        w.start()