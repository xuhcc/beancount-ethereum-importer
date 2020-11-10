import datetime
import json
import os
from itertools import groupby

from beancount.ingest.importer import ImporterProtocol
from beancount.core.amount import Amount
from beancount.core.data import EMPTY_SET, Posting, Transaction, new_metadata
from beancount.core.number import D


class Importer(ImporterProtocol):

    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as config_file:
            self.config = json.load(config_file)

    def name(self) -> str:
        return 'ethereum'

    def identify(self, file) -> bool:
        name = self.config['name']
        return os.path.basename(file.name) == f'{name}.json'

    @property
    def account_map(self):
        return {key.lower(): value for key, value
                in self.config['account_map'].items()}

    def _find_account(
        self,
        address: str,
        value: D,
        currency: str,
    ) -> str:
        if address == '0xffffffffffffffffffffffffffffffffffffffff':
            assert currency == 'ETH'
            account = self.config['fee_account']
        else:
            if address not in self.account_map:
                if value > 0:
                    account = self.config['expenses_account']
                else:
                    account = self.config['income_account']
            else:
                account = f'{self.account_map[address]}:{currency.upper()}'
        return account

    def extract(self, file, existing_entries=None) -> list:
        # TODO: check for duplicates
        with open(file.name, 'r') as _file:
            transactions = json.load(_file)
        entries = []
        key_func = lambda tx: tx['tx_id']  # noqa: E731
        transactions = sorted(transactions, key=key_func)
        for tx_id, transfers in groupby(transactions, key_func):
            tx_date = None
            metadata = {'txid': tx_id}
            postings = []
            for transfer in transfers:
                if tx_date is None:
                    tx_date = datetime.datetime.\
                        fromtimestamp(transfer['time']).date()
                value = D(transfer['value'])
                if value == 0:
                    continue
                account_from = self._find_account(
                    transfer['from'],
                    -value,
                    transfer['currency'],
                )
                posting_from = Posting(
                    account_from,
                    Amount(-value, transfer['currency'].upper()),
                    None, None, None, None,
                )
                postings.append(posting_from)
                account_to = self._find_account(
                    transfer['to'],
                    value,
                    transfer['currency'],
                )
                posting_to = Posting(
                    account_to,
                    Amount(value, transfer['currency'].upper()),
                    None, None, None, None,
                )
                postings.append(posting_to)

            entry = Transaction(
                new_metadata('', 0, metadata),
                tx_date,
                '*',
                '',
                '',
                EMPTY_SET,
                EMPTY_SET,
                postings,
            )
            entries.append(entry)

        return entries
