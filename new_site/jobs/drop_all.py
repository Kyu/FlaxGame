import configparser
import os
import sys

import transaction
from sqlalchemy import (
    engine_from_config,
    MetaData,
    Table
)


def usage(argv):
    # If script run without arguments. Argument needs to point to config file that holds sqlalchemy options
    cmd = os.path.basename(argv[0])
    print('usage: do(<config_uri>)\n'
          '(example: do(development.ini))')
    sys.exit(1)


def create(path):
    if not path:
        usage(path)

    # Getting settings from file specified.
    config_uri = path
    config = configparser.ConfigParser()
    config.read(config_uri)
    options = config['app:main']
    engine = engine_from_config(options, 'sqlalchemy.')

    metadata = MetaData(engine)

    hexes = Table('hexes', metadata, autoload=True)
    players = Table('players', metadata, autoload=True)
    radio = Table('radio', metadata, autoload=True)
    teams = Table('teams', metadata, autoload=True)
    users = Table('users', metadata, autoload=True)
    return hexes, players, radio, teams, users


def do(path=''):
    tables = create(path)
    with transaction.manager:
        # Drops tables
        for i in tables:
            i.drop()

    print("Done!")