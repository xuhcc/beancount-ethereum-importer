import json
import os
import pickle
from decimal import Decimal
from itertools import groupby

from beancount.ingest import importer
from beancount.core import amount, data
from beancount.core.number import D


class Importer(importer.ImporterProtocol):

    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as config_file:
            self.config = json.load(config_file)

    def name(self) -> str:
        return 'ethereum'

    def identify(self, file) -> bool:
        return 'transactions.pickle' == os.path.basename(file.name)

    @property
    def account_map(self):
        return {key.lower(): value for key, value
                in self.config['account_map'].items()}

    def _find_account(
        self,
        address: str,
        amount: Decimal,
        currency: str,
    ) -> str:
        if address == '0xffffffffffffffffffffffffffffffffffffffff':
            assert currency == 'ETH'
            account = self.config['fee_account']
        else:
            if address not in self.account_map:
                if amount > 0:
                    account = self.config['expenses_account']
                else:
                    account = self.config['income_account']
            else:
                account = f'{self.account_map[address]}:{currency}'
        return account

    def extract(self, file, existing_entries=None) -> list:
        # TODO: check for duplicates
        with open(file.name, 'rb') as _file:
            transactions = pickle.load(_file)
        entries = []
        key_func = lambda tx: tx['tx_id']  # noqa: E731
        transactions = sorted(transactions, key=key_func)
        for tx_id, transfers in groupby(transactions, key_func):
            tx_date = None
            metadata = {'txid': tx_id}
            postings = []
            for transfer in transfers:
                if tx_date is None:
                    tx_date = transfer['time'].date()
                if transfer['value'] == 0:
                    continue
                account_from = self._find_account(
                    transfer['from'],
                    -transfer['value'],
                    transfer['currency'],
                )
                posting_from = data.Posting(
                    account_from,
                    amount.Amount(D(-transfer['value']), transfer['currency']),
                    None, None, None, None,
                )
                postings.append(posting_from)
                account_to = self._find_account(
                    transfer['to'],
                    transfer['value'],
                    transfer['currency'],
                )
                posting_to = data.Posting(
                    account_to,
                    amount.Amount(D(transfer['value']), transfer['currency']),
                    None, None, None, None,
                )
                postings.append(posting_to)

            entry = data.Transaction(
                data.new_metadata('', 0, metadata),
                tx_date,
                '*',
                '',
                '',
                data.EMPTY_SET,
                data.EMPTY_SET,
                postings,
            )
            entries.append(entry)

        return entries
