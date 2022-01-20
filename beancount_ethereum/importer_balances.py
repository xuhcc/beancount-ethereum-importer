import datetime
import json
import os

from beancount.ingest.importer import ImporterProtocol
from beancount.core.amount import Amount
from beancount.core.data import Balance, new_metadata
from beancount.core.number import D

DEFAULT_CURRENCY = 'ETH'


class Importer(ImporterProtocol):

    def __init__(
        self,
        config_path='config.json',
    ):
        with open(config_path, 'r') as config_file:
            self.config = json.load(config_file)

    def name(self) -> str:
        return 'ethereum_balances'

    def identify(self, file) -> bool:
        name = self.config['name']
        return os.path.basename(file.name) == f'{name}-balances.json'

    @property
    def account_map(self) -> dict:
        return {key.lower(): value for key, value
                in self.config['account_map'].items()}

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

    def extract(self, file, existing_entries=None) -> list:

        with open(file.name, 'r') as _file:
            balances = json.load(_file)
        entries = []

        for record in balances:
            meta = new_metadata(file.name, 0)
            balance_date = datetime.datetime.fromtimestamp(record['time'])
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
