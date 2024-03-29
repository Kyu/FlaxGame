import logging
from math import (
    sqrt,
    log10
)
from random import (
    randrange,
    choice
)
from datetime import (
    datetime,
    timedelta
)
from collections import OrderedDict

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
)

log = logging.getLogger(__name__)


def get_map_info_for(location='all'):
    # Returns all location info if no location specified
    if location == 'all':
        hexes = DBSession.query(Hex)
    else:
        hexes = DBSession.query(Hex).filter_by(name=location)

    # Sorts the hexes by x component, then y component
    sorted_hexes = sorted(hexes, key=lambda the_hex: (the_hex.x, the_hex.y))
    hexes = {}
    # For each item in sorted_hexes, this adds the item to the hexes dict, with an empty string value
    # If there are any players in the location, the string is updated to say so
    for i in sorted_hexes:
        hexes[i] = ''
        tanks = 0
        infantry = 0
        try:
            here = DBSession.query(Player).filter(Player.is_active).filter_by(location=i.name).all()
            tanks += sum([i.troops for i in here if i.squad_type == 'Tank'])
            infantry += sum([i.troops for i in here if i.squad_type == 'Infantry'])
        except NoResultFound:
            continue

        if tanks:
            hexes[i] += "-- {tanks} Tank troops".format(tanks=tanks)
        if infantry:
            if tanks:
                hexes[i] += ", "
            else:
                hexes[i] += "-- "
            hexes[i] += "{infantry} Infantry troops".format(infantry=infantry)

    # Re sorts the the dict by the x and y components of each key
    re_sort = OrderedDict(sorted(hexes.items(), key=lambda the_hex: (the_hex[0].x, the_hex[0].y)))
    return re_sort


def get_location_called(name):
    # Returns Hex object for location name
    try:
        the_hex = DBSession.query(Hex).filter_by(name=name).one()
    except NoResultFound as e:
        msg = "{err} on get_location_called(name={name})".format(err=str(type(e).__name__ + ': ' + str(e)), name=name)
        log.warning(msg)
        the_hex = None
    return the_hex


def update_location_info(name, update, new):
    # Update location info from dict
    try:
        with transaction.manager:
            DBSession.query(Hex).filter_by(name=name).update({update: new})
        return True, 'success'
    except Exception as e:
        msg = "{err} on update_location_info(name={name}, update='{update}', new={new})".format(
            err=str(type(e).__name__ + ': ' + str(e)), name=name, update=update, new=new)
        log.warning(msg)
        return False, type(e).__name__ + ': ' + str(e)


def get_team_info(team, get_all=False):
    # Gets info for a team name, or info for all teams.
    try:
        team_info = DBSession.query(Team).filter_by(name=team).one()
    except NoResultFound:
        # No need to log this error, user gets redirected
        # Scratch that I should probably do something with this for safety sake
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
    # Update Player info from dict.
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


def player_dig_in(player):
    # Increases a Players dug_in stat by 5, if they have 5 actions and their dug_in is < 100
    player = DBSession.query(Player).filter_by(username=player).one()
    if player.actions < 5:
        return "You need 5 actions to dig in!"
    if player.dug_in == 100:
        return "You cant dig in any further!"

    if player.dug_in >= 95:
        dug = 100
    else:
        dug = player.dug_in + 5

    update_player_info(player, {'dug_in': dug, 'actions': player.actions - 5})

    return "Successfully dug in!"


def remove_actions_from(player, actions):
    # Remove actions from a player
    player = get_player_info(player)

    if not player.actions >= actions:
        return False
    else:
        return update_player_info(player=player, updates={'actions': player.actions-actions})[0]


def remove_ammo_from(player, amount):
    # Removes ammo from a player
    player = get_player_info(player)

    if player.ammo < amount:
        return False

    return update_player_info(player=player, updates={'ammo': player.ammo-amount})[0]


