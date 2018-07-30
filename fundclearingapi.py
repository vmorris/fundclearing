import json
from time import sleep

import fund_clearing_python_sdk
from fund_clearing_python_sdk.rest import ApiException

import logging
from logging.config import fileConfig

fileConfig('logging_config.ini')
logger = logging.getLogger()

class FundClearingApi(object):
    """FundClearingApi wraps fund_clearing_python_sdk configuration and apis"""

    def __init__(self, api_endpoint):
        self.api_config = fund_clearing_python_sdk.Configuration()
        self.api_config.host = api_endpoint
        self.api_client = fund_clearing_python_sdk.ApiClient(self.api_config)

    def get_banking_participant(self, id):
        api = fund_clearing_python_sdk.BankingParticipantApi(self.api_client)
        return api.banking_participant_find_by_id(id)

    def post_transfer_request(self, data):
        api = fund_clearing_python_sdk.SubmitTransferRequestApi(self.api_client)
        return api.submit_transfer_request_create(data=data)

    def get_transfer_request(self, id):
        api = fund_clearing_python_sdk.TransferRequestApi(self.api_client)
        return api.transfer_request_find_by_id(id)

    def post_batch_transfer_request(self, id):
        usd_rates = [
            fund_clearing_python_sdk.UsdExchangeRate(to='EURO',rate=0.75)
        ]
        data = fund_clearing_python_sdk.CreateBatch(
            batch_id = id,
            usd_rates = usd_rates
        )
        api = fund_clearing_python_sdk.CreateBatchApi(self.api_client)
        try:
            return api.create_batch_create(data=data)
        except fund_clearing_python_sdk.rest.ApiException as e:
            logger.debug("WARNING: when sending CreateBatch transaction: " + json.loads(e.body)["error"]["message"])

    def get_batch_transfer_request(self, id):
        api = fund_clearing_python_sdk.BatchTransferRequestApi(self.api_client)
        return api.batch_transfer_request_find_by_id(id)

    def mark_preprocess_complete(self, data):
        while True:
            api = fund_clearing_python_sdk.MarkPreProcessCompleteApi(self.api_client)
            try: 
                result = api.mark_pre_process_complete_create(data=data)
                if isinstance(result, fund_clearing_python_sdk.MarkPreProcessComplete):
                    break # result looks okay
            except fund_clearing_python_sdk.rest.ApiException as e:
                if e.status == 500:
                    sleep(1)
                    logger.debug("WARNING: when sending MarkPreprocessComplete transaction: " + json.loads(e.body)["error"]["message"])
                    pass # we'll back off and keep trying
                else:
                    raise e
        return result
