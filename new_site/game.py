import logging
from math import (
    sqrt,
    log10
)
from random import (
    randrange,
    choice
)

import transaction
from sqlalchemy import (
    and_,
    or_
)
from sqlalchemy.orm.exc import NoResultFound

from .models import (
    DBSession,
    Hex,
    Player,
    Team,
    Radio,
    Avatar
)

log = logging.getLogger(__name__)
# TODO organize these better


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


def update_location_info(name, update, new):
    try:
        with transaction.manager:
            DBSession.query(Hex).filter_by(name=name).update({update: new})
        return True, 'success'
    except Exception as e:
        msg = "{err} on update_location_info(name={name}, update='{update}', new={new})".format(
            err=str(type(e).__name__ + ': ' + str(e)), name=name, update=update, new=new)
        log.warning(msg)
        return False, type(e).__name__ + ': ' + str(e)


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


def update_player_info(player, updates=None):
    if type(player) is Player:
        username = player.username
    else:
        username = player
    try:
        with transaction.manager:
            DBSession.query(Player).filter_by(username=username).update(updates)
        return True, 'success'
    except Exception as e:
        msg = "{err} on update_player_info(player={username}, updates={updates})".format(
            err=str(type(e).__name__ + ': ' + str(e)), username=username, updates=updates)
        log.warning(msg)
        return False, type(e).__name__ + ': ' + str(e)


def remove_actions_from(player, actions):
    player = get_player_info(player)

    if not player.actions >= actions:
        return False
    else:
        return update_player_info(player=player, updates={'actions': player.actions-actions})[0]


def remove_ammo_from(player, amount):
    player = get_player_info(player)

    if player.ammo < amount:
        return False

    return update_player_info(player=player, updates={'ammo': player.ammo-amount})[0]


def can_move_to(player, locations):
    visitable = []
    currently_at = [i for i in locations if i.name == player.location][0]

    diff_is_one = (-1, 0, 1)
    for i in locations:
        if currently_at.x - i.x in diff_is_one and currently_at.y - i.y in diff_is_one:
            visitable.append(i)

    return visitable


def can_move(to, player):
    currently_at = get_location_called(player.location)
    diff_is_one = (-1, 0, 1)
    friendly = 'None', player.team
    status = ''
    if not currently_at:
        msg = "Unexpected error on move_to(to={to}, player={player})".format(to=to, player=player.username)
        log.warning(msg)
        return False, ''
    if type(to) is str:
        to = get_location_called(to)
        if not to:
            return to, 'This location does not exist'
    if player.location == to.name:
        return False, 'The location you are trying to move to is the same location you are currently in'
    if (to.control not in friendly and currently_at.control not in friendly) and player.squad_type != 'Tank':
        return False, 'One of the locations you are moving to/from must be friendly'
    if to.control != 'None' and to.control != player.team:
        status = 'Enemy'
    if currently_at.x - to.x in diff_is_one and currently_at.y - to.y in diff_is_one:
        return True, status
    return False, 'This location is not next to your current location'


def player_can_attack(attacker, defender):
    attacker, defender = get_player_info(attacker), get_player_info(defender)

    if not attacker or not defender:
        return "Player does not exist!"
    if attacker.team == defender.team:
        return "You cannot attack your teammate!"
    if attacker.location != defender.location and attacker.squad_type != 'Artillery':
        return "You are not in the same location as this player!"
    if attacker.squad_type == 'Artillery':
        to, _from = get_location_called(attacker.location), get_location_called(defender.location)
        diffx = abs(to.x-_from.x)
        diffy = abs(to.y-_from.y)
        if not (diffx > 1 or diffy > 1):
            return "Target is too close. You could get hit!"
        if not (diffx < 6 or diffy < 6):
            return "Target is too far away!"
    if attacker.morale < 10:
        return "Your squad lacks heart! Raise your morale!"
    if not attacker.actions:
        return "You do not have enough actions!"
    return True


