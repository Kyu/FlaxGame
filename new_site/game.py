import transaction

from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from .models import (
    DBSession,
    Hex,
    Player,
    Team
)


# TODO: change hex variables to `location`
def get_hexes():
    hexes = DBSession.query(Hex)
    sorted_hexes = sorted(hexes, key=lambda the_hex: (the_hex.x, the_hex.y))
    return sorted_hexes


def get_location_called(name):
    try:
        the_hex = DBSession.query(Hex).filter_by(name=name).one()
    except NoResultFound:
        the_hex = None
    return the_hex


def get_team_info(team, all=None):
    try:
        team_info = DBSession.query(Team).filter_by(name=team).one()
    except NoResultFound:
        return {}

    team = dict()
    team['name'] = team_info.name
    team['capital'] = team_info.capital
    # TODO use https://stackoverflow.com/a/32527383/3875151 to calc active users on turn
    active_users = DBSession.query(Player).filter(and_(Player.team == team_info.name, Player.is_active)).all()
    team['active_members'] = active_users
    if all:
        team['members'] = DBSession.query(Player).filter(team=team_info.name).all()

    return team


def update_player_info(player, update, new):
    if type(player) is Player:
        username = player.username
    else:
        username = player
    try:
        with transaction.manager:
            DBSession.query(Player).filter_by(username=username).update({update: new})
        return True, 'success'
    except Exception as e:
        # TODO when you get to logging
        return False, type(e).__name__ + ': ' + str(e)


def remove_actions_from(player, actions):
    player = get_player_info(player)
    if not player.actions >= actions:
        return False
    else:
        update_player_info(player=player, update='actions', new=player.actions-actions)
        return True


def can_move_to(player, locations):
    visitable = []
    currently_at = [i for i in locations if i.name == player.location][0]

    # if player.type is regular foot soldier
    diff_is_one = (-1, 0 , 1)
    for i in locations:
        if currently_at.x - i.x in diff_is_one and currently_at.y - i.y in diff_is_one:
            visitable.append(i)

    return visitable


def can_move(to, _from):
    currently_at = get_location_called(_from)
    diff_is_one = (-1, 0, 1)

    if not currently_at:
        return False
    if type(to) is str:
        to = get_location_called(to)
    if _from == to.name:
        return False
    if currently_at.x - to.x in diff_is_one and currently_at.y - to.y in diff_is_one:
        return True
    return False


def player_can_attack(attacker, defender):
    attacker, defender = get_player_info(attacker), get_player_info(defender)

    if attacker.team == defender.team or attacker.location != defender.location:
        return False

    return True


# TODO morale, ammo
def player_attack(attacker, defender):
    if not remove_actions_from(attacker, 1):
        return "You do not have enough actions!"

    if not player_can_attack(attacker=attacker, defender=defender):
        return "You cannot attack this player!"

    attacker, defender = get_player_info(attacker), get_player_info(defender)

    if attacker.troops < defender.troops:
        attack1 = update_player_info(attacker.username, 'troops', attacker.troops-5)
        attack2 = update_player_info(defender.username, 'troops', defender.troops-2)
    elif attacker.troops > defender.troops:
        attack1 = update_player_info(attacker.username, 'troops', attacker.troops - 2)
        attack2 = update_player_info(defender.username, 'troops', defender.troops - 5)
    else:
        attack1 = update_player_info(attacker.username, 'troops', attacker.troops - 3)
        attack2 = update_player_info(defender.username, 'troops', defender.troops - 3)

    if attack1[0] is not attack2[0]:
        # TODO logging errors
        return "This is a weird ass attack. Please report the current time and date and error the the admin"
    elif attack1[0] is False:
        return attack1[1]
    else:
        return "Successfully attacked"
        # TODO add attack details, whether attack send player back


def send_player_to(location, player):
    if not remove_actions_from(player, 2):
        return "You do not have enough actions!"
    player_loc = get_player_info(player).location
    if not can_move(to=location, _from=player_loc):
        return "You are cannot move to this location!"

    movement = update_player_info(player, 'location', location)

    if movement[0]:
        return "Successfully moved from {player_loc} to {new_loc}!".format(player_loc=player_loc, new_loc=location)
    else:
        return "An error occurred while trying to move!"


def get_player_info(username):
    player = DBSession.query(Player).filter_by(username=username).one()
    return player


def get_players_located_at(location):
    players_at = DBSession.query(Player).filter_by(location=location).all()
    return players_at


def get_all_game_info_for(player, location=''):
    game_info = dict()
    game_info['hexes'] = get_hexes()
    game_info['player'] = get_player_info(player)

    if location:
        game_info['current_hex'] = get_location_called(location)
        game_info['currently_here'] = get_players_located_at(location)
        game_info['movable'] = can_move(game_info['current_hex'], game_info['player'].location)

    return game_info