def can_move_to(player, locations):
    # Checks to see which locations a player can visit (should this be a list?)
    # Player can move to location if the difference between Hex(Player.location) and location.x AND location.y is <= 1
    visitable = []
    currently_at = [i for i in locations if i.name == player.location][0]

    diff_is_one = (-1, 0, 1)
    for i in locations:
        if currently_at.x - i.x in diff_is_one and currently_at.y - i.y in diff_is_one:
            if i.name != player.location:
                visitable.append(i)

    return visitable


def can_move(to, player):
    # See if Player can actually move to a location
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
    # Infantry, artillery cant move enemy -> enemy
    # Tanks cant move enemy controlled capital -> enemy controlled location
    if (to.control not in friendly and currently_at.control not in friendly) and \
            (player.squad_type != 'Tank' or (player.squad_type == 'Tank' and to.type in ('city', 'capital'))):
        return False, 'One of the locations you are moving to/from must be friendly'
    if to.control != 'None' and to.control != player.team:
        status = 'Enemy'
    if currently_at.x - to.x in diff_is_one and currently_at.y - to.y in diff_is_one:
        return True, status
    return False, 'This location is not next to your current location'


def player_can_attack(attacker, defender):
    # See if player can attack another player. Anything but True means they can't
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
        if diffx < 1 or diffy < 1:
            return "Target is too close. You could get hit!"
        if not diffx > 4 or diffy > 4:
            return "Target is too far away!"
    if attacker.morale < 10:
        return "Your squad lacks heart! Raise your morale!"
    if not attacker.actions:
        return "You do not have enough actions!"
    return True


def artillery_attack(attacker, defender):
    # Artillery  can self destruct if <1/5 capacity remaning, also takes 2 turns to move
    # Turn 1: Pack up - 1 action
    # Turn 2: Move - 2 actions
    if attacker.squad_type != 'Artillery':
        return "Not artillery, how did you get here?"

    targets = get_players_located_at(defender.location)

    for player in targets:  # Come up with a formula
        if player.squad_type in ('Tank', 'Artillery'):
            loss = 1
        else:
            loss = 10
        loss += 1  # DELETE THIS LINE WHEN WORKING ON ACTUAL FORMULA. ONLY HERE TO APPEASE PYCHARM

    # Send kill messages etc


