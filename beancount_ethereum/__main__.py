import argparse
import json
import os
from .downloader import download


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-c', '--config',
                            default='config.json')
    arg_parser.add_argument('-o', '--output-dir',
                            default='downloads')
    args = arg_parser.parse_args()
    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
    output_dir = os.path.join(os.getcwd(), args.output_dir)
    download(config, output_dir)


if __name__ == '__main__':
    main()