# TODO Fix this ASAP, add artillery
# You won! meme lost 2108 troops while you only lost 2. The enemy rushes back to their capital to regenerate. Tank v Infantry
# You won! meme lost 257 troops while you only lost 213. You drop everything and hurry back to the capital to regenerate. The enemy rushes back to their capital to regenerate. Tank v Tank
def player_attack(attacker, defender):
    can_attack = player_can_attack(attacker=attacker, defender=defender)
    if can_attack is not True:
        return can_attack

    attacker, defender = get_player_info(attacker), get_player_info(defender)

    #  Returns negative if morale < 1, error if 0

    attacker_strength = (sqrt(attacker.troops*attacker.attack) * log10(attacker.morale) + (randrange(11, 20)/10))
    defender_strength = (sqrt(defender.troops*defender.defense) * log10(defender.morale) + (randrange(11, 20)/10))

    a_ammo_needed = attacker.troops//attacker.logistics  # 5
    d_ammo_needed = defender.troops//defender.logistics

    a_troops = attacker.troops  # 5
    d_troops = defender.troops
    a_min = 10
    d_min = 10

    a_multiplier = 1
    d_multiplier = 1

    if attacker.squad_type == 'Tank':
        a_min = 1
        a_multiplier = 10
        attacker_strength *= choice((6, 7, 8, 9))
        defender_strength /= choice((6, 7, 8, 9))
        a_ammo_needed *= 100  # 500
        a_troops *= 100  # 500
    if defender.squad_type == 'Tank':
        d_min = 1
        d_multiplier = 10
        defender_strength *= choice((6, 7, 8, 9))
        attacker_strength /= choice((6, 7, 8, 9))
        d_ammo_needed *= 100
        d_troops *= 100

    if a_ammo_needed > attacker.ammo:
        attacker_strength = attacker_strength * (attacker.ammo / attacker.troops)
    if d_ammo_needed > defender.ammo:
        defender_strength = defender_strength * (defender.ammo / defender.troops)

    if attacker_strength*a_multiplier > defender_strength*d_multiplier:
        attacker_loss = round(defender_strength)
        defender_loss = round(attacker_strength)
        if attacker_loss*a_multiplier == defender_loss*d_multiplier:
            status = dict(result='win', draw=True)
        else:
            status = dict(result='win', draw=False)
    else:
        attacker_loss = round(defender_strength)
        defender_loss = round(attacker_strength)
        if attacker_loss*a_multiplier == defender_loss*d_multiplier:
            status = dict(result='loss', draw=True)
        else:
            status = dict(result='loss', draw=False)

    remove_actions_from(attacker.username, 1)
    remove_ammo_from(attacker.username, a_ammo_needed)

    remove_ammo_from(defender.username, d_ammo_needed)

    fight1 = update_player_info(attacker.username, updates={'troops': attacker.troops - attacker_loss})
    fight2 = update_player_info(defender.username, updates={'troops': defender.troops - defender_loss})

    if status['result'] == 'win':
        update_player_info(defender.username, updates={'morale': defender.morale - 10})
    else:
        update_player_info(attacker.username, updates={'morale': attacker.morale - 10})

    if fight1[0] is not fight2[0]:
        log.warning("Weird ass error player_attack(attacker={attacker}, defender={defender})".format(
            attacker=attacker.username, defender=defender.username))
        return "This is a weird ass attack. Please report the current time and date and error the the admin"
    elif fight1[0] is False:
        return "A problem occurred, investigating"

    if status['result'] == 'win':
        msg = "You won! {defender} lost {d_loss} troops while you only lost {a_loss}. ".format(
                defender=defender.username, d_loss=defender_loss, a_loss=attacker_loss)
        d_msg = "You were attacked by {attacker} and lost {d_loss} troops while they only lost {a_loss} troops.".format(
            attacker=attacker.username, d_loss=defender_loss, a_loss=attacker_loss)
        update_player_info(attacker.username, updates={'experience': attacker.experience + defender_loss})
        if status['draw']:
            msg += ("Even though the losses were the same, the vigour and skill of your squad strikes fear into "
                    "the hearts of the enemy and they lose morale.")
            d_msg += ("Even though the losses were the same, your squad become discouraged "
                      "at the lack of win and lose morale.")

    else:
        msg = "You lost! {defender} only lost {d_loss} troops while you lost {a_loss}. ".format(
            defender=defender.username, d_loss=defender_loss, a_loss=attacker_loss)
        d_msg = "You were attacked by {attacker} and only lost {d_loss} troops while they lost {a_loss} troops.".format(
            attacker=attacker.username, d_loss=defender_loss, a_loss=attacker_loss)
        update_player_info(defender.username, updates={'experience': defender.experience + attacker_loss})
        if status['draw']:
            msg += "Even though losses are the same, your squad become discouraged at the lack of win and lose morale."
            d_msg += ("Even though the losses were the same, the vigour and skill of your squad strikes fear into "
                      "the hearts of the enemy and they lose morale.")

    attacker, defender = get_player_info(attacker.username), get_player_info(defender.username)

    if attacker.ammo < 0:
        update_player_info(attacker.username, updates={'ammo': 0})
    if defender.ammo < 0:
        update_player_info(defender.username, updates={'ammo': 0})

    if attacker.troops < a_min or attacker.morale < 10:
        msg += " You drop everything and hurry back to the capital to regenerate."
        d_msg += "Their losses are heavy and they rush back to the capital to regenerate"
        update_player_info(attacker.username, updates={'troops': a_min, 'morale': 10, 'ammo': 0})
        send_player_to(get_team_info(attacker.team)['capital'], attacker.username, force=True)

    if defender.troops < d_min or defender.morale < 10:
        msg += " The enemy rushes back to their capital to regenerate."
        d_msg += "Your losses are great so and you drop everything hurry back to the capital to regenerate"
        update_player_info(defender.username, updates={'troops': a_min, 'morale': 10, 'ammo': 0})
        send_player_to(get_team_info(defender.team)['capital'], defender.username, force=True)

    send_message(_from='', message=d_msg, to=defender.username)
    return msg