# TODO Implement dig in, implement artillery, comment later
def player_attack(attacker, defender):
    can_attack = player_can_attack(attacker=attacker, defender=defender)
    if can_attack is not True:
        return can_attack

    attacker, defender = get_player_info(attacker), get_player_info(defender)

    # Default: 100 troops, 2 attack, 100 morale

    # Returns negative if morale < 1, error if 0, make +1 instead?
    # 21.x at default
    attacker_strength = (sqrt(attacker.troops*attacker.attack) * log10(attacker.morale+1.1) + (randrange(11, 20)/10))
    defender_strength = (sqrt(defender.troops*defender.defense) * log10(defender.morale+1.1) + (randrange(11, 20)/10))

    a_ammo_needed = attacker.troops//attacker.logistics  # 5
    d_ammo_needed = defender.troops//defender.logistics

    a_min = 10  # Minimum amount of troops you can have
    d_min = 10

    a_max = 100 * attacker.charisma  # Maximum amount of troops you can have
    d_max = 100 * defender.charisma

    tank_multiplier_choices = \
        [2.5, 2.5,
         3, 3, 3, 3,
         3.5, 3.5, 3.5, 3.5, 3.5, 3.5,
         4, 4, 4, 4,
         5, 5,
         5.5]  # Choices for attack_strength multiplier if tank

    '''
    43.1 makes it 50/50? of getting 1 or 0 taken out if Infantry vs Tank
    14.4 makes it 50/50? or getting 1 or 2
    10 is sure 2, 20 is sure 1
    '''
    infantry_demultiplier_choices = \
        [10, 10, 10,
         20, 20, 20, 20, 20, 20,
         14.4, 14.4, 14.4, 14.4, 14.4,
         43.1, 43.1, 43.1]

    # Tweak minimum and maximum troops if attacker is a Tank. Also tweak strength
    if attacker.squad_type == 'Tank':
        a_min = 2
        a_max = 10 * attacker.charisma
        attacker_strength *= choice(tank_multiplier_choices)
        a_ammo_needed *= 100
        if defender.squad_type == 'Infantry':  # Decrease defender strength because 10-21
            defender_strength /= choice(infantry_demultiplier_choices)
        elif defender.squad_type == 'Tank':
            defender_strength /= 10

    if defender.squad_type == 'Tank':
        d_min = 2
        d_max = 10 * defender.charisma
        defender_strength *= choice(tank_multiplier_choices)
        d_ammo_needed *= 100
        if attacker.squad_type == 'Infantry':
            attacker_strength /= choice(infantry_demultiplier_choices)
        elif attacker.squad_type == 'Tank':
            attacker_strength /= 10

    if a_ammo_needed > attacker.ammo:  # If player doesnt have enough ammo, decrease strength by ammo/ammo needed
        attacker_strength *= (attacker.ammo / a_ammo_needed)
    if d_ammo_needed > defender.ammo:
        defender_strength *= (defender.ammo / d_ammo_needed)

    # Calculate percent of max troops lost. Will be used to calculate winner/loser
    attacker_loss_percent = defender_strength/a_max * 100
    defender_loss_percent = attacker_strength/d_max * 100

    # Round off strengths to get actual losses
    attacker_loss = round(defender_strength)
    defender_loss = round(attacker_strength)

    draw = False

    # Since player attacked, they must always have a lower percent of loss
    # Hmm using percent of loss might not always be a good idea. e.g 10/100 infantry loss vs 10/200 infantry loss
    if defender_loss_percent > attacker_loss_percent:
        win = True
    else:
        win = False
        if defender_loss_percent == attacker_loss_percent:
            draw = True

    # Remove actions and ammo from players
    remove_actions_from(attacker.username, 1)
    remove_ammo_from(attacker.username, a_ammo_needed)

    remove_ammo_from(defender.username, d_ammo_needed)

    # Just checking for errors -- actually forgot why I put this here, but It seems important
    fight1 = update_player_info(attacker.username, updates={'troops': attacker.troops - attacker_loss})
    fight2 = update_player_info(defender.username, updates={'troops': defender.troops - defender_loss})

    if win:
        update_player_info(defender.username, updates={'morale': defender.morale - 10})
    else:
        update_player_info(attacker.username, updates={'morale': attacker.morale - 10})

    if fight1[0] is not fight2[0]:
        log.warning("Weird ass error player_attack(attacker={attacker}, defender={defender})".format(
            attacker=attacker.username, defender=defender.username))
        return "This is a weird ass attack. Please report the current time and date and error the the admin"
    elif fight1[0] is False:
        return "A problem occurred, investigating"

    # Win and loss messages, update exp for winners
    if win:
        msg = "You won! {defender} lost {d_loss} troops while you only lost {a_loss}. ".format(
                defender=defender.username, d_loss=defender_loss, a_loss=attacker_loss)
        d_msg = "You were attacked by {attacker} and lost {d_loss} troops while they only lost {a_loss} troops.".format(
            attacker=attacker.username, d_loss=defender_loss, a_loss=attacker_loss)
        update_player_info(attacker.username, updates={'experience': attacker.experience + defender_loss})
        if draw:
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
        if draw:
            msg += "Even though losses are the same, your squad become discouraged at the lack of win and lose morale."
            d_msg += ("Even though the losses were the same, the vigour and skill of your squad strikes fear into "
                      "the hearts of the enemy and they lose morale.")

    # Update players
    attacker, defender = get_player_info(attacker.username), get_player_info(defender.username)

    # Reset any out of bound stats, send players home if need be
    if attacker.ammo < 0:
        update_player_info(attacker.username, updates={'ammo': 0})
    if defender.ammo < 0:
        update_player_info(defender.username, updates={'ammo': 0})

    if attacker.troops < a_min or attacker.morale < 10:
        msg += " You drop everything and hurry back to the capital to regenerate."
        d_msg += "Their losses are heavy and they rush back to the capital to regenerate"
        update_player_info(attacker.username, updates={'troops': a_min, 'morale': 10, 'ammo': 0, 'dug_in': 0,
                                                       'actions': 0})
        send_player_to(get_team_info(attacker.team)['capital'], attacker.username, force=True)

    if defender.troops < d_min or defender.morale < 10:
        msg += " The enemy rushes back to their capital to regenerate."
        d_msg += "Your losses are great so and you drop everything hurry back to the capital to regenerate"
        update_player_info(defender.username, updates={'troops': d_min, 'morale': 10, 'ammo': 0, 'dug_in': 0,
                                                       'actions': 0})
        send_player_to(get_team_info(defender.team)['capital'], defender.username, force=True)

    # Send summary message to defender.
    send_message(_from='', message=d_msg, to=defender.username)

    # Returns summary message to attacker
    return msg


