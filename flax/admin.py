import logging

import transaction
from sqlalchemy.orm.exc import NoResultFound

from .game import (
    update_player_info,
    send_message
)
from .models import (
    DBSession,
    User,
    Radio
)

log = logging.getLogger(__name__)


# Ban a player. If until=None, ban is permanent
def ban_player(username, reason, banner, until=None):
    updates = {'banned': True, 'reason_banned': reason, 'time_banned': until, 'banned_by': banner}
    ban = update_player_info(username, updates=updates)
    if ban[0]:
        return username + " banned successfully"
    else:
        return ban[1]


# Unban a player
def unban_player(username):
    updates = {'banned': False, 'banned_by': None, 'time_banned': None, 'reason_banned': None}
    ub = update_player_info(username, updates=updates)
    if ub[0]:
        return username + " unbanned successfully"
    else:
        return ub[1]


# Get a user.
def get_user(username):
    try:
        user = DBSession.query(User).filter_by(username=username).one()
    except NoResultFound:
        return

    return user


# Hide an announcement by ID(Admins can see announcement IDs)
def create_announcement(author, message):
    sent = send_message(message=message, broadcast_by=author)
    return sent


def hide_announcement(_id):
    try:
        msg = DBSession.query(Radio).filter_by(id=_id).filter_by(team='all')
        active = msg.one().active
    except NoResultFound:
        return "No announcement with that ID found"

    if not active:
        return "Announcement already hidden"

    with transaction.manager:
        msg.update({'active': False})

    return "Announcement Hidden"
