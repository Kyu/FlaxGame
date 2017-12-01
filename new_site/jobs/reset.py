import configparser
import sys
from datetime import datetime

import transaction
from sqlalchemy import (
    engine_from_config,
    MetaData,
    Table
)


def usage(argv):
    # If script run without arguments. Argument needs to point to config file that holds sqlalchemy options
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
    return {'hexes': hexes, 'players': players, 'radio': radio, 'teams': teams, 'users': users}


def hard(path=''):
    tables = create(path)
    with transaction.manager:
        # Drops tables
        for i in list(tables.values()):
            i.drop()

    print("Done!")


def soft(path='', full=False):
    if not path:
        usage(path)
    from ..models import Radio, gen_hexes, gen_player
    from .models import Hex, Player, create_session
    # Not sure why I have two of these but OK

    DBSession = create_session(path)

    with transaction.manager:
        old_hexes = DBSession.query(Hex).delete()
        DBSession.add_all(gen_hexes())
        players = DBSession.query(Player)
        now = datetime.utcnow().strftime('%D - %H:%M:%S')
        DBSession.add(Radio(author='Admin', message='Game reset at {0}'.format(now), team='all'))
        for player in players:
            stats = gen_player()

            player.team = stats['team']
            player.squad_type = stats['squad']
            player.location = stats['location']
            player.troops = stats['troops']
            player.ammo = 200
            player.morale = 100
            player.actions = 10

            if full:
                player.level = 1
                player.experience = 0
                player.management = 1
                player.attack = 1
                player.defense = 1
                player.charisma = 1
                player.rallying = 1
                player.pathfinder = 1
                player.logistics = 1
                player.development = 1

        DBSession.commit()
    print("Done")
