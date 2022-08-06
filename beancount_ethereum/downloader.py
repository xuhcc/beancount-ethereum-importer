import argparse
import json
import os
import time
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_CURRENCY = 'ETH'
MINER = '0xffffffffffffffffffffffffffffffffffffffff'
WEI = 10 ** 18
NO_TRANSACTIONS = [
    'No transactions found',
    'No internal transactions found',
    'No token transfers found',
]


class BlockExplorerApi:

    def __init__(self, api_url: str, api_key: str, delay: float = 0.0, base_currency: str = DEFAULT_CURRENCY):
        self.api_url = api_url
        self.api_key = api_key
        self.delay = delay
        self._last_request_timestamp = 0.0
        self.base_currency = base_currency

    def _make_api_request(self, address: str, action: str) -> list:
        """
        Load data from block explorer API
        """
        last_request_delta = time.time() - self._last_request_timestamp
        if last_request_delta < self.delay:
            time.sleep(self.delay - last_request_delta)
        params = {
            'module': 'account',
            'action': action,
            'address': address,
            'sort': 'asc',
        }
        if self.api_key is not None:
            params['apikey'] = self.api_key
        url = f'{self.api_url}?{urlencode(params)}'
        request = Request(url)
        request.add_header('Content-Type', 'application/json')
        request.add_header('Accept', 'application/json')
        request.add_header('User-Agent', 'python-requests/2.24.0')
        response = urlopen(request).read()
        self._last_request_timestamp = time.time()
        data = json.loads(response)
        if int(data['status']) == 1 or data['message'] in NO_TRANSACTIONS:
            return data['result']
        else:
            raise RuntimeError(response)

    def get_normal_transactions(self, address: str) -> list:
        transactions = []
        for item in self._make_api_request(address, 'txlist'):
            if int(item['isError']) == 0:
                transaction = {
                    'tx_id': item['hash'],
                    'time': int(item['timeStamp']),
                    'from': item['from'],
                    'to': item['to'],
                    'currency': self.base_currency,
                    'value': Decimal(item['value']) / WEI,
                }
                transactions.append(transaction)
            if item['from'].lower() == address.lower():
                transaction_fee = {
                    'tx_id': item['hash'],
                    'time': int(item['timeStamp']),
                    'from': item['from'],
                    'to': MINER,
                    'currency': self.base_currency,
                    'value': (Decimal(item['gasUsed']) *
                              Decimal(item['gasPrice']) /
                              WEI),
                }
                transactions.append(transaction_fee)
        return transactions

    def get_internal_transactions(self, address: str) -> list:
        transactions = []
        for item in self._make_api_request(address, 'txlistinternal'):
            transaction = {
                # Blockscout uses 'transactionHash' instead of 'hash'
                'tx_id': (item['hash'] if 'hash' in item
                          else item['transactionHash']),
                'time': int(item['timeStamp']),
                'from': item['from'],
                'to': item['to'],
                'currency': self.base_currency,
                'value': Decimal(item['value']) / WEI,
            }
            transactions.append(transaction)
        return transactions

    def get_erc20_transfers(self, address: str) -> list:
        transactions = []
        for item in self._make_api_request(address, 'tokentx'):
            if item['tokenDecimal'] == '':
                # Skip NFTs (Blockscout)
                continue
            transaction = {
                'tx_id': item['hash'],
                'time': int(item['timeStamp']),
                'from': item['from'],
                'to': item['to'],
                'currency': item['tokenSymbol'],
                'value': (Decimal(item['value']) /
                          10 ** Decimal(item['tokenDecimal'])),
            }
            transactions.append(transaction)
        return transactions


def download(config: dict, output_dir: str):
    name = config['name']
    addresses = config['account_map'].keys()
    api = BlockExplorerApi(
        config['block_explorer_api_url'],
        config['block_explorer_api_key'],
        config.get('block_explorer_api_request_delay', 0.0),
        config.get('base_currency', DEFAULT_CURRENCY),
    )
    transactions = []
    for address in addresses:
        transactions += api.get_normal_transactions(address)
        transactions += api.get_internal_transactions(address)
        transactions += api.get_erc20_transfers(address)
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, f'{name}.json')
    with open(output_file_path, 'w') as output_file:
        json.dump(transactions, output_file, indent=4, default=str)
    print(f'Transactions saved to {output_file_path}')