def send_player_to(location, player, force=False):
    player_info = get_player_info(player)
    player_loc = player_info.location

    movable = can_move(to=location, player=player_info)
    if not force:
        if not movable[0]:
            return "You are cannot move to this location! {}".format(movable[1])
        actions_needed = 2
        if movable[1] == 'Enemy':
            actions_needed = 5
        if player_info.squad_type == 'Tank':
            actions_needed *= 2

        actions_needed //= player_info.pathfinder
        if not player_info.actions >= actions_needed:
            return "You do not have enough actions!"

        remove_actions_from(player, round(actions_needed))

    movement = update_player_info(player, updates={'location': location})

    if movement[0]:
        return "Successfully moved from {player_loc} to {new_loc}!".format(player_loc=player_loc, new_loc=location)
    else:
        return "An error occurred while trying to move!"


def give_player_ammo(player, amount=0):
    player = get_player_info(player)

    if not amount:
        increase = 100
        location = get_location_called(player.location)
        if not player.actions >= 1:
            return "Not enough actions!"
        if location.ammo < increase:
            return "Not enough ammo in location"
        update_location_info(player.location, 'ammo', location.ammo - increase)
    else:
        increase = amount

    update_player_info(player, updates={'ammo': player.ammo + increase})

    return "Ammo increased!"


def increase_player_troops(player, amount=0):
    player = get_player_info(player)
    if not amount:
        increase = 10 * player.charisma
        multiplier = 100
        if player.squad_type == 'Tank':
            increase //= 10
            multiplier //= 10
        location = get_location_called(player.location)
        if not player.actions >= 1:
            return "Not enough actions!"
        if location.population < increase:
            return "Not enough people in location"
        if player.troops + increase > player.management * multiplier:
            return "You cannot manage more than {} troops!".format(player.management * multiplier)

        update_location_info(player.location, 'population', location.population - increase)
    else:
        increase = amount
    remove_actions_from(player, 1)
    update_player_info(player, updates={'troops': player.troops + increase})

    return "Troops increased by {}".format(str(increase))


def upgrade_hex_for(player):
    player = get_player_info(player)

    if not player.actions >= 5:
        return "Not enough actions!"
    location = get_location_called(player.location)
    update_location_info(player.location, 'industry', location.industry + 1)
    remove_actions_from(player, 5)

    return "Upgraded location!"


