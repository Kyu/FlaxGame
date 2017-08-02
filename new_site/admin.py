import logging

from .game import update_player_info

log = logging.getLogger(__name__)


def ban_player(username, reason, banner, until=None):
    updates = {'banned': True, 'reason_banned': reason, 'time_banned': until, 'banned_by': banner}
    ban = update_player_info(username, updates=updates)
    if ban[0]:
        return username + " banned successfully"
    else:
        return ban[1]


def unban_player(username):
    updates = {'banned': False, 'banned_by': None, 'time_banned': None, 'reason_banned': None}
    ub = update_player_info(username, updates=updates)
    if ub[0]:
        return username + " unbanned successfully"
    else:
        return ub[1]