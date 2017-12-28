import configparser
import time
from datetime import (
    datetime,
    timedelta
)

import schedule
import transaction

from .models import (
    Player,
    Hex,
    create_session
)


def determine_hex_controllers():
    hex_stats = dict()

    # Find who has the most points in each location, add team as controller.
    with transaction.manager:
        for l in DBSession.query(Hex).all():
            hex_stats[l.name] = {'Blue': l.blue, 'Yellow': l.yellow, 'Black': l.black, 'Red': l.red, 'None': 0.1}

            # I honestly don't how this does it, but it works and that's the important part
            # Returns the team(s) with the most points in a location
            control = \
                [key for m in [max(hex_stats[l.name].values())] for key, val in hex_stats[l.name].items() if val == m]

            # If more than one control, None is the controller.
            if len(control) > 1:
                hex_stats[l.name]['control'] = 'None'
            else:
                hex_stats[l.name]['control'] = control[0]

        # Update controller
        for loc, ctrl in hex_stats.items():
            DBSession.query(Hex).filter(Hex.name == loc).update({Hex.control: ctrl['control']})

        DBSession.commit()


def fix_hex_stats():
    # Reverse over and underflow for locations
    # Plains, City max - 1000, Capital max - 3000
    hex_stats = dict()
    with transaction.manager:
        for l in DBSession.query(Hex).all():
            if l.yellow < 0:
                l.yellow = 0
            elif l.yellow > 1500 and l.type == 'capital':
                l.yellow = 1500
            elif l.yellow > 1000 and l.type in 'plains city':
                l.yellow = 1000
            if l.blue < 0:
                l.blue = 0
            elif l.blue > 1500 and l.type == 'capital':
                l.blue = 1500
            elif l.blue > 1000 and l.type in 'plains city':
                l.blue = 1000
            if l.red < 0:
                l.red = 0
            elif l.red > 1500 and l.type == 'capital':
                l.red = 1500
            elif l.red > 1000 and l.type in 'plains city':
                l.red = 1000
            if l.black < 0:
                l.black = 0
            elif l.black > 1500 and l.type == 'capital':
                l.black = 1500
            elif l.black > 1000 and l.type in 'plains city':
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
    # Find out how many points each team has for each location, and update DB to appropriate values
    hexes = calc_hex_controls()

    with transaction.manager:
        for loc, ctrl in hexes.items():
            DBSession.query(Hex).filter(Hex.name == loc).update({Hex.blue: Hex.blue + ctrl['Blue'],
                                                                 Hex.yellow: Hex.yellow + ctrl['Yellow'],
                                                                 Hex.red: Hex.red + ctrl['Red'],
                                                                 Hex.black: Hex.black + ctrl['Black']})

        DBSession.commit()

    # Reverse overflow, then determine who controls each location
    fix_hex_stats()
    determine_hex_controllers()


def update_hex_resources():
    # Update all hex resources according attributes; ammo-industry, population-infrastructure
    with transaction.manager:
            DBSession.query(Hex).update({Hex.ammo: Hex.industry + Hex.ammo, Hex.population: Hex.population + Hex.infrastructure})
            DBSession.commit()


def deactivate_inactive_players():
    # Make is_active False for players who haven't been on for more than 14 days
    now = datetime.now()
    fortnight = now - timedelta(days=14)
    with transaction.manager:
        DBSession.query(Player).filter(Player.is_active).filter(Player.last_active < fortnight).update({Player.is_active: False})

        DBSession.commit()


def unban_banned():
    # Unban players whos bans have expired
    now = datetime.now()
    with transaction.manager:
        DBSession.query(Player).filter(Player.banned).filter(Player.time_banned)\
            .filter(now > Player.time_banned).update\
            ({Player.banned: False, Player.time_banned: None, Player.reason_banned: None, Player.banned_by: None})
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


def get_options(path):
    config_uri = path
    config = configparser.ConfigParser()
    config.read(config_uri)
    options = config['app:main']

    turn_time = int(options['turn_time'])
    return turn_time


def turn():
    begin = datetime.now()
    print("Turn starting at {}".format(begin))

    update_hex_control()
    update_hex_resources()
    deactivate_inactive_players()
    increase_actions()
    increase_morale()

    end = datetime.now()
    DBSession.close()
    print("Turn ran successfully, took {}\n".format(end-begin))


def start(path=''):
    if not path:
        print("No path defined!")
        quit()

    global DBSession  # yeah
    DBSession = create_session(path)

    turn_time = get_options(path)

    schedule.every(turn_time).seconds.do(turn)
    schedule.every(turn_time/10).seconds.do(unban_banned)

    '''One team is found to control all of the hexes. Turns will stop for 24 hours.
    If this team still controls `All` the hexes after 24 hours, they will be declared the winners'''

    # True = some var that is false if ^
    print('\nStarting..')
    while True:
        schedule.run_pending()
        time.sleep(turn_time/5)