def upgrade_infrastructure_for(player):
    player = get_player_info(player)

    if not player.actions >= 5:
        return "Not enough actions!"
    location = get_location_called(player.location)
    update_location_info(player.location, 'infrastructure', location.infrastructure + 1)
    remove_actions_from(player, 5)

    return "Upgraded infrastructure!"


def get_player_info(username):
    if type(username) is Player:
        username = username.username
    try:
        player = DBSession.query(Player).filter_by(username=username).one()
    except NoResultFound as e:
        msg = "{err} on get_player_info(username={username})".format(err=str(type(e).__name__ + ': ' + str(e)),
                                                                     username=username)
        log.warning(msg)
        return
    return player


def get_player_avatar(player, small=False):
    avatar = DBSession.query(Avatar).filter(username=player.username).one()
    path = avatar.path  # path = '_{username}/{username}'
    if not path:
        path = 'default/{team}/{num}'.format(team=player.team.lower(), num=avatar.default)

    if small:
        path += '-small'

    return path


def change_player_avatar(player, avatar):
    pass


def get_players_located_at(location):
    try:
        players_at = DBSession.query(Player).filter(Player.is_active).filter_by(location=location).all()
    except NoResultFound as e:
        msg = "{err} on get_players_located_at(location={location})".format(err=str(type(e).__name__ + ': ' + str(e)),
                                                                            location=location)
        log.warning(msg)
        return
    return players_at


def xp_for_level_up(player):
    player = get_player_info(player)

    if player.level >= 10:
        num = float('3.' + str(player.level))
    else:
        num = float('2.' + str(player.level))

    xp_needed = (player.level ** num * 100 / player.level)

    return xp_needed


def level_up_player(player, attribute):
    attributes = ['management', 'attack', 'defense', 'charisma', 'rallying', 'pathfinder', 'logistics']
    if attribute not in attributes:
        return "Invalid attribute"

    player = get_player_info(player)

    current_lvl = getattr(player, attribute)
    if current_lvl >= 10:
        return "You've already maxed this out!"

    xp_gone = xp_for_level_up(player)
    if not player.experience >= xp_gone:
        return "Not enough xp"

    if attribute == 'pathfinder' and player.squad_type == 'Tank':
        return "Tanks can't upgrade this stat"

    update_player_info(player, updates={attribute: current_lvl+1})
    update_player_info(player, updates={'level': player.level + 1})
    update_player_info(player, updates={'experience': player.experience-xp_gone})

    return "Leveled up {name}!".format(name=attribute)


def get_radio_for(player):
    player = get_player_info(player)
    news_tag = "{name}_{id}".format(name=player.username, id=player.id)
    results = DBSession.query(Radio)\
        .filter(or_(Radio.team == player.team, Radio.team == 'all', Radio.team == news_tag))\
        .filter(Radio.active).limit(50).all()
    if not results:
        return []

    return results


def send_message(message, _from='', to='', broadcast_by=''):
    if not message:
        return "https://www.youtube.com/watch?v=u9Dg-g7t2l4"
    if len(message) > 140 and not to and not broadcast_by:
        return "Your budget is not high enough to send this many words"

    if not _from and not to and not broadcast_by:
        return "No author specified"

    if broadcast_by:
        team = 'all'
        author = broadcast_by
    elif to:
        player = get_player_info(to)
        team = "{name}_{id}".format(name=player.username, id=player.id)
        author = 'Server'
    else:
        player = get_player_info(_from)
        team = player.team
        author = player.username

    with transaction.manager:
        new_msg = Radio(author=author, message=message, team=team)
        DBSession.add(new_msg)
        transaction.commit()

    return "Message sent successfully!"


def get_all_game_info_for(player, location=''):
    game_info = dict()
    game_info['hexes'] = get_hexes()
    game_info['player'] = get_player_info(player)

    if location:
        loc = get_location_called(location)
        if not loc:
            return False
        game_info['current_hex'] = loc
        game_info['currently_here'] = get_players_located_at(location)
        game_info['movable'] = can_move(game_info['current_hex'], game_info['player'])[0]

    return game_info
