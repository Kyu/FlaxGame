import configparser
import sys
from sqlalchemy import (
    engine_from_config,
    MetaData,
    Table
)
from sqlalchemy.orm import (
    mapper,
    sessionmaker
)


# Empty classes to represent tables
class Player:
    pass


class Hex:
    pass


class Radio:
    pass


class Teams:
    pass


class Users:
    pass


class Avatar:
    pass


def usage():
    # If script run without arguments. Argument needs to point to config file that holds sqlalchemy options
    print('usage: create_session(<config_uri>)\n'
          '(example: "create_session(\'..\..\development.ini\')')
    sys.exit(1)


def create_session(path):
    if not path:
        usage()

    # Getting settings from file specified.
    config_uri = path
    config = configparser.ConfigParser()
    config.read(config_uri)
    options = config['app:main']
    engine = engine_from_config(options, 'sqlalchemy.')

    global turn_time
    turn_time = int(options['turn_time'])

    # Loading Classes from tables.
    metadata = MetaData(engine)

    hexes = Table('hexes', metadata, autoload=True)
    mapper(Hex, hexes)

    players = Table('players', metadata, autoload=True)
    mapper(Player, players)

    # Create and return session
    _session = sessionmaker(bind=engine)
    session = _session()
    return session