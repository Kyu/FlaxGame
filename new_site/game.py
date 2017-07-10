import transaction

from sqlalchemy.orm.exc import NoResultFound

from .models import (
    DBSession,
    Hex,
    Player
)


# TODO: come up with better hex variable naming convention (hex is a builtin)
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
    try:
        with transaction.manager:
            # Battle formula v1
            if attacker.troops < defender.troops:
                DBSession.query(Player).filter_by(username=attacker.username).update({'troops': attacker.troops - 5})
                DBSession.query(Player).filter_by(username=defender.username).update({'troops': defender.troops - 2})
            elif attacker.troops > defender.troops:
                DBSession.query(Player).filter_by(username=attacker.username).update({'troops': attacker.troops - 2})
                DBSession.query(Player).filter_by(username=defender.username).update({'troops': defender.troops - 5})
            else:
                DBSession.query(Player).filter_by(username=attacker.username).update({'troops': attacker.troops - 3})
                DBSession.query(Player).filter_by(username=defender.username).update({'troops': defender.troops - 3})
            transaction.commit()
            return True
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))
        return False


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
