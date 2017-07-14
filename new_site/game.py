from math import sqrt, log10
from random import randrange

import transaction
import logging

from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from .models import (
    DBSession,
    Hex,
    Player,
    Team
)

log = logging.getLogger(__name__)


def get_hexes():
    hexes = DBSession.query(Hex)
    sorted_hexes = sorted(hexes, key=lambda the_hex: (the_hex.x, the_hex.y))
    return sorted_hexes


def get_location_called(name):
    try:
        the_hex = DBSession.query(Hex).filter_by(name=name).one()
    except NoResultFound as e:
        msg = "{err} on get_location_called(name={name})".format(err=str(type(e).__name__ + ': ' + str(e)), name=name)
        log.warning(msg)
        the_hex = None
    return the_hex


def get_team_info(team, get_all=None):
    try:
        team_info = DBSession.query(Team).filter_by(name=team).one()
    except NoResultFound as e:
        msg = "{err} on get_team_info(team={team}, all={all})".format(
            err=str(type(e).__name__ + ': ' + str(e)), team=team, all=get_all)
        log.warning(msg)
        return {}

    team = dict()
    team['name'] = team_info.name
    team['capital'] = team_info.capital
    active_users = DBSession.query(Player).filter(and_(Player.team == team_info.name, Player.is_active)).all()
    team['active_members'] = active_users
    if get_all:
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
        msg = "{err} on update_player_info(player={username}, update='{update}', new={new})".format(
            err=str(type(e).__name__ + ': ' + str(e)), username=username, update=update, new=new)
        log.warning(msg)
        return False, type(e).__name__ + ': ' + str(e)


def remove_actions_from(player, actions):
    if type(player) is not Player:
        player = get_player_info(player)

    if not player.actions >= actions:
        return False
    else:
        return update_player_info(player=player, update='actions', new=player.actions-actions)[0]


def remove_ammo_from(player, amount):
    if type(player) is not Player:
        player = get_player_info(player)

    if player.ammo < amount:
        return False

    return update_player_info(player=player, update='ammo', new=player.ammo-amount)[0]


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
        msg = "Unexpected error on move_to(to={to}, _from={_from})".format(to=to, _from=_from)
        log.warning(msg)
        return False, ''
    if type(to) is str:
        to = get_location_called(to)
        if not to:
            return to, 'This location does not exist'
    if _from == to.name:
        return False, 'The location you are trying to move to is the same location you are currently in'
    if currently_at.x - to.x in diff_is_one and currently_at.y - to.y in diff_is_one:
        return True, ''
    return False, 'This location is not next to your current location'


def player_can_attack(attacker, defender):
    attacker, defender = get_player_info(attacker), get_player_info(defender)

    if not attacker or not defender:
        return "Player does not exist!"
    if attacker.team == defender.team:
        return "You cannot attack your teammate!"
    if attacker.location != defender.location:
        return "You are not in the same location as this player!"
    if attacker.morale < 10:
        return "Your squad lacks heart! Raise your morale!"
    if not attacker.actions:
        return "You do not have enough actions!"
    if not attacker.ammo >= attacker.troops:  # TODO start working on formulas
        return "You do not have enough ammo"
    return True


