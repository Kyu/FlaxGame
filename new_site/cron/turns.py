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
    # If script run without arguments. Argument needs to point to config file that holds sqlalchemy options
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s ..\..\development.ini")' % (cmd, cmd))
    sys.exit(1)


class Player:
    # Empty class that will later represent `players` table
    pass


class Hex:
    # Empty class that will later represent `hexes` table
    pass


def create_session(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    # Getting settings from file specified.
    config_uri = argv[1]
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

# The DBSession
DBSession = create_session()


# TODO D-R-Y

def determine_hex_controllers():
    hex_stats = dict()

    with transaction.manager:
        for l in DBSession.query(Hex).all():
            hex_stats[l.name] = {'Blue': l.blue, 'Yellow': l.yellow, 'Black': l.black, 'Red': l.red, 'None': 0.1}

            control = \
                [key for m in [max(hex_stats[l.name].values())] for key, val in hex_stats[l.name].items() if val == m]

            # If more than one control, None is the controller.
            if len(control) > 1:
                hex_stats[l.name]['control'] = 'None'
            else:
                hex_stats[l.name]['control'] = control[0]

        for loc, ctrl in hex_stats.items():
            DBSession.query(Hex).filter(Hex.name == loc).update({Hex.control: ctrl['control']})

        DBSession.commit()


def fix_hex_stats():
    hex_stats = dict()
    with transaction.manager:
        for l in DBSession.query(Hex).all():
            if l.yellow < 0:
                l.yellow = 0
            elif l.yellow > 1000:
                l.yellow = 1000
            if l.blue < 0:
                l.blue = 0
            elif l.blue > 1000:
                l.blue = 1000
            if l.red < 0:
                l.red = 0
            elif l.red > 1000:
                l.red = 1000
            if l.black < 0:
                l.black = 0
            elif l.black > 1000:
                l.black = 1000
        DBSession.commit()

    return hex_stats


def calc_hex_controls():
    hex_stats = dict()

    for l in DBSession.query(Hex).all():
        hex_stats[l.name] = {'Blue': 0, 'Yellow': 0, 'Black': 0, 'Red': 0}
        blue = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Blue')
        red = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Red')
        yellow = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Yellow')
        black = DBSession.query(Player).filter(Player.is_active).filter(Player.location == l.name).filter(Player.team == 'Black')

        # Takes 3 seconds in all to compute
        # Reason: `x.all()`
        hex_stats[l.name]['Blue'] = sum([b.troops for b in blue.all()])
        hex_stats[l.name]['Yellow'] = sum([y.troops for y in yellow.all()])
        hex_stats[l.name]['Red'] = sum([r.troops for r in red.all()])
        hex_stats[l.name]['Black'] = sum([bl.troops for bl in black.all()])

        total = sum(hex_stats[l.name].values())

        # The final number for each team is the sum of all the other teams
        for k in hex_stats[l.name].keys():
            hex_stats[l.name][k] = (hex_stats[l.name][k] * 2) - total

    return hex_stats


def update_hex_control():
    hexes = calc_hex_controls()

    with transaction.manager:
        for loc, ctrl in hexes.items():
            DBSession.query(Hex).filter(Hex.name == loc).update({Hex.blue: Hex.blue + ctrl['Blue'],
                                                                 Hex.yellow: Hex.yellow + ctrl['Yellow'],
                                                                 Hex.red: Hex.red + ctrl['Red'],
                                                                 Hex.black: Hex.black + ctrl['Black']})

        DBSession.commit()

    fix_hex_stats()
    determine_hex_controllers()


def update_hex_resources():
    # Update all hex resources according attributes; ammo-industry, population-infrastructure
    with transaction.manager:
            DBSession.query(Hex).update({Hex.ammo: Hex.industry + Hex.ammo, Hex.population: Hex.population + Hex.infrastructure})
            DBSession.commit()


def deactivate_inactive_players():
    # Make is_active False for players who havent been on for more than 14 days
    now = datetime.now()
    fortnight = now - timedelta(days=14)
    with transaction.manager:
        DBSession.query(Player).filter(Player.is_active).filter(Player.last_active < fortnight).update({Player.is_active: False})
        DBSession.commit()


def increase_actions():
    # Increase all player actions, max 1
    with transaction.manager:
        DBSession.query(Player).filter(Player.is_active).filter(Player.actions <= 9).update({Player.actions: Player.actions + 1})
        DBSession.commit()


def increase_morale():
    # Increase all player morale, max 100
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


schedule.every(turn_time).seconds.do(turn)

print('\nStarting..')
while True:
    schedule.run_pending()
    time.sleep(turn_time/5)