def send_player_to(location, player, force=False):
    # Sends player to another location.
    # Checks to see if player can move actually move there if force isn't true
    player_info = get_player_info(player)
    player_loc = player_info.location

    success = False
    movable = can_move(to=location, player=player_info)

    def resulting(text):
        r = {'result': text, 'succeed': success}
        if success:
            r['new'] = location
        return r

    if not force:
        if not movable[0]:
            msg = "You cannot move to this location! {}".format(movable[1])
            return resulting(msg)

        actions_needed = 2
        if movable[1] == 'Enemy':
            actions_needed = 5
        if player_info.squad_type == 'Tank':
            actions_needed *= 2

        actions_needed //= player_info.pathfinder
        if not player_info.actions >= actions_needed:
            msg = "You do not have enough actions!"
            return resulting(msg)

        remove_actions_from(player, round(actions_needed))

    movement = update_player_info(player, updates={'location': location, 'dug_in': 0})

    if movement[0]:
        move_message = "Successfully moved from {player_loc} to {new_loc}!".format(player_loc=player_loc, new_loc=location)
        success = True
    else:
        move_message = "An error occurred while trying to move!"

    return resulting(move_message)


def give_player_ammo(player, amount=0):
    # Gives a player ammo
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
    # Increase the amount of troops a player has
    # Amount is always increased by the level of the charisma attribute
    # If player is a tank, amount = amount/10
    # Requires one action, and that the population of the current location is enough
    # Also player.management

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
    # Upgrades industry for the location a player is currently in. Requires 5 actions
    player = get_player_info(player)

    if not player.actions >= 5:
        return "Not enough actions!"
    location = get_location_called(player.location)
    update_location_info(player.location, 'industry', location.industry + 1)
    remove_actions_from(player, 5//player.development)

    return "Upgraded location!"


def upgrade_infrastructure_for(player):
    # Upgrades infrastructure for the location a player is currently in. Requires 5 actions
    player = get_player_info(player)

    if not player.actions >= 5: # //player.development
        return "Not enough actions!"
    location = get_location_called(player.location)
    update_location_info(player.location, 'infrastructure', location.infrastructure + 1)
    remove_actions_from(player, 5//player.development)

    return "Upgraded infrastructure!"


def get_player_info(username):
    # Gets info for player
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


def get_players_located_at(location):
    # Gets all players located at a location
    try:
        players_at = DBSession.query(Player).filter(Player.is_active).filter_by(location=location).all()
    except NoResultFound as e:
        msg = "{err} on get_players_located_at(location={location})".format(err=str(type(e).__name__ + ': ' + str(e)),
                                                                            location=location)
        log.warning(msg)
        return
    return players_at


def xp_for_level_up(player):
    # Calculates how much xp a player needs to level up
    player = get_player_info(player)

    if player.level >= 10:
        num = float('3.' + str(player.level))
    else:
        num = float('2.' + str(player.level))

    xp_needed = (player.level ** num * 100 // player.level)

    return xp_needed


def level_up_player(player, attribute):
    # Levels a player's attribute if they have enough xp for it, and haven't maxed it out.
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
    # Returns all the Messages a player is allowed to see
    player = get_player_info(player)
    news_tag = "{name}_{id}".format(name=player.username, id=player.id)
    results = DBSession.query(Radio)\
        .filter(or_(Radio.team == player.team, Radio.team == 'all', Radio.team == news_tag))\
        .filter(Radio.active).limit(50).all()
    if not results:
        return []

    return results


def send_message(message, _from='', to='', broadcast_by=''):
    result = dict(success=False, status='', message='')
    # Sends a message for a player.
    if not message:
        result['status'] = "https://www.youtube.com/watch?v=u9Dg-g7t2l4"
        return result
    if len(message) > 140 and not to and not broadcast_by:
        result['status'] = "Your budget is not high enough to send this many words"
        return result
    if not _from and not to and not broadcast_by:
        result['status'] = "No author specified"
        return result

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

    result = DBSession.query(Radio).filter_by(id=new_msg.id).one()
    return {'status': "Message sent successfully!", 'success': True,
            'message': {'content': result.message, 'timestamp': str(result.timestamp)}}
    # Sent as str because json can't render datetime? Not confirmed but I don't wanna test it now


def get_location_info_for(username, location):
    # Gets location info for frontend
    current = get_location_called(location)
    player = get_player_info(username)
    # also_here, amount_here
    is_here = current.name == player.location
    player_location_obj = get_location_called(player.location)

    movable = can_move_to(player, [current, player_location_obj])

    friendly = is_here and (current.control == 'None' or current.control == player.team)
    info = {'name': current.name, 'terrain': current.type, 'population': current.population, 'ammo': current.ammo,
            'industry': current.industry, 'infrastructure': current.infrastructure, 'dug_in': player.dug_in,
            'is_here': is_here, 'friendly': friendly, 'movable': bool(movable)}

    currently_here = get_players_located_at(location)
    also_here = []
    for i in currently_here:
        if (i.username != player.username) and (i.location == player.location or i.team == player.team):
            p_info = get_player_json_info_for(i.username)
            is_enemy = {'is_enemy': i.team != player.team}
            p_info.update(is_enemy)
            also_here.append(p_info)

    if also_here:
        info['also_here'] = also_here

    blue_total = {'sum': sum([i.troops for i in currently_here if i.team == 'Blue']), 'team': 'Blue'}
    red_total = {'sum': sum([i.troops for i in currently_here if i.team == 'Red']), 'team': 'Red'}
    yellow_total = {'sum': sum([i.troops for i in currently_here if i.team == 'Yellow']), 'team': 'Yellow'}
    black_total = {'sum': sum([i.troops for i in currently_here if i.team == 'Black']), 'team': 'Black'}
    totals = [i for i in (blue_total, red_total, yellow_total, black_total) if i['sum'] > 0]

    amount_here = [i['team'] + " troops: " + str(i['sum']) for i in totals]
    info['amount_here'] = amount_here

    return info


def get_player_json_info_for(username, me=False):
    # Gets player info for frontend
    player = get_player_info(username)
    # Could return NoResultFound Remember that
    currently_online = len(
        DBSession.query(Player).filter(Player.last_active > (datetime.now() - timedelta(minutes=16))).all())

    player_info = {'name': player.username, 'morale': player.morale, 'squad': player.squad_type,
                   'team': player.team, 'troops': player.troops, 'dug_in': player.dug_in,
                   'currently_online': currently_online if currently_online else 1}
    if me:
        player_info['actions'] = player.actions
        player_info['location'] = player.location
        player_info['ammo'] = player.ammo

    return player_info


def get_all_game_info_for(player, location=''):
    # Returns all the game info. Dict
    game_info = dict()
    game_info['hexes'] = get_map_info_for()
    game_info['player'] = get_player_info(player)
    game_info['online'] = \
        DBSession.query(Player).filter(Player.last_active > (datetime.now() - timedelta(minutes=16))).all()

    if location:
        loc = get_location_called(location)
        if not loc:
            return False
        game_info['current_hex'] = loc
        game_info['currently_here'] = get_players_located_at(location)
        game_info['movable'] = can_move(game_info['current_hex'], game_info['player'])[0]

    return game_info
