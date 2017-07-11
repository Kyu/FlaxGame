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


def get_hex_called(name):
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


def remove_actions_from(player, actions):
    player = get_player_info(player)
    if not player.actions >= actions:
        return "Not enough actions"
    else:
        update_player_info(player=player, update='actions', new=player.actions-actions)


def can_move_to(player, hexes):
    visitable = []
    currently_at = [i for i in hexes if i.name == player.location][0]

    # if player.type is regular foot soldier
    diff_is_one = (-1, 0 , 1)
    for i in hexes:
        if currently_at.x - i.x in diff_is_one and currently_at.y - i.y in diff_is_one:
            visitable.append(i)

    return visitable


def can_move(to, from_loc):
    currently_at = get_hex_called(from_loc)
    diff_is_one = (-1, 0, 1)

    if not currently_at:
        return False
    if type(to) is str:
        to = get_hex_called(to)
    if from_loc == to.name:
        return False
    if currently_at.x - to.x in diff_is_one and currently_at.y - to.y in diff_is_one:
        return True
    return False


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
        return False, type(e).__name__ + ': ' + str(e)


def player_can_attack(attacker, defender):
    attacker, defender = get_player_info(attacker), get_player_info(defender)

    if attacker.team == defender.team or attacker.location != defender.location:
        return False

    return True


# TODO morale, ammo, actions
def player_attack(attacker, defender):
    if not player_can_attack(attacker=attacker, defender=defender):
        return False
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
        # TODO loging errors
        return
    elif attack1[0] is False:
        return attack1[1]
    else:
        return "Sucessfully attacked"
        # TODO add attack details, whether attack send player back


def send_player_to(position, player):
    try:
        with transaction.manager:
            movement = DBSession.query(Player).filter_by(username=player).update({'location': position})
            transaction.commit()
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))


def get_player_info(username):
    player = DBSession.query(Player).filter_by(username=username).one()
    return player


def get_players_located_at(hex_name):
    players_at = DBSession.query(Player).filter_by(location=hex_name).all()
    return players_at


def get_all_game_info_for(player, hex_at=''):
    game_info = dict()
    game_info['hexes'] = get_hexes()
    game_info['player'] = get_player_info(player)

    if hex_at:
        game_info['current_hex'] = get_hex_called(hex_at)
        game_info['currently_here'] = get_players_located_at(hex_at)
        game_info['movable'] = can_move(game_info['current_hex'], game_info['player'].location)

    return game_info
