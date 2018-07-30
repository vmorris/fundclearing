import os
import multiprocessing as mp
from time import sleep
import sys
import uuid
import random
from websocket import create_connection
import json
import pickle
import asyncio
import threading

from fundclearingapi import FundClearingApi
from bankaccount import BankAccount
import fund_clearing_python_sdk

# setup logger
import logging
from logging.config import fileConfig
fileConfig('logging_config.ini')
logger = logging.getLogger()

class Bank(object):
    '''
    A Bank class captures a fund-clearing-network BankingParticipant
    '''

    def __init__(self, bank_id, server_url):
        self.bank_id = bank_id
        self.rest_url = "http://" + server_url + "/api/"
        self.ws_url = "ws://" + server_url
        self.bank_accounts = {}
        self.transaction_queue = mp.Queue() # populated by bank accounts
        self.api = FundClearingApi(self.rest_url)
        self.banking_participant = self.api.get_banking_participant(self.bank_id)
        self.currency = self.banking_participant.working_currency
        try:
            # create worker processes for transaction queue
            num_workers = 1
            for _ in range(num_workers):
                worker = mp.Process(target=self.handle_transfer_queue, args=(self.transaction_queue,))
                worker.start()
            # create a single process to submit batch transfer create requests
            worker = mp.Process(target=self.create_batch_transfer_requests)
            worker.start()
            # create a thread to listen for batch transfer request created events
            worker = threading.Thread(target=self.btr_created_listener)
            worker.start()

        except KeyboardInterrupt:
            return

    def create_bank_account(self, account_id, balance):
        bank_account = BankAccount(
            account_id, 
            self.bank_id, 
            self.currency, 
            balance, 
            self.transaction_queue
        )
        self.bank_accounts[account_id] = bank_account
        logger.debug(f'{self.bank_id}: Created account: {account_id}')
        return bank_account

    def get_bank_account_by_id(self, id):
        '''
        returns the BankAccount object referenced by id
        '''
        return self.bank_accounts[id]

    def update_banking_participant(self):
        '''
        used to refresh banking participant data from composer network, particularly the balance
        '''
        self.banking_participant = self.api.get_banking_participant(self.bank_id)

    def handle_transfer_queue(self, tx_queue):
        '''
        when a bank account reqeusts a fund transfer, it's placed on the tx_queue
        and handled here
        '''
        try:
            while True:
                transfer = tx_queue.get() # removed tx from queue
                # prepare transfer request parameters
                transfer_id = str(uuid.uuid4())
                to_bank = transfer.to_bank
                state = "PENDING"
                details = fund_clearing_python_sdk.Transfer(
                    currency = transfer.currency,
                    amount = transfer.amount,
                    from_account = transfer.from_account,
                    to_account = transfer.to_account
                )
                data = fund_clearing_python_sdk.SubmitTransferRequest(
                    transfer_id = transfer_id, 
                    to_bank = to_bank,
                    state = state,
                    details = details
                )
                request_number = random.randint(1000,9999)
                logger.debug(f'{self.bank_id}: tx request - Posting {transfer_id}')
                try:
                    result = self.api.post_transfer_request(data)
                    #logger.debug("tx request #{} - Result: {}".format(request_number, result))
                    if result.transfer_id != transfer_id:
                        raise ValueError(request_number, result.transfer_id, transfer_id)
                except ValueError as e:
                    logger.debug(f'ERROR: api.post_transfer_request result transfer id ' \
                    f'does not match request transfer id. request {e.args[0]}: {e.args[1]} != {e.args[2]}')
        except KeyboardInterrupt:
            return

    def create_batch_transfer_requests(self):
        '''
        periodically, the bank will request that the fund-clearing composer network create BatchTransferRequest assets
        '''
        try:
            while True:
                sleep(random.randint(5,20))
                btr_id = str(uuid.uuid4())
                logger.debug(f'{self.bank_id}: BTR request - Posting {btr_id}')
                self.api.post_batch_transfer_request(btr_id)
        except KeyboardInterrupt:
            return

    '''
    def btr_created_event_loop(self):
    '''
    #setup asyncio event loop and listen for batch created events on websockets
    '''
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.btr_created_event_listener())
        except KeyboardInterrupt:
            loop.close()
        else:
            loop.close()
    '''

    def btr_created_listener(self):
        ws = create_connection(self.ws_url)
        try:
            while True:
                message = json.loads(ws.recv())
                logger.debug(f'{self.bank_id}: ws>{message["batchId"]}')
                self.handle_btr(message['batchId'])
        except KeyboardInterrupt:
            return
    

    '''
    async def btr_created_event_listener(self):
    '''
       # websocket listening for batch create events
       # when detected, spawn a new process to handle the BTR
    '''
        try:
            async with websockets.connect(self.ws_url) as websocket:
                while True:
                    message = json.loads(await websocket.recv())
                    logger.debug(f'ws> {message["batchId"]}')
                    if self.bank_id in message['batchId']: # is our bank part of this batch?
                        # spawn a new process to handle the BTR lifecycle
                        worker = mp.Process(target=self.handle_btr, args=(message['batchId'],))
                        worker.start()
                        worker.join()
        except KeyboardInterrupt:
            return
    '''
    def handle_btr(self, btr_id):
        '''
        process Batch Transfer Request asset lifecycle:
        1) retrieve BTR asset details
        2) for each transfer request contained, set internal account's fundtransfer to paid in principal
        3) submit mark preprocess complete on BTR and wait for state to be READY_TO_SETTLE
        4) for each transfer request contained, debit or credit account's balance, and mark fundtransfer to paid, and submit postprocessing complete transaction
        5) wait for BTR state to be COMPLETE
        6) for each transfer request contained, if from bank = true, remove transfer request asset from fund-clearing network
        7) if originating bank in the BTR id, remove BTR asset from fund-clearing network
        8) update banking participant (to refresh bank balance)
        '''
        trace_code = random.randint(1000, 9999)
        logger.info(f'{self.bank_id}: Processing BTR [{trace_code}]: {btr_id}')
        # 1) retrieve BTR asset details
        btr = self.api.get_batch_transfer_request(btr_id)
        transfer_requests = btr.transfer_requests
        # 2) for each txreq, set account's fundtransfer to paid in principal and submit preprocessing complete transaction
        for txreq in transfer_requests:
            tx_trace_code = random.randint(100, 999)
            txreq = txreq.split('#')[1]
            logger.debug(f'{self.bank_id}: [{trace_code}-{tx_trace_code}]: preprocessing started: {txreq}')
            # 2a) retrieve txreq details from composer network
            tx = self.api.get_transfer_request(txreq)
            # 2b) are we "to_bank" or "from_bank", and which account to credit or debit?
            amount = tx.details.amount
            if self.bank_id in tx.to_bank: # credit = True
                # update internal record
                target_account = int(tx.details.to_account)
                acct = self.bank_accounts[target_account]
                #print('-------------------------')
                #print(acct.get_transaction_history())
                #print('-------------------------')
                logger.debug(f'{self.bank_id}: [{trace_code}-{tx_trace_code}]: Credit Account={target_account}: Amount={amount}')
            elif self.bank_id in tx.from_bank: # debit = True
                # update internal record
                target_account = int(tx.details.from_account)
                acct = self.bank_accounts[target_account]
                logger.debug(f'{self.bank_id}: [{trace_code}-{tx_trace_code}]: Debit Account={target_account}: Amount={amount}')
        # 3) submit mark preprocess complete on BTR and wait for state to be READY_TO_SETTLE
        data = fund_clearing_python_sdk.MarkPreProcessComplete(
            batch_id = btr_id
        )
        self.api.mark_preprocess_complete(data)
        logger.debug(f'{self.bank_id}: [{trace_code}]: preprocessing complete: {txreq}')


    def __repr__(self):
        return f'{self.bank_id}:\n\t-accounts:{self.bank_accounts}\n\t-banking participant:\n{self.banking_participant}\n\t-transaction queue count:{self.transaction_queue.qsize()}'
