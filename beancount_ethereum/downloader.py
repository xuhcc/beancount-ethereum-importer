import argparse
import json
import os
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ETHERSCAN_API_URL = 'http://api.etherscan.io/api'
MINER = '0xffffffffffffffffffffffffffffffffffffffff'
WEI = 10 ** 18


def load_from_etherscan(api_key: str, address: str, action: str) -> list:
    """
    https://etherscan.io/apis#accounts
    """
    params = {
        'module': 'account',
        'action': action,
        'address': address,
        'sort': 'asc',
        'apikey': api_key,
    }
    url = f'{ETHERSCAN_API_URL}?{urlencode(params)}'
    request = Request(url)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Accept', 'application/json')
    response = urlopen(request).read()
    data = json.loads(response)
    if int(data['status']) == 1 or data['message'] == 'No transactions found':
        return data['result']
    else:
        raise RuntimeError(response)


def get_normal_transactions(api_key: str, address: str) -> list:
    transactions = []
    for item in load_from_etherscan(api_key, address, 'txlist'):
        if int(item['isError']) == 0:
            transaction = {
                'tx_id': item['hash'],
                'time': int(item['timeStamp']),
                'from': item['from'],
                'to': item['to'],
                'currency': 'ETH',
                'value': Decimal(item['value']) / WEI,
            }
            transactions.append(transaction)
        if item['from'].lower() == address.lower():
            transaction_fee = {
                'tx_id': item['hash'],
                'time': int(item['timeStamp']),
                'from': item['from'],
                'to': MINER,
                'currency': 'ETH',
                'value': (Decimal(item['gasUsed']) *
                          Decimal(item['gasPrice']) /
                          WEI),
            }
            transactions.append(transaction_fee)
    return transactions


def get_internal_transactions(api_key: str, address: str) -> list:
    transactions = []
    for item in load_from_etherscan(api_key, address, 'txlistinternal'):
        transaction = {
            'tx_id': item['hash'],
            'time': int(item['timeStamp']),
            'from': item['from'],
            'to': item['to'],
            'currency': 'ETH',
            'value': Decimal(item['value']) / WEI,
        }
        transactions.append(transaction)
    return transactions


def get_erc20_transfers(api_key: str, address: str) -> list:
    transactions = []
    for item in load_from_etherscan(api_key, address, 'tokentx'):
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


def main(config: dict, output_dir: str):
    addresses = config['account_map'].keys()
    api_key = config['etherscan_api_key']
    transactions = []
    for address in addresses:
        transactions += get_normal_transactions(api_key, address)
        transactions += get_internal_transactions(api_key, address)
        transactions += get_erc20_transfers(api_key, address)
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, 'transactions.json')
    with open(output_file_path, 'w') as output_file:
        json.dump(transactions, output_file, indent=4, default=str)
    print(f'Transactions saved to {output_file_path}')


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-c', '--config',
                            default='config.json')
    arg_parser.add_argument('-o', '--output-dir',
                            default='downloads')
    args = arg_parser.parse_args()
    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
    output_dir = os.path.join(os.getcwd(), args.output_dir)
    main(config, output_dir)
