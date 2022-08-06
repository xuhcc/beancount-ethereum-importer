# Ethereum transaction importer for Beancount

## Configuration

Example of configuration file: [config.json](config.json.example).

`beancount-ethereum` can load data from [Etherscan](https://etherscan.io/) or block explorers with similar API like [Blockscout](https://blockscout.com/poa/xdai/).

If you are using Etherscan, get your API key at https://etherscan.io/.

## Install

Install `beancount-ethereum`:

```
pip install beancount-ethereum
```

To install from source:

```
pip install -e .
```

## Usage

Download transactions to file:

```
beancount-ethereum --config=config.json --output-dir=downloads
```

Add importer to import configuration ([example](import_config.py.example)):

```
import beancount_ethereum

CONFIG = [
    beancount_ethereum.importer.Importer(config_path='config.json'),
]
```

Check with `bean-identify`:

```
bean-identify import_config.py downloads
```

Import transactions with `bean-extract`:

```
bean-extract -e test.beancount import_config.py downloads
```

## Deploy

Deploy `beancount-ethereum`:

```
make deploy
```
