# Ethereum transaction importer for Beancount

## Configuration

Example of configuration file: [config.json](config.json.example).

## Usage

Get API key on https://etherscan.io/

Download transactions to file:

```
python beancount_ethereum/downloader.py --config=config.json --output-dir=downloads
```

Add importer to import configuration ([example](import_config.py)):

```
import beancount_ethereum

CONFIG = [
    beancount_ethereum.importer.Importer(config='config.json'),
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