def player_attack(attacker, defender):
    can_attack = player_can_attack(attacker=attacker, defender=defender)
    if can_attack is not True:
        return can_attack

    attacker, defender = get_player_info(attacker), get_player_info(defender)

    #  Returns negative if morale < 1, error if 0
    #  TODO include ammo count in forumla

    attacker_strength = (sqrt(attacker.troops*attacker.attack) * log10(attacker.morale) + (randrange(11, 20)/10))
    defender_strength = (sqrt(defender.troops*defender.defense) * log10(defender.morale) + (randrange(11, 20)/10))

    if attacker_strength > defender_strength:
        attacker_loss = round(defender_strength)
        defender_loss = round(attacker_strength)
        if attacker_loss == defender_loss:
            status = dict(result='win', draw=True)
        else:
            status = dict(result='win', draw=False)
    else:
        attacker_loss = round(defender_strength)
        defender_loss = round(attacker_strength)
        if attacker_loss == defender_loss:
            status = dict(result='loss', draw=True)
        else:
            status = dict(result='loss', draw=False)

    remove_actions_from(attacker.username, 1)
    remove_ammo_from(attacker.username, attacker.troops/attacker.logistics)

    remove_ammo_from(defender.username, defender.troops/defender.logistics)

    fight1 = update_player_info(attacker.username, 'troops', attacker.troops - attacker_loss)
    fight2 = update_player_info(defender.username, 'troops', defender.troops - defender_loss)

    if status['result'] == 'win':
        update_player_info(defender.username, 'morale', defender.morale - 10)
    else:
        update_player_info(attacker.username, 'morale', attacker.morale - 10)

    if fight1[0] is not fight2[0]:
        log.warning("Weird ass error player_attack(attacker={attacker}, defender={defender})".format(
            attacker=attacker.username, defender=defender.username))
        return "This is a weird ass attack. Please report the current time and date and error the the admin"
    elif fight1[0] is False:
        return "A problem occurred, investigating"

    if status['result'] == 'win':
        msg = "You won! {defender} lost {d_loss} troops while you only lost {a_loss}. ".format(
                defender=defender.username, d_loss=defender_loss, a_loss=attacker_loss)
        update_player_info(attacker.username, 'experience', attacker.experience + defender_loss)
        if status['draw']:
            msg = msg + ("Even though the losses were the same, the vigour and skill of your squad strikes fear into "
                         "the hearts of the enemy and they lose morale.")
    else:
        msg = "You lost! {defender} only lost {d_loss} troops while you lost {a_loss}. ".format(
            defender=defender.username, d_loss=defender_loss, a_loss=attacker_loss)
        update_player_info(defender.username, 'experience', defender.experience + attacker_loss)
        if status['draw']:
            msg += "Even though losses are the same, your squad become discouraged at the lack of win and lose morale."

    attacker, defender = get_player_info(attacker.username), get_player_info(defender.username)

    if attacker.troops < 10 or attacker.morale < 10:
        msg += " You hurry back to the capital to regenerate."
        update_player_info(attacker.username, 'troops', 10)
        update_player_info(attacker.username, 'morale', 10)
        send_player_to(get_team_info(attacker.team)['capital'], attacker.username, force=True)

    if defender.troops < 10 or defender.morale < 10:
        msg += " The enemy rushes back to their capital to regenerate."
        update_player_info(defender.username, 'troops', 10)
        update_player_info(defender.username, 'morale', 10)
        send_player_to(get_team_info(defender.team)['capital'], defender.username, force=True)

    return msg


def send_player_to(location, player, force=False):
    player_info = get_player_info(player)
    player_loc = player_info.location

    movable = can_move(to=location, _from=player_loc)
    if not force:
        if not movable[0]:
            return "You are cannot move to this location! {}".format(movable[1])

        if not player_info.actions >=2:
            return "You do not have enough actions!"

        remove_actions_from(player, round(3/player_info.pathfinder))

    movement = update_player_info(player, 'location', location)

    if movement[0]:
        return "Successfully moved from {player_loc} to {new_loc}!".format(player_loc=player_loc, new_loc=location)
    else:
        return "An error occurred while trying to move!"


def get_player_info(username):
    try:
        player = DBSession.query(Player).filter_by(username=username).one()
    except NoResultFound as e:
        msg = "{err} on get_player_info(username={username})".format(err=str(type(e).__name__ + ': ' + str(e)),
                                                                     username=username)
        log.warning(msg)
        return
    return player


def get_players_located_at(location):
    try:
        players_at = DBSession.query(Player).filter_by(location=location).all()
    except NoResultFound as e:
        msg = "{err} on get_players_located_at(location={location})".format(err=str(type(e).__name__ + ': ' + str(e)),
                                                                            location=location)
        log.warning(msg)
        return
    return players_at


def get_all_game_info_for(player, location=''):
    game_info = dict()
    game_info['hexes'] = get_hexes()
    game_info['player'] = get_player_info(player)

    if location:
        game_info['current_hex'] = get_location_called(location)
        game_info['currently_here'] = get_players_located_at(location)
        game_info['movable'] = can_move(game_info['current_hex'], game_info['player'].location)[0]

    return game_info
