import configparser
import os
import sys

import transaction
from sqlalchemy import (
    engine_from_config,
    MetaData,
    Table
)
from sqlalchemy.orm import (
    mapper,
    sessionmaker
)

from .models import *


def usage(argv):
    # If script run without arguments. Argument needs to point to config file that holds sqlalchemy options
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s ..\..\development.ini")' % (cmd, cmd))
    sys.exit(1)

argv = sys.argv

if len(argv) != 2:
    usage(argv)

# Getting settings from file specified.
config_uri = argv[1]
config = configparser.ConfigParser()
config.read(config_uri)
options = config['app:main']
engine = engine_from_config(options, 'sqlalchemy.')


# Loading Classes from tables.
metadata = MetaData(engine)

hexes = Table('hexes', metadata, autoload=True)
mapper(Hex, hexes)

players = Table('players', metadata, autoload=True)
mapper(Player, players)

radio = Table('radio', metadata, autoload=True)
mapper(Radio, radio)

teams = Table('teams', metadata, autoload=True)
mapper(Teams, teams)

users = Table('users', metadata, autoload=True)
mapper(Users, users)

# Create session
_session = sessionmaker(bind=engine)
DBSession = _session()

with transaction.manager:
    # Drops tables
    hexes.drop()
    players.drop()
    radio.drop()
    teams.drop()
    users.drop()

print("Done!")