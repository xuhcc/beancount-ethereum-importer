import datetime
import json
import os
from itertools import groupby

from beancount.ingest.importer import ImporterProtocol
from beancount.core.amount import Amount
from beancount.core.data import EMPTY_SET, Posting, Transaction, new_metadata, Balance
from beancount.core.number import D

DEFAULT_CURRENCY = 'ETH'
MINER = '0xffffffffffffffffffffffffffffffffffffffff'


class Importer(ImporterProtocol):
    def __init__(
        self,
        config_path='config.json',
        max_delta=90,  # days
        import_balances=False,
    ):
        with open(config_path, 'r') as config_file:
            self.config = json.load(config_file)
        self.min_date = datetime.datetime.now() - datetime.timedelta(days=max_delta)
        self.import_balances = import_balances

    def name(self) -> str:
        return 'ethereum'

    def identify(self, file) -> bool:
        name = self.config['name']
        return os.path.basename(file.name) == f'{name}.json'  or (
            self.import_balances
            and os.path.basename(file.name) == f'{name}-balances.json'
        )

    @property
    def account_map(self) -> dict:
        return {key.lower(): value for key, value in self.config['account_map'].items()}

    def account_suffix(self, currency: str) -> str:
        if 'currency_map' in self.config:
            if currency in self.config['currency_map']:
                if 'account_suffix' in self.config['currency_map'][currency]:
                    return self.config['currency_map'][currency]['account_suffix']
                else:
                    return self.config['currency_map'][currency]['commodity']
            else:
                return currency
        else:
            return currency

    def commodity(self, currency: str) -> str:
        if 'currency_map' in self.config:
            if currency in self.config['currency_map']:
                return self.config['currency_map'][currency]['commodity']
            else:
                return currency
        else:
            return currency

    def _create_posting(
        self,
        address: str,
        value: D,
        currency: str,
    ) -> tuple:
        if address == MINER:
            assert currency == self.config.get('base_currency', DEFAULT_CURRENCY)
            account = self.config['fee_account']
            payee = None
        else:
            if address not in self.account_map:
                if value == 0:
                    # Do not create posting
                    account = None
                elif value > 0:
                    account = self.config['expenses_account']
                else:
                    account = self.config['income_account']
                payee = address
            else:
                if value == 0:
                    # Do not create posting
                    account = None
                else:
                    account = (
                        f"{self.account_map[address]}:{self.account_suffix(currency)}"
                    )
                payee = None
        if account:
            posting = Posting(
                account,
                Amount(value, self.commodity(currency)),
                None,
                None,
                None,
                None,
            )
        else:
            posting = None
        return posting, payee

    def extract_balances(self, file) -> list:

        with open(file.name, 'r') as _file:
            balances = json.load(_file)
        entries = []

        for record in balances:
            meta = new_metadata(file.name, 0)
            balance_date = datetime.datetime.fromtimestamp(record["time"])
            currency = record['currency']
            account = f"{self.account_map[record['address']]}:{self.account_suffix(currency)}"
            balance = record['balance']

            entry = Balance(
                meta,
                balance_date,
                account,
                Amount(D(balance), self.commodity(currency)),
                None,
                None,
            )

            entries.append(entry)
        return entries

    def extract_transactions(self, file, existing_entries=None) -> list:
        # Get list of existing transactions
        existing_txs = []
        if existing_entries is not None:
            for item in existing_entries:
                if isinstance(item, Transaction) and 'txid' in item.meta:
                    existing_txs.append(item.meta['txid'])

        # Load new transactions
        with open(file.name, 'r') as _file:
            transactions = json.load(_file)
        entries = []
        sorted_transactions = sorted(
            transactions,
            key=lambda tx: (tx['time'], tx['tx_id']),
        )
        grouped_transactions = groupby(
            sorted_transactions,
            lambda tx: tx['tx_id'],
        )
        for tx_id, transfers in grouped_transactions:
            tx_date = None
            metadata = {'txid': tx_id}
            postings = []
            payees = []
            for transfer in transfers:
                if tx_date is None:
                    tx_date = datetime.datetime.fromtimestamp(transfer['time'])
                value = D(transfer['value'])
                posting_from, payee = self._create_posting(
                    transfer['from'],
                    -value,
                    transfer['currency'].upper(),
                )
                if posting_from:
                    postings.append(posting_from)
                if payee:
                    payees.append(payee)
                posting_to, payee = self._create_posting(
                    transfer['to'],
                    value,
                    transfer['currency'].upper(),
                )
                if posting_to:
                    postings.append(posting_to)
                if payee is not None:
                    payees.append(payee)

            if tx_id in existing_txs:
                continue
            if tx_date < self.min_date:
                continue

            entry = Transaction(
                new_metadata('', 0, metadata),
                tx_date.date(),  # type: ignore
                '*',
                ', '.join(payees),
                '',
                EMPTY_SET,
                EMPTY_SET,
                postings,
            )
            entries.append(entry)

        return entries

    def extract(self, file, existing_entries=None) -> list:
        if file.name.endswith('balances.json'):
            return self.extract_balances(file)
        else:
            return self.extract_transactions(file, existing_entries)
