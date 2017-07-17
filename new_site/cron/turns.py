import sys
import os

from datetime import (
    datetime,
    timedelta
)
import configparser
import transaction

import schedule
import time

from sqlalchemy import (
    engine_from_config,
    MetaData,
    Table
)

from sqlalchemy.orm import (
    mapper,
    sessionmaker
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s ..\..\development.ini")' % (cmd, cmd))
    sys.exit(1)


class Player:
    pass


class Hex:
    pass


def create_session(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    config = configparser.ConfigParser()
    config.read(config_uri)
    options = config['app:main']
    engine = engine_from_config(options, 'sqlalchemy.')

    metadata = MetaData(engine)

    hexes = Table('hexes', metadata, autoload=True)
    mapper(Hex, hexes)

    players = Table('players', metadata, autoload=True)
    mapper(Player, players)

    _session = sessionmaker(bind=engine)
    session = _session()
    return session

DBSession = create_session()


def calc_hex_controls():
    hex_stats = dict()

    for l in DBSession.query(Hex).all():
        hex_stats[l.name] = {'Blue': 0, 'Yellow': 0, 'Black': 0, 'Red': 0, 'None': 0.1}
        blue = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Blue')
        red = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Red')
        yellow = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Yellow')
        black = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Black')
        for b in blue.all():
            hex_stats[l.name]['Blue'] += b.troops
        for y in yellow.all():
            hex_stats[l.name]['Yellow'] += y.troops
        for r in red.all():
            hex_stats[l.name]['Red'] += r.troops
        for bl in black.all():
            hex_stats[l.name]['Black'] += bl.troops

        total = sum(hex_stats[l.name].values()) - 0.1

        for k in hex_stats[l.name].keys():
            if k != 'None':
                hex_stats[l.name][k] = (hex_stats[l.name][k] * 2) - total

        control = [key for m in [max(hex_stats[l.name].values())] for key, val in hex_stats[l.name].items() if val == m]

        for k in hex_stats[l.name].keys():
            if hex_stats[l.name][k] < 0:
                hex_stats[l.name][k] = 0
        if len(control) > 1:
            hex_stats[l.name]['control'] = 'None'
        else:
            hex_stats[l.name]['control'] = control[0]

    return hex_stats


def update_hex_control():
        hexes = calc_hex_controls()

        with transaction.manager:
            for loc, ctrl in hexes.items():
                DBSession.query(Hex).filter(Hex.name == loc).update({Hex.control: ctrl['control'], Hex.blue: ctrl['Blue'],
                                                                     Hex.yellow: ctrl['Yellow'], Hex.red: ctrl['Red'],
                                                                     Hex.black: ctrl['Black']})

            DBSession.commit()


def update_hex_resources():
    with transaction.manager:
            DBSession.query(Hex).update({Hex.ammo: Hex.industry + Hex.ammo, Hex.population: Hex.population + Hex.infrastructure})
            DBSession.commit()


def deactivate_inactive_players():
    now = datetime.now()
    fortnight = now - timedelta(days=14)

    with transaction.manager:
        DBSession.query(Player).filter(Player.is_active).filter(Player.last_active < fortnight).update({Player.is_active: False})
        DBSession.commit()


def increase_actions():
    with transaction.manager:
        DBSession.query(Player).filter(Player.is_active).filter(Player.actions <= 9).update({Player.actions: Player.actions + 1})
        DBSession.commit()


def increase_morale():

    with transaction.manager:
        DBSession.query(Player).filter(Player.is_active).filter(Player.morale <= 99).update({Player.morale: Player.morale + 1})
        DBSession.commit()


def turn():
    start = datetime.now()
    print("Turn starting at {}".format(start))
    update_hex_control()
    update_hex_resources()
    deactivate_inactive_players()
    increase_actions()
    increase_morale()
    end = datetime.now()
    print("Turn ran successfully, took {}\n".format(end-start))

schedule.every(10).seconds.do(turn)

print('\n')
while True:
    schedule.run_pending()
    time.sleep(5)
